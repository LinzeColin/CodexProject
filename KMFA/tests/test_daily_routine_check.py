from __future__ import annotations

import unittest
import zipfile
from datetime import date, datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from KMFA.tools.daily_routine_check.archive_reader import DwsArchiveReader
from KMFA.tools.daily_routine_check.healthcheck import build_source_readiness
from KMFA.tools.daily_routine_check.ledger import connect, write_run_payload
from KMFA.tools.daily_routine_check.main import (
    build_notification_events,
    build_run_summary,
    evaluate_cash_risk,
    flag_merged_results,
    load_rules,
    run_sqlite_cleanup,
)
from KMFA.tools.daily_routine_check.models import RoutineRule, SourceMessage
from KMFA.tools.daily_routine_check.rule_engine import evaluate_rule
from KMFA.tools.daily_routine_check.schedule_rules import rules_for_trigger_window


def write_dws_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w") as zf:
        for group, sender in (("付款请示群", "杨婷"), ("生产管理群", "黄婷")):
            zf.writestr(
                f"DWS_Outputs/{group}/chat_records/chat_records.csv",
                "group_name,open_message_id,message_time,sender_name,content,resource_count,resource_types\n"
                f"{group},{group}-m1,2026-07-07 10:00:00,{sender},资金账户明细表 可用资金合计 800000,0,\n",
            )
            zf.writestr(
                f"DWS_Outputs/{group}/_manifest/manifest.csv",
                "group_name,message_id,message_time,sender_name,resource_type,output_path,sha256,status\n"
                f"{group},{group}-m1,2026-07-07 10:00:00,{sender},image,files/0707/{group}.png,sha-{group},downloaded\n",
            )


