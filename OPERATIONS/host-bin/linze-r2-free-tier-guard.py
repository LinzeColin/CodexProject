#!/usr/bin/env python3
"""R2 免费额度守卫 —— Owner 铁律「不允许任何收费行为」的机器执行体。

背景（2026-08-07 事故）：`backups` 桶建桶时默认存储类被设成 InfrequentAccess，
上传脚本不指定存储类 -> 每个对象都继承 IA。**IA 完全在免费额度之外，且按整单位向上取整计费**：
实际只有 51 次 IA Class A 操作，被当作 1 个完整计费单位收了 $9.00。
同期真正的大用量（3.01M Class B、110.91k Class A、0.74GB 存储）全是 Standard，全部 $0.00。
=> 结论：**R2 上把钱烧掉的不是"用得多"，是"用错存储类"。**

本守卫做四件事，自身不产生任何 R2 操作（全部走 CF REST + GraphQL Analytics）：
  1. 桶默认存储类 != Standard  -> 自动 PATCH 回 Standard（熔断动作，幂等）
  2. 账号内存在非 Standard 对象 -> CRIT（不自动转换：CopyObject 会再计费，要人确认）
  3. 本计费周期 Class A / Class B / 存储 投影到整周期，对免费额度算占比 -> >70% WARN，>90% CRIT
  4. 写 JSON 判定 + 追加日志；有违规则以非零码退出

零 agent、零模型调用、纯脚本。
"""
import json
import os
import sys
import urllib.request
import urllib.error
from datetime import date, datetime, timedelta, timezone

ACCT = "a8e86fa4be62ee3f9b5873b2aa934256"
TOKEN_FILE = os.environ.get("R2_GUARD_TOKEN_FILE", "/srv/linze/secrets/cf_r2_write_token")
VERDICT = os.environ.get("R2_GUARD_VERDICT", "/srv/linze/apps/status/data/r2_free_tier_guard.json")

# 计费周期起始日 —— 取自 dashboard「Cycle Jul 7 - Aug 6」/「Aug 7 - Sep 6」
CYCLE_DAY = 7
# R2 免费额度（每计费周期，仅 Standard 存储类享有；IA 一分钱额度都没有）
FREE_CLASS_A = 1_000_000
FREE_CLASS_B = 10_000_000
FREE_STORAGE_GB = 10.0
# Owner 安全线不是免费额度的 100%，而是严格小于 50%。40% 预警，50% 拒绝新增周期负载。
WARN_RATIO, CRIT_RATIO = 0.40, 0.50

CLASS_A = {
    "ListBuckets", "PutBucket", "ListObjects", "PutObject", "CopyObject",
    "CompleteMultipartUpload", "CreateMultipartUpload", "ListMultipartUploads",
    "UploadPart", "UploadPartCopy", "ListParts", "PutBucketEncryption",
    "PutBucketCors", "PutBucketLifecycleConfiguration", "LifecycleStorageTierTransition",
}

TOKEN = open(TOKEN_FILE).read().strip()


