from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
import re
from xml.etree import ElementTree
from zipfile import ZipFile


@dataclass(frozen=True)
class Transaction:
    transaction_time: datetime
    transaction_type: str
    counterparty: str
    account: str
    description: str
    direction: str
    amount_cents: int
    payment_method: str
    status: str
    order_id: str
    merchant_order_id: str
    note: str
    source_file: str
    source_platform: str = "alipay"

    @property
    def amount_yuan(self) -> float:
        return self.amount_cents / 100


def _read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "gb18030", "gbk"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="gb18030", errors="replace")


def _is_alipay_header(fields: list[str]) -> bool:
    return bool(fields) and fields[0] == "交易时间" and "交易分类" in fields


def _is_wechat_header(fields: list[str]) -> bool:
    return bool(fields) and fields[0] == "交易时间" and "交易类型" in fields and any("金额" in item for item in fields)


def _csv_fields(line: str) -> list[str]:
    return [item.strip() for item in next(csv.reader([line]))]


def _find_alipay_header(lines: list[str]) -> int:
    for idx, line in enumerate(lines):
        if _is_alipay_header(_csv_fields(line)):
            return idx
    raise ValueError("未找到支付宝账单表头：交易时间,...")


def _find_wechat_header(lines: list[str]) -> int:
    for idx, line in enumerate(lines):
        if _is_wechat_header(_csv_fields(line)):
            return idx
    raise ValueError("未找到微信账单表头：交易时间,交易类型,...")


def _find_bill_header(lines: list[str]) -> tuple[str, int]:
    for idx, line in enumerate(lines):
        fields = _csv_fields(line)
        if _is_alipay_header(fields):
            return "alipay", idx
        if _is_wechat_header(fields):
            return "wechat", idx
    raise ValueError("未找到支持的账单表头：支付宝或微信 CSV")


def _find_bill_table_header(table: list[list[str]]) -> tuple[str, int]:
    for idx, row in enumerate(table):
        fields = [str(item or "").strip() for item in row]
        if _is_alipay_header(fields):
            return "alipay", idx
        if _is_wechat_header(fields):
            return "wechat", idx
    raise ValueError("未找到支持的账单表头：支付宝或微信 CSV/XLSX")


def _amount_to_cents(value: str) -> int:
    cleaned = (value or "").strip().replace(",", "")
    for token in ("¥", "￥", "元", " "):
        cleaned = cleaned.replace(token, "")
    if not cleaned:
        return 0
    if "." in cleaned:
        yuan, fen = cleaned.split(".", 1)
        fen = (fen + "00")[:2]
    else:
        yuan, fen = cleaned, "00"
    sign = -1 if yuan.startswith("-") else 1
    yuan = yuan.lstrip("+-") or "0"
    return sign * (int(yuan) * 100 + int(fen))


def _parse_transaction_time(value: str) -> datetime:
    cleaned = (value or "").strip()
    for pattern in ("%Y-%m-%d %H:%M:%S", "%Y/%m/%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y/%m/%d %H:%M"):
        try:
            return datetime.strptime(cleaned, pattern)
        except ValueError:
            continue
    if re.fullmatch(r"\d+(\.\d+)?", cleaned):
        serial = float(cleaned)
        if serial > 30_000:
            return datetime(1899, 12, 30) + timedelta(days=serial)
    raise ValueError(f"无法识别交易时间：{value}")


def _pick(raw: dict[str, str], *names: str) -> str:
    for name in names:
        value = raw.get(name)
        if value is not None:
            return value.strip()
    return ""


def _alipay_transaction(raw: dict[str, str], source: Path) -> Transaction:
    return Transaction(
        transaction_time=_parse_transaction_time(raw["交易时间"]),
        transaction_type=(raw.get("交易分类") or "").strip(),
        counterparty=(raw.get("交易对方") or "").strip(),
        account=(raw.get("对方账号") or "").strip(),
        description=(raw.get("商品说明") or "").strip(),
        direction=(raw.get("收/支") or "").strip(),
        amount_cents=_amount_to_cents(raw.get("金额") or "0"),
        payment_method=(raw.get("收/付款方式") or "").strip(),
        status=(raw.get("交易状态") or "").strip(),
        order_id=(raw.get("交易订单号") or "").strip(),
        merchant_order_id=(raw.get("商家订单号") or "").strip(),
        note=(raw.get("备注") or "").strip(),
        source_file=str(source),
        source_platform="alipay",
    )


def _wechat_transaction(raw: dict[str, str], source: Path) -> Transaction | None:
    try:
        transaction_time = _parse_transaction_time(raw["交易时间"])
    except ValueError:
        return None
    return Transaction(
        transaction_time=transaction_time,
        transaction_type=_pick(raw, "交易类型", "交易分类"),
        counterparty=_pick(raw, "交易对方", "对方"),
        account="微信支付",
        description=_pick(raw, "商品", "商品说明", "商品名称"),
        direction=_pick(raw, "收/支", "收支"),
        amount_cents=_amount_to_cents(_pick(raw, "金额(元)", "金额", "交易金额")),
        payment_method=_pick(raw, "支付方式", "收/付款方式"),
        status=_pick(raw, "当前状态", "交易状态"),
        order_id=_pick(raw, "交易单号", "交易订单号"),
        merchant_order_id=_pick(raw, "商户单号", "商家订单号"),
        note=_pick(raw, "备注", "备注信息"),
        source_file=str(source),
        source_platform="wechat",
    )