class TriggerWindowTests(unittest.TestCase):
    def setUp(self) -> None:
        _, self.rules = load_rules("KMFA/metadata/daily_routine_check/routine_rules.public.yaml")

    def test_morning_window_evaluates_payment_daily_and_monday_rules(self) -> None:
        evaluated, skipped = rules_for_trigger_window(self.rules, date(2026, 7, 6), "morning_1135")
        self.assertEqual(
            {rule.rule_id for rule in evaluated},
            {
                "PAY_DAILY_CASH_ACCOUNT",
                "PAY_DAILY_CASH_FLOW",
                "PAY_MON_EXISTING_BILLS",
                "PAY_MON_DEPOSIT_COLLECTION",
                "PAY_MON_COLLECTION_DETAIL",
            },
        )
        self.assertIn("PROD_DAILY_PERSONNEL", {rule.rule_id for rule in skipped})

    def test_evening_window_evaluates_production_and_monthly_third_friday_rules(self) -> None:
        evaluated, skipped = rules_for_trigger_window(self.rules, date(2026, 7, 17), "evening_1705")
        self.assertEqual(
            {rule.rule_id for rule in evaluated},
            {
                "PROD_DAILY_PERSONNEL",
                "PROD_FRI_WORKER_HOURS",
                "PROD_FRI_PAYABLES",
                "PAY_MONTHLY_TAX_RETURN",
                "PAY_MONTHLY_TAX_SETTLEMENT",
            },
        )
        self.assertIn("PAY_DAILY_CASH_ACCOUNT", {rule.rule_id for rule in skipped})

    def test_run_summary_records_beijing_window_and_rule_accounting(self) -> None:
        summary = build_run_summary(
            run_at_beijing="2026-07-17T17:05:00+08:00",
            check_date=date(2026, 7, 17),
            trigger_window="evening_1705",
            rules_evaluated=["PROD_DAILY_PERSONNEL"],
            rules_skipped=["PAY_DAILY_CASH_ACCOUNT"],
            data_quality_issues=[{"issue_type": "SOURCE_MISSING", "group_name": "生产管理群"}],
        )
        self.assertEqual(summary["timezone"], "Asia/Shanghai")
        self.assertEqual(summary["run_at_beijing"], "2026-07-17T17:05:00+08:00")
        self.assertEqual(summary["check_date"], "2026-07-17")
        self.assertEqual(summary["trigger_window"], "evening_1705")
        self.assertEqual(summary["rules_evaluated"], ["PROD_DAILY_PERSONNEL"])
        self.assertEqual(summary["rules_skipped"], ["PAY_DAILY_CASH_ACCOUNT"])
        self.assertEqual(summary["data_quality_issues"][0]["issue_type"], "SOURCE_MISSING")

    def test_trigger_window_not_yaml_due_time_controls_evaluation(self) -> None:
        rule = RoutineRule(
            rule_id="PROD_THU_FUND_PLAN",
            group_name="生产管理群",
            frequency="weekly",
            due_time="17:30",
            required_senders=("黄婷", "李权智"),
            artifact_name="资金计划",
            document_family="production_fund_plan",
            keywords_positive=("资金计划",),
            weekdays=("thursday",),
            trigger_window="evening_1705",
        )
        msg = SourceMessage(
            group_name="生产管理群",
            message_id="m-fund-plan",
            message_time=datetime(2026, 7, 9, 16, 50),
            sender_name="李权智",
            content="今日资金计划",
        )
        result = evaluate_rule(rule, [msg], date(2026, 7, 9), datetime(2026, 7, 9, 17, 5))
        self.assertEqual(result.status, "OK")

    def test_late_delivery_keeps_match_and_sets_p1_reminder(self) -> None:
        rule = RoutineRule(
            rule_id="PAY_DAILY_CASH_ACCOUNT",
            group_name="付款请示群",
            frequency="daily",
            due_time="10:30",
            required_senders=("杨婷",),
            artifact_name="资金账户明细表",
            document_family="cash_account_statement",
            keywords_positive=("资金账户明细表",),
            trigger_window="morning_1135",
        )
        msg = SourceMessage(
            group_name="付款请示群",
            message_id="late-account",
            message_time=datetime(2026, 7, 7, 11, 0),
            sender_name="杨婷",
            content="资金账户明细表",
        )
        result = evaluate_rule(rule, [msg], date(2026, 7, 7), datetime(2026, 7, 7, 11, 35))
        self.assertEqual(result.status, "LATE")
        self.assertEqual(result.abnormal_type, "late")
        self.assertEqual(result.reminder_level, "P1")

    def test_wrong_document_family_sets_review_reminder(self) -> None:
        rule = RoutineRule(
            rule_id="PAY_DAILY_CASH_ACCOUNT",
            group_name="付款请示群",
            frequency="daily",
            due_time="10:30",
            required_senders=("杨婷",),
            artifact_name="资金账户明细表",
            document_family="cash_account_statement",
            keywords_positive=("资金账户明细表",),
            keywords_negative=("资金流水明细", "资金明细"),
            trigger_window="morning_1135",
        )
        msg = SourceMessage(
            group_name="付款请示群",
            message_id="wrong-flow",
            message_time=datetime(2026, 7, 7, 10, 0),
            sender_name="杨婷",
            content="资金流水明细",
        )
        result = evaluate_rule(rule, [msg], date(2026, 7, 7), datetime(2026, 7, 7, 11, 35))
        self.assertEqual(result.status, "WRONG")
        self.assertEqual(result.abnormal_type, "wrong")
        self.assertEqual(result.reminder_level, "P1")

    def test_valid_delivery_after_wrong_family_is_not_marked_wrong(self) -> None:
        rule = RoutineRule(
            rule_id="PAY_DAILY_CASH_ACCOUNT",
            group_name="付款请示群",
            frequency="daily",
            due_time="10:30",
            required_senders=("杨婷",),
            artifact_name="资金账户明细表",
            document_family="cash_account_statement",
            keywords_positive=("资金账户明细表",),
            keywords_negative=("资金流水明细", "资金明细"),
            trigger_window="morning_1135",
        )
        messages = [
            SourceMessage(
                group_name="付款请示群",
                message_id="wrong-flow",
                message_time=datetime(2026, 7, 7, 10, 0),
                sender_name="杨婷",
                content="资金流水明细",
            ),
            SourceMessage(
                group_name="付款请示群",
                message_id="correct-account",
                message_time=datetime(2026, 7, 7, 10, 5),
                sender_name="杨婷",
                content="资金账户明细表",
            ),
        ]
        result = evaluate_rule(rule, messages, date(2026, 7, 7), datetime(2026, 7, 7, 11, 35))
        self.assertEqual(result.status, "OK")
        self.assertEqual(result.matched_message_id, "correct-account")

    def test_merged_message_sets_review_reminder_for_independent_artifacts(self) -> None:
        account = RoutineRule(
            rule_id="PAY_DAILY_CASH_ACCOUNT",
            group_name="付款请示群",
            frequency="daily",
            due_time="10:30",
            required_senders=("杨婷",),
            artifact_name="资金账户明细表",
            document_family="cash_account_statement",
            keywords_positive=("资金账户明细表",),
            trigger_window="morning_1135",
        )
        flow = RoutineRule(
            rule_id="PAY_DAILY_CASH_FLOW",
            group_name="付款请示群",
            frequency="daily",
            due_time="10:30",
            required_senders=("杨婷",),
            artifact_name="资金流水明细",
            document_family="cash_flow_detail",
            keywords_positive=("资金流水明细",),
            trigger_window="morning_1135",
        )
        msg = SourceMessage(
            group_name="付款请示群",
            message_id="merged-one-message",
            message_time=datetime(2026, 7, 7, 10, 0),
            sender_name="杨婷",
            content="资金账户明细表 资金流水明细",
        )
        results = [
            evaluate_rule(account, [msg], date(2026, 7, 7), datetime(2026, 7, 7, 11, 35)),
            evaluate_rule(flow, [msg], date(2026, 7, 7), datetime(2026, 7, 7, 11, 35)),
        ]
        flagged = flag_merged_results(results)
        self.assertEqual({result.status for result in flagged}, {"MERGED_REVIEW"})
        self.assertEqual({result.abnormal_type for result in flagged}, {"merged"})
        self.assertEqual({result.reminder_level for result in flagged}, {"P1"})

    def test_notification_events_include_abnormal_type_and_reminder_level(self) -> None:
        rule = RoutineRule(
            rule_id="PAY_DAILY_CASH_ACCOUNT",
            group_name="付款请示群",
            frequency="daily",
            due_time="10:30",
            required_senders=("杨婷",),
            artifact_name="资金账户明细表",
            document_family="cash_account_statement",
            keywords_positive=("资金账户明细表",),
            trigger_window="morning_1135",
        )
        msg = SourceMessage(
            group_name="付款请示群",
            message_id="late-account",
            message_time=datetime(2026, 7, 7, 11, 0),
            sender_name="杨婷",
            content="资金账户明细表",
        )
        result = evaluate_rule(rule, [msg], date(2026, 7, 7), datetime(2026, 7, 7, 11, 35))
        events = build_notification_events([result], [], "张霖泽")

        self.assertEqual(events[0]["event_type"], "LATE_ROUTINE_ITEM")
        self.assertEqual(events[0]["payload"]["abnormal_type"], "late")
        self.assertEqual(events[0]["payload"]["reminder_level"], "P1")

    def test_cash_risk_extracts_yang_ting_total_and_sets_p1(self) -> None:
        raw_rules, _ = load_rules("KMFA/metadata/daily_routine_check/routine_rules.public.yaml")
        cash_config = {
            "scope": {"group_name": "付款请示群", "sender_name": "杨婷"},
            "thresholds": {"hard_threshold": 500000, "soft_threshold": 1000000},
            "extraction": {"total_available_cash_markers": ["可用资金合计", "总可用现金"]},
        }
        msg = SourceMessage(
            group_name="付款请示群",
            message_id="cash-account-p1",
            message_time=datetime(2026, 7, 7, 10, 0),
            sender_name="杨婷",
            content="资金账户明细表 今日余额 800000 可用资金合计 800000",
        )

        result = evaluate_cash_risk(
            cash_config,
            raw_rules["ocr_feature_profiles"],
            [msg],
            date(2026, 7, 7),
        )

        self.assertEqual(result.risk_level, "P1_YELLOW")
        self.assertEqual(result.total_available_cash, 800000)
        self.assertEqual(result.source_message_id, "cash-account-p1")
        self.assertGreaterEqual(result.confidence, 0.80)

    def test_cash_risk_review_event_is_notified_with_payload(self) -> None:
        cash_config = {
            "scope": {"group_name": "付款请示群", "sender_name": "杨婷"},
            "thresholds": {"hard_threshold": 500000, "soft_threshold": 1000000},
            "extraction": {"total_available_cash_markers": ["可用资金合计", "总可用现金"]},
        }
        msg = SourceMessage(
            group_name="付款请示群",
            message_id="cash-account-review",
            message_time=datetime(2026, 7, 7, 10, 0),
            sender_name="杨婷",
            content="资金账户明细表 图片见附件",
            resource_count=1,
            resource_types=("image",),
        )
        cash_result = evaluate_cash_risk(cash_config, {}, [msg], date(2026, 7, 7))
        events = build_notification_events([], [], "张霖泽", cash_result=cash_result)

        self.assertEqual(events[0]["event_type"], "CASH_NEEDS_REVIEW")
        self.assertEqual(events[0]["payload"]["risk_level"], "NEEDS_REVIEW")
        self.assertEqual(events[0]["payload"]["source_message_id"], "cash-account-review")

    def test_sqlite_payload_persists_result_detail_and_cleanup_event(self) -> None:
        with TemporaryDirectory() as tmp:
            db_path = f"{tmp}/daily_routine_check.sqlite"
            conn = connect(db_path)
            payload = {
                "check_date": "2026-07-07",
                "results": [{
                    "rule_id": "PAY_DAILY_CASH_ACCOUNT",
                    "check_date": "2026-07-07",
                    "status": "LATE",
                    "group_name": "付款请示群",
                    "artifact_name": "资金账户明细表",
                    "matched_message_id": "late-account",
                    "confidence": 1.0,
                }],
                "cash_risk_result": {
                    "report_date": "2026-07-07",
                    "risk_level": "P1_YELLOW",
                    "total_available_cash": 800000,
                    "hard_threshold": 500000,
                    "soft_threshold": 1000000,
                    "source_message_id": "cash-account-p1",
                    "source_file_sha256": None,
                    "confidence": 0.9,
                },
                "notification_events": [{
                    "event_type": "LATE_ROUTINE_ITEM",
                    "target_label": "张霖泽",
                    "idempotency_key": "late:2026-07-07:PAY_DAILY_CASH_ACCOUNT",
                }],
                "data_quality_issues": [{
                    "issue_type": "SOURCE_STALE",
                    "issue_code": "SOURCE_CHAT_RECORDS_STALE",
                    "group_name": "付款请示群",
                    "check_date": "2026-07-07",
                }],
            }
            write_run_payload(conn, "run-test", payload)
            conn.close()

            cleanup = run_sqlite_cleanup(db_path)

            conn = connect(db_path)
            try:
                counts = {
                    table: conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                    for table in [
                        "run_log",
                        "routine_check_results",
                        "cash_risk_results",
                        "notification_events",
                        "data_quality_issues",
                        "cleanup_events",
                    ]
                }
            finally:
                conn.close()

        self.assertEqual(counts["run_log"], 1)
        self.assertEqual(counts["routine_check_results"], 1)
        self.assertEqual(counts["cash_risk_results"], 1)
        self.assertEqual(counts["notification_events"], 1)
        self.assertEqual(counts["data_quality_issues"], 1)
        self.assertEqual(counts["cleanup_events"], 1)
        self.assertIn("wal_checkpoint", cleanup["actions"])

    def test_reader_reports_missing_and_stale_sources(self) -> None:
        with TemporaryDirectory() as tmp:
            reader = DwsArchiveReader(tmp)
            missing = reader.inspect_group_sources("付款请示群", date(2026, 7, 7))
            self.assertEqual(missing[0]["issue_type"], "SOURCE_MISSING")

            group_chat = reader.group_path("生产管理群") / "chat_records"
            group_chat.mkdir(parents=True)
            group_manifest = reader.group_path("生产管理群") / "_manifest"
            group_manifest.mkdir(parents=True)
            (group_chat / "chat_records.csv").write_text(
                "group_name,open_message_id,message_time,sender_name,content,resource_count,resource_types\n"
                "生产管理群,m1,2026-07-06 17:00:00,黄婷,每日人员表,0,\n",
                encoding="utf-8",
            )
            (group_manifest / "manifest.csv").write_text(
                "group_name,message_id,message_time,sender_name,resource_type,output_path,sha256,status\n",
                encoding="utf-8",
            )
            stale = reader.inspect_group_sources("生产管理群", date(2026, 7, 7))
            self.assertEqual(stale[0]["issue_type"], "SOURCE_STALE")

    def test_reader_streams_messages_and_manifest_from_dws_zip(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            zip_path = base / "DWS_Outputs.zip"
            write_dws_zip(zip_path)

            reader = DwsArchiveReader(base / "DWS_Outputs")
            issues = reader.inspect_group_sources("付款请示群", date(2026, 7, 7))
            messages = reader.read_messages("付款请示群")
            files = reader.read_files("付款请示群")

        self.assertEqual(issues, [])
        self.assertEqual(messages[0].message_id, "付款请示群-m1")
        self.assertEqual(files[0].sha256, "sha-付款请示群")
        self.assertTrue(files[0].absolute_path.startswith("zip://"))
        self.assertIn("DWS_Outputs.zip!", files[0].absolute_path)

    def test_healthcheck_accepts_readable_zip_as_primary_input(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            write_dws_zip(base / "DWS_Outputs.zip")
            readiness = build_source_readiness(base / "DWS_Outputs")

        self.assertFalse(readiness["direct_input_ready"])
        self.assertTrue(readiness["zip_present"])
        self.assertTrue(readiness["zip_input_ready"])
        self.assertEqual(readiness["status"], "READY")
        self.assertEqual(readiness["next_enable_conditions"], [])

    def test_healthcheck_reports_unreadable_zip_without_requiring_direct_folder(self) -> None:
        with TemporaryDirectory() as tmp:
            base = Path(tmp)
            (base / "DWS_Outputs.zip").write_text("placeholder", encoding="utf-8")
            (base / "DWS_Archive" / "付款请示群" / "files" / "0707").mkdir(parents=True)
            readiness = build_source_readiness(base / "DWS_Outputs")

        self.assertFalse(readiness["direct_input_ready"])
        self.assertTrue(readiness["zip_present"])
        self.assertFalse(readiness["zip_input_ready"])
        self.assertTrue(readiness["archive_present"])
        self.assertEqual(readiness["status"], "ZIP_INPUT_UNREADABLE")
        self.assertTrue(any(
            "DWS_Outputs.zip" in item and "readable" in item
            for item in readiness["next_enable_conditions"]
        ))


if __name__ == "__main__":
    unittest.main()