def api(path, method="GET", payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4" + path, data=data, method=method,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=45).read())


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.cloudflare.com/client/v4/graphql", data=body,
        headers={"Authorization": "Bearer " + TOKEN, "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if out.get("errors"):
        raise RuntimeError("GraphQL: " + json.dumps(out["errors"], ensure_ascii=False)[:300])
    return out["data"]["viewer"]["accounts"][0]


def cycle_bounds(today):
    """本计费周期的 [起, 讫]。周期每月 7 号换，与 dashboard 一致。"""
    start = today.replace(day=CYCLE_DAY)
    if today.day < CYCLE_DAY:
        start = (start - timedelta(days=1)).replace(day=CYCLE_DAY)
    nxt = (start + timedelta(days=32)).replace(day=CYCLE_DAY)
    return start, nxt - timedelta(days=1)


def main():
    today = date.today()
    start, end = cycle_bounds(today)
    elapsed = (today - start).days + 1
    total_days = (end - start).days + 1

    findings, actions = [], []
    severity = "PASS"

    def raise_to(level):
        nonlocal severity
        order = {"PASS": 0, "WARN": 1, "CRIT": 2}
        if order[level] > order[severity]:
            severity = level

    # ---- 1. 桶默认存储类；违规即熔断改回 Standard --------------------------
    buckets = api("/accounts/%s/r2/buckets" % ACCT)["result"]["buckets"]
    bucket_classes = {}
    for b in buckets:
        name = b["name"]
        # 列桶接口**不返回** storage_class（只有 name/creation_date），必须逐桶 GET。
        # 早先版本在这里写了 .get("storage_class","Standard")，把"缺字段"当成了"合规"——
        # 负控实测：新建一个 IA 桶，守卫报 PASS。假绿就是这么来的，别再省这一趟请求。
        detail = api("/accounts/%s/r2/buckets/%s" % (ACCT, name))["result"]
        sc = detail.get("storage_class")
        if sc is None:
            findings.append({"code": "STORAGE_CLASS_UNREADABLE", "severity": "CRIT", "bucket": name,
                             "zh": "读不到桶 %s 的默认存储类 —— 读不到就不许当合规。" % name})
            raise_to("CRIT")
            bucket_classes[name] = "<unreadable>"
            continue
        bucket_classes[name] = sc
        if sc != "Standard":
            findings.append({
                "code": "BUCKET_DEFAULT_NOT_STANDARD", "severity": "CRIT",
                "bucket": name, "storage_class": sc,
                "zh": "桶 %s 的默认存储类是 %s —— 该存储类不在免费额度内，写进去的每个对象都会计费。" % (name, sc)})
            raise_to("CRIT")
            # 改默认存储类靠 cf-r2-storage-class 请求头，不是 body 字段
            try:
                req = urllib.request.Request(
                    "https://api.cloudflare.com/client/v4/accounts/%s/r2/buckets/%s" % (ACCT, name),
                    data=b"{}", method="PATCH",
                    headers={"Authorization": "Bearer " + TOKEN,
                             "Content-Type": "application/json",
                             "cf-r2-storage-class": "Standard"})
                urllib.request.urlopen(req, timeout=45)
                actions.append({"action": "BUCKET_DEFAULT_RESET_TO_STANDARD", "bucket": name,
                                "zh": "已把桶 %s 的默认存储类改回 Standard" % name})
            except Exception as exc:  # 熔断失败要看得见，不能吞
                findings.append({"code": "FUSE_FAILED", "severity": "CRIT", "bucket": name,
                                 "zh": "自动改回 Standard 失败：%s" % str(exc)[:160]})

    # ---- 2. 账号内是否还有非 Standard 对象（GraphQL，不花 R2 操作）---------
    q_store = """query($a:String!,$s:Date!,$u:Date!){viewer{accounts(filter:{accountTag:$a}){
      r2StorageAdaptiveGroups(filter:{date_geq:$s,date_leq:$u},limit:5000,orderBy:[date_DESC]){
        dimensions{bucketName date storageClass} max{payloadSize metadataSize objectCount}}}}}"""
    # 只读**最近一个完整日**：r2StorageAdaptiveGroups 的值是当日 24h 内的 max，
    # 当天这一格会把"今天早些时候刚被清掉的旧峰值"当成现值报出来（§9.2 已记过这个坑）。
    # 存储是慢变量，晚一天发现无碍；真正的即时拦截靠上面的桶默认存储类检查。
    complete_day = today - timedelta(days=1)
    store_rows = gql(q_store, {"a": ACCT, "s": (complete_day - timedelta(days=2)).isoformat(),
                               "u": complete_day.isoformat()})["r2StorageAdaptiveGroups"]
    latest = {}
    for row in store_rows:
        d = row["dimensions"]
        key = (d["bucketName"], d["storageClass"])
        if key not in latest or d["date"] > latest[key][0]:
            latest[key] = (d["date"], row["max"])

    ia_objects, storage_bytes = 0, 0
    ia_detail = []
    for (bucket, sc), (when, mx) in latest.items():
        storage_bytes += mx["payloadSize"] + mx["metadataSize"]
        if sc != "Standard" and mx["objectCount"] > 0:
            ia_objects += mx["objectCount"]
            # 先只登记。是 CRIT 还是最短计费期的尾巴，要等第 3 步拿到「本周期有没有 IA 操作」才能判。
            ia_detail.append({"bucket": bucket, "storage_class": sc,
                              "objects": mx["objectCount"], "as_of": when})

    # ---- 3. 本周期操作量投影 ------------------------------------------------
    q_ops = """query($a:String!,$s:Date!,$u:Date!){viewer{accounts(filter:{accountTag:$a}){
      r2OperationsAdaptiveGroups(filter:{date_geq:$s,date_leq:$u},limit:10000,orderBy:[sum_requests_DESC]){
        dimensions{actionType bucketName date storageClass} sum{requests}}}}}"""
    ops = gql(q_ops, {"a": ACCT, "s": start.isoformat(), "u": today.isoformat()})["r2OperationsAdaptiveGroups"]
    a_used = b_used = 0
    ia_ops = 0
    ia_ops_detail = []
    daily = {}
    per_bucket = {}
    for row in ops:
        n = row["sum"]["requests"]
        act = row["dimensions"]["actionType"]
        bkt = row["dimensions"]["bucketName"] or "(account)"
        when = row["dimensions"].get("date")
        daily.setdefault(when, {"class_a": 0, "class_b": 0})
        if act in CLASS_A:
            a_used += n
            daily[when]["class_a"] += n
        else:
            b_used += n
            daily[when]["class_b"] += n
        per_bucket[bkt] = per_bucket.get(bkt, 0) + n
        if row["dimensions"].get("storageClass") not in (None, "Standard"):
            # 这才是真正贵的那一类：IA 操作按整计费单位向上取整，$9.00 起步
            ia_ops += n
            ia_ops_detail.append({"bucket": bkt, "action": act, "date": when, "requests": n})

    # ---- IA 定级：真的在写 IA，还是 30 天最短计费期的尾巴？----------------
    # IA 有 30 天最短存储期：对象 CopyObject 转成 Standard 之后，Cloudflare 的存储分析
    # 仍把它们记在 InfrequentAccess 直到期满。实时 S3 列举才是真值。
    # 真正贵的是 IA **操作**（整单位向上取整，$9.00 起步），不是 IA 存储残留（$0.01/月）。
    if ia_detail:
        bad_default = [b for b, c in bucket_classes.items() if c != "Standard"]
        # 判据是「**还在不在**写 IA」，不是「本周期发生过没有」。
        # 一次性的清理动作（CopyObject 转 Standard）会在周期总数里留痕好几周，
        # 拿周期总数当判据 = 修完之后守卫继续报 CRIT 报到月底，狼来了。
        # 只看最近两天（上一完整日 + 今日）：那才是「现在还在写吗」。
        recent_days = {today.isoformat(), complete_day.isoformat()}
        ia_ops_recent = sum(d["requests"] for d in ia_ops_detail if d.get("date") in recent_days)
        if ia_ops_recent > 0 or bad_default:
            for d in ia_detail:
                findings.append({**d, "code": "NON_STANDARD_OBJECTS_PRESENT", "severity": "CRIT",
                                 "ia_operations_recent": ia_ops_recent,
                                 "zh": "桶 %s 有 %d 个 %s 对象（截至 %s），且最近两天发生了 %d 次 IA 操作"
                                       "／存在非 Standard 默认桶 %s —— **这是还在往 IA 写，不是历史残留**。"
                                       % (d["bucket"], d["objects"], d["storage_class"], d["as_of"],
                                          ia_ops_recent, bad_default or "无")})
            raise_to("CRIT")
        else:
            for d in ia_detail:
                findings.append({**d, "code": "IA_MIN_DURATION_TAIL", "severity": "WARN",
                                 "ia_operations_this_cycle": 0,
                                 "zh": "桶 %s 的存储分析里仍显示 %d 个 %s 对象（截至 %s），"
                                       "但最近两天**零 IA 操作**且所有桶默认均为 Standard —— "
                                       "这是 IA 30 天最短计费期的尾巴，实时 S3 列举应为 0，约 $0.01/月，会自然消失。"
                                       "**不要为此再做 CopyObject —— 转换本身就是 IA 操作，$9.00 起步。**"
                                       % (d["bucket"], d["objects"], d["storage_class"], d["as_of"])})
            raise_to("WARN")

    # 不能拿事故日除以两天再线性外推整月。用当前累计值 + 最近稳定日 × 剩余天数；
    # 当 UTC 当日已过 6 小时，按已过时长把当日样本折算为 24h，否则使用上一完整日。
    now_utc = datetime.now(timezone.utc)
    today_key = today.isoformat()
    complete_key = complete_day.isoformat()
    if today_key in daily and now_utc.hour >= 6:
        elapsed_hours = now_utc.hour + now_utc.minute / 60 + now_utc.second / 3600
        day_scale = 24 / elapsed_hours
        steady_a = int(daily[today_key]["class_a"] * day_scale)
        steady_b = int(daily[today_key]["class_b"] * day_scale)
        projection_basis = "current_utc_day_scaled_to_24h"
    else:
        steady_a = daily.get(complete_key, {}).get("class_a", 0)
        steady_b = daily.get(complete_key, {}).get("class_b", 0)
        projection_basis = "latest_complete_utc_day"
    remaining_days = max((end - today).days, 0)
    projected_a = a_used + steady_a * remaining_days
    projected_b = b_used + steady_b * remaining_days
    usage = {
        "class_a": {"used": a_used, "projected": projected_a, "free": FREE_CLASS_A, "steady_day": steady_a},
        "class_b": {"used": b_used, "projected": projected_b, "free": FREE_CLASS_B, "steady_day": steady_b},
        "storage_gb": {"used": round(storage_bytes / 2 ** 30, 3), "projected": round(storage_bytes / 2 ** 30, 3),
                       "free": FREE_STORAGE_GB},
    }
    for label, item in usage.items():
        ratio = item["projected"] / item["free"] if item["free"] else 0
        item["projected_ratio"] = round(ratio, 4)
        if ratio >= CRIT_RATIO:
            findings.append({"code": "FREE_TIER_PROJECTED_BREACH", "severity": "CRIT", "metric": label,
                             "zh": "%s 投影达到免费额度的 %.0f%%，触发 Owner 的 50%% 安全线；禁止新增周期负载。" % (label, ratio * 100)})
            raise_to("CRIT")
        elif ratio >= WARN_RATIO:
            findings.append({"code": "FREE_TIER_PROJECTED_HIGH", "severity": "WARN", "metric": label,
                             "zh": "%s 投影为免费额度的 %.0f%%，逼近上限。" % (label, ratio * 100)})
            raise_to("WARN")

    verdict = {
        "schema_version": "linze.r2_free_tier_guard.v1",
        "generated_at": today.isoformat(),
        "policy": "R2 必须完全落在免费额度内；禁止 InfrequentAccess（IA 无免费额度且按整单位向上取整计费）",
        "billing_cycle": {"start": start.isoformat(), "end": end.isoformat(),
                          "days_elapsed": elapsed, "days_total": total_days,
                          "projection_basis": projection_basis,
                          "projection_confidence": "low" if now_utc.hour < 6 else "normal"},
        "storage_as_of": complete_day.isoformat(),
        "severity": severity,
        "bucket_default_storage_class": bucket_classes,
        "non_standard_objects": ia_objects,
        "ia_operations_this_cycle": ia_ops,
        "ia_operations_recent_2d": ia_ops_recent if ia_detail else 0,
        "ia_operations_detail": ia_ops_detail[:10],
        "usage": usage,
        "top_buckets_by_operations": dict(sorted(per_bucket.items(), key=lambda kv: -kv[1])[:5]),
        "actions_taken": actions,
        "findings": findings,
    }

    try:
        os.makedirs(os.path.dirname(VERDICT), exist_ok=True)
        tmp = VERDICT + ".tmp"
        with open(tmp, "w") as fh:
            json.dump(verdict, fh, ensure_ascii=False, indent=2, sort_keys=True)
        os.replace(tmp, VERDICT)
        os.chmod(VERDICT, 0o644)
    except OSError as exc:
        print("verdict 写入失败: %s" % exc, file=sys.stderr)

    print("%s severity=%s classA=%d/%d(投影%d) classB=%d/%d(投影%d) 存储=%.2fGB/%.0fGB IA对象=%d 熔断=%d" % (
        today.isoformat(), severity,
        a_used, FREE_CLASS_A, usage["class_a"]["projected"],
        b_used, FREE_CLASS_B, usage["class_b"]["projected"],
        usage["storage_gb"]["used"], FREE_STORAGE_GB, ia_objects, len(actions)))
    for f in findings:
        print("  [%s] %s" % (f["severity"], f["zh"]))
    return 0 if severity == "PASS" else (1 if severity == "WARN" else 2)


if __name__ == "__main__":
    sys.exit(main())
