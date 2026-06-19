from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from pfi_os.integrations.research_bus_api import (
    CHAT_DROPBOX_DIR,
    bus_api_requests_frame,
    bus_chat_inputs_frame,
    bus_heartbeats_frame,
    heartbeat_system,
    pending_bus_requests_frame,
    process_chat_dropbox,
    process_pending_bus_requests,
    research_bus_health_summary,
    confirm_holding_update_candidate,
    submit_bus_request,
    submit_chat_input,
    submit_webhook_payload,
)
from pfi_os.integrations.research_bus_audit import AUDIT_OUTPUT_PATH, run_research_bus_interop_audit


def main() -> None:
    parser = argparse.ArgumentParser(description="ResearchBus bidirectional API and chat input bridge.")
    sub = parser.add_subparsers(dest="command", required=True)

    chat = sub.add_parser("submit-chat")
    chat.add_argument("--text", required=True)
    chat.add_argument("--source-system", default="ExternalChat")
    chat.add_argument("--author", default="")
    chat.add_argument("--channel", default="chat")
    chat.add_argument("--attachment-path", action="append", default=[])
    chat.add_argument("--attachment-json", action="append", default=[])
    chat.add_argument("--db", default="")
    chat.add_argument("--json", action="store_true")

    webhook = sub.add_parser("submit-webhook")
    webhook.add_argument("--payload-json", default="")
    webhook.add_argument("--text", default="")
    webhook.add_argument("--source-system", default="LocalWebhook")
    webhook.add_argument("--db", default="")
    webhook.add_argument("--json", action="store_true")

    request = sub.add_parser("submit-request")
    request.add_argument("--type", required=True)
    request.add_argument("--payload-json", default="{}")
    request.add_argument("--source-system", default="ExternalChat")
    request.add_argument("--target-system", default="ResearchBus")
    request.add_argument("--priority", type=int, default=5)
    request.add_argument("--db", default="")
    request.add_argument("--json", action="store_true")

    process = sub.add_parser("process")
    process.add_argument("--system-name", default="ResearchBus")
    process.add_argument("--limit", type=int, default=25)
    process.add_argument("--db", default="")
    process.add_argument("--json", action="store_true")

    confirm_candidate = sub.add_parser("confirm-holding-candidate")
    confirm_candidate.add_argument("--candidate-id", required=True)
    confirm_candidate.add_argument("--holding-import-path", default="")
    confirm_candidate.add_argument("--transaction-import-path", default="")
    confirm_candidate.add_argument("--holdings-book-path", default="")
    confirm_candidate.add_argument("--db", default="")
    confirm_candidate.add_argument("--json", action="store_true")

    dropbox = sub.add_parser("process-dropbox")
    dropbox.add_argument("--inbox-dir", default="")
    dropbox.add_argument("--source-system", default="ChatDropbox")
    dropbox.add_argument("--min-age-seconds", type=float, default=1.0)
    dropbox.add_argument("--limit", type=int, default=100)
    dropbox.add_argument("--db", default="")
    dropbox.add_argument("--json", action="store_true")

    inbox = sub.add_parser("dropbox-path")
    inbox.add_argument("--json", action="store_true")

    heartbeat = sub.add_parser("heartbeat")
    heartbeat.add_argument("--system-name", default="ResearchBus")
    heartbeat.add_argument("--status", default="Ready")
    heartbeat.add_argument("--capability", action="append", default=[])
    heartbeat.add_argument("--payload-json", default="{}")
    heartbeat.add_argument("--db", default="")

    status = sub.add_parser("status")
    status.add_argument("--db", default="")
    status.add_argument("--json", action="store_true")

    audit = sub.add_parser("audit")
    audit.add_argument("--db", default="")
    audit.add_argument("--schema-path", default="")
    audit.add_argument("--ai-research-root", default="")
    audit.add_argument("--output-path", default="")
    audit.add_argument("--no-write", action="store_true")
    audit.add_argument("--json", action="store_true")

    args = parser.parse_args()
    db_path = Path(args.db).expanduser() if getattr(args, "db", "") else None

    if args.command == "submit-chat":
        text = sys.stdin.read() if args.text == "-" else args.text
        payload = submit_chat_input(
            text,
            source_system=args.source_system,
            author=args.author,
            channel=args.channel,
            attachments=_chat_attachments(args.attachment_path, args.attachment_json),
            db_path=db_path,
        )
    elif args.command == "submit-request":
        request_payload = json.loads(args.payload_json)
        payload = submit_bus_request(
            args.type,
            request_payload,
            source_system=args.source_system,
            target_system=args.target_system,
            priority=args.priority,
            db_path=db_path,
        ).to_dict()
    elif args.command == "submit-webhook":
        if args.payload_json:
            webhook_payload = json.loads(args.payload_json)
        elif args.text:
            webhook_payload = sys.stdin.read() if args.text == "-" else args.text
        else:
            webhook_payload = json.loads(sys.stdin.read())
        payload = submit_webhook_payload(webhook_payload, source_system=args.source_system, db_path=db_path)
    elif args.command == "process":
        payload = process_pending_bus_requests(system_name=args.system_name, limit=args.limit, db_path=db_path)
    elif args.command == "confirm-holding-candidate":
        payload = confirm_holding_update_candidate(
            args.candidate_id,
            db_path=db_path,
            holding_import_path=args.holding_import_path or None,
            transaction_import_path=args.transaction_import_path or None,
            holdings_book_path=args.holdings_book_path or None,
        )
    elif args.command == "process-dropbox":
        payload = process_chat_dropbox(
            Path(args.inbox_dir).expanduser() if args.inbox_dir else None,
            db_path=db_path,
            default_source_system=args.source_system,
            min_age_seconds=args.min_age_seconds,
            limit=args.limit,
        )
    elif args.command == "heartbeat":
        heartbeat_system(
            args.system_name,
            status=args.status,
            capabilities=args.capability,
            payload=json.loads(args.payload_json),
            db_path=db_path,
        )
        payload = {"system_name": args.system_name, "status": args.status, "capabilities": args.capability}
    elif args.command == "dropbox-path":
        payload = {"inbox_dir": str(CHAT_DROPBOX_DIR)}
    elif args.command == "audit":
        payload = run_research_bus_interop_audit(
            db_path=db_path,
            schema_path=Path(args.schema_path).expanduser() if args.schema_path else None,
            ai_research_root=Path(args.ai_research_root).expanduser() if args.ai_research_root else None,
            output_path=None if args.no_write else (Path(args.output_path).expanduser() if args.output_path else AUDIT_OUTPUT_PATH),
        )
    else:
        payload = {
            "requests": bus_api_requests_frame(db_path, limit=50).to_dict("records"),
            "pending": pending_bus_requests_frame(db_path=db_path, target_system="ResearchBus", limit=50).to_dict("records"),
            "chat_inputs": bus_chat_inputs_frame(db_path, limit=50).to_dict("records"),
            "heartbeats": bus_heartbeats_frame(db_path).to_dict("records"),
            "health": research_bus_health_summary(db_path=db_path),
        }

    if getattr(args, "json", False):
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
        return
    if isinstance(payload, dict):
        for key, value in payload.items():
            print(f"{key}: {value}")
    else:
        print(payload)


def _chat_attachments(paths: list[str], attachment_json_values: list[str]) -> list[dict[str, object]]:
    attachments: list[dict[str, object]] = []
    for path in paths:
        clean_path = str(path or "").strip()
        if clean_path:
            expanded = Path(clean_path).expanduser()
            attachments.append({"path": str(expanded), "name": expanded.name, "source": "cli"})
    for raw in attachment_json_values:
        if not str(raw or "").strip():
            continue
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            attachments.append(parsed)
        elif isinstance(parsed, list):
            attachments.extend(item for item in parsed if isinstance(item, dict))
        else:
            raise ValueError("--attachment-json must be a JSON object or array of objects.")
    return attachments


if __name__ == "__main__":
    main()
