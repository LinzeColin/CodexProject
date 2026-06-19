import time
from typing import Any, Dict, Optional

import httpx

from app.services import db


SYSTEM_PROMPT = (
    "你是武汉开明高科技有限公司的工业运维分析助手。"
    "回答必须结合规则引擎结论，输出谨慎、可执行、需要工程师确认的建议。"
)


def route_model(module: str, input_data: Dict[str, Any], offline_result: Dict[str, Any], case_id: Optional[int] = None) -> Dict[str, Any]:
    configs = [item for item in db.get_model_configs() if item["enabled"] and item["api_key"] and item["base_url"] and item["model"]]
    if not configs:
        return {
            "used": False,
            "provider": "offline_rules",
            "message": "未配置可用模型，已使用离线规则引擎。",
        }

    prompt = {
        "module": module,
        "input": input_data,
        "rule_result": {
            "summary": offline_result.get("summary"),
            "risk_level": offline_result.get("risk_level"),
            "risk_score": offline_result.get("risk_score"),
            "suggestions": offline_result.get("suggestions", []),
        },
    }
    last_error = None
    for config in configs:
        started = time.perf_counter()
        try:
            response = httpx.post(
                f"{config['base_url'].rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {config['api_key']}"},
                json={
                    "model": config["model"],
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": str(prompt)},
                    ],
                    "temperature": 0.2,
                },
                timeout=20,
            )
            response.raise_for_status()
            payload = response.json()
            content = payload.get("choices", [{}])[0].get("message", {}).get("content", "")
            latency_ms = int((time.perf_counter() - started) * 1000)
            db.add_model_call_log(case_id, config["provider"], config["model"], "success", latency_ms, None)
            return {
                "used": True,
                "provider": config["provider"],
                "model": config["model"],
                "message": content or "模型返回为空，保留离线规则结果。",
                "latency_ms": latency_ms,
            }
        except Exception as exc:  # noqa: BLE001 - log-and-fallback boundary
            latency_ms = int((time.perf_counter() - started) * 1000)
            last_error = str(exc)
            db.add_model_call_log(case_id, config["provider"], config["model"], "failed", latency_ms, last_error)

    return {
        "used": False,
        "provider": "offline_rules",
        "message": f"已尝试配置模型但调用失败，使用离线规则引擎。最后错误：{last_error}",
    }