def _transactions_from_dict_rows(rows: Iterable[dict[str, str]], source: Path, source_type: str) -> list[Transaction]:
    transactions: list[Transaction] = []
    for raw in rows:
        if not raw or not (raw.get("交易时间") or "").strip():
            continue
        if source_type == "wechat":
            tx = _wechat_transaction(raw, source)
            if tx is not None:
                transactions.append(tx)
        else:
            transactions.append(_alipay_transaction(raw, source))
    return transactions


def read_alipay_csv(path: str | Path) -> list[Transaction]:
    source = Path(path)
    text = _read_text(source)
    lines = text.splitlines()
    header_idx = _find_alipay_header(lines)
    rows = csv.DictReader(lines[header_idx:])
    return _transactions_from_dict_rows(rows, source, "alipay")


def read_wechat_csv(path: str | Path) -> list[Transaction]:
    source = Path(path)
    text = _read_text(source)
    lines = text.splitlines()
    header_idx = _find_wechat_header(lines)
    rows = csv.DictReader(lines[header_idx:])
    return _transactions_from_dict_rows(rows, source, "wechat")


def _xml_namespace(root: ElementTree.Element) -> str:
    if root.tag.startswith("{"):
        return root.tag.split("}", 1)[0] + "}"
    return ""


def _shared_strings(archive: ZipFile) -> list[str]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    root = ElementTree.fromstring(archive.read("xl/sharedStrings.xml"))
    ns = _xml_namespace(root)
    strings: list[str] = []
    for item in root.findall(f".//{ns}si"):
        text = "".join(node.text or "" for node in item.findall(f".//{ns}t"))
        strings.append(text)
    return strings


def _column_index(cell_ref: str) -> int:
    letters = re.sub(r"[^A-Z]", "", cell_ref.upper())
    value = 0
    for letter in letters:
        value = value * 26 + (ord(letter) - ord("A") + 1)
    return max(value - 1, 0)


def _cell_text(cell: ElementTree.Element, ns: str, shared_strings: list[str]) -> str:
    cell_type = cell.attrib.get("t", "")
    if cell_type == "inlineStr":
        return "".join(node.text or "" for node in cell.findall(f".//{ns}t")).strip()
    value_node = cell.find(f"{ns}v")
    value = "" if value_node is None or value_node.text is None else value_node.text.strip()
    if cell_type == "s" and value:
        index = int(value)
        return shared_strings[index].strip() if 0 <= index < len(shared_strings) else ""
    return value


def _read_xlsx_table(path: Path) -> list[list[str]]:
    with ZipFile(path) as archive:
        sheet_names = sorted(name for name in archive.namelist() if re.fullmatch(r"xl/worksheets/sheet\d+\.xml", name))
        if not sheet_names:
            raise ValueError(f"未找到 XLSX 工作表：{path}")
        shared = _shared_strings(archive)
        root = ElementTree.fromstring(archive.read(sheet_names[0]))
    ns = _xml_namespace(root)
    table: list[list[str]] = []
    for row in root.findall(f".//{ns}sheetData/{ns}row"):
        values: list[str] = []
        for cell in row.findall(f"{ns}c"):
            ref = cell.attrib.get("r", "")
            index = _column_index(ref) if ref else len(values)
            while len(values) <= index:
                values.append("")
            values[index] = _cell_text(cell, ns, shared)
        table.append(values)
    return table


def read_bill_xlsx(path: str | Path) -> list[Transaction]:
    source = Path(path)
    table = _read_xlsx_table(source)
    source_type, header_idx = _find_bill_table_header(table)
    headers = [str(item or "").strip() for item in table[header_idx]]
    dict_rows: list[dict[str, str]] = []
    for row in table[header_idx + 1 :]:
        if not any(str(item or "").strip() for item in row):
            continue
        dict_rows.append({header: str(row[index] if index < len(row) else "").strip() for index, header in enumerate(headers) if header})
    return _transactions_from_dict_rows(dict_rows, source, source_type)


def read_bill_csv(path: str | Path) -> list[Transaction]:
    source = Path(path)
    lines = _read_text(source).splitlines()
    source_type, _ = _find_bill_header(lines)
    if source_type == "wechat":
        return read_wechat_csv(source)
    return read_alipay_csv(source)


def read_bill_file(path: str | Path) -> list[Transaction]:
    source = Path(path)
    suffix = source.suffix.casefold()
    if suffix == ".xlsx":
        return read_bill_xlsx(source)
    if suffix == ".csv":
        return read_bill_csv(source)
    raise ValueError(f"当前导入器支持支付宝/微信 CSV/XLSX；暂不支持该文件类型：{source}")


def expand_input_paths(inputs: Iterable[str | Path]) -> list[Path]:
    paths: list[Path] = []
    for item in inputs:
        path = Path(item).expanduser()
        if path.is_dir():
            paths.extend(sorted(child for child in path.iterdir() if child.is_file() and child.suffix.casefold() in {".csv", ".xlsx"}))
        else:
            if path.suffix.casefold() not in {".csv", ".xlsx"}:
                raise ValueError(f"当前导入器支持支付宝/微信 CSV/XLSX；暂不支持该文件类型：{path}")
            paths.append(path)
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError("输入文件不存在：" + ", ".join(missing))
    return paths


def load_transactions(inputs: Iterable[str | Path]) -> list[Transaction]:
    seen: set[tuple[str, str, int, str, str]] = set()
    merged: list[Transaction] = []
    for path in expand_input_paths(inputs):
        for tx in read_bill_file(path):
            key = (
                tx.order_id or tx.merchant_order_id,
                tx.transaction_time.isoformat(sep=" "),
                tx.amount_cents,
                tx.direction,
                tx.counterparty,
                tx.description,
            )
            if key in seen:
                continue
            seen.add(key)
            merged.append(tx)
    return sorted(merged, key=lambda tx: tx.transaction_time)
