from __future__ import annotations

import unittest
from datetime import date, datetime
from tempfile import TemporaryDirectory

from KMFA.tools.daily_routine_check.archive_reader import DwsArchiveReader
from KMFA.tools.daily_routine_check.main import build_notification_events, build_run_summary, flag_merged_results, load_rules
from KMFA.tools.daily_routine_check.models import RoutineRule, SourceMessage
from KMFA.tools.daily_routine_check.rule_engine import evaluate_rule
from KMFA.tools.daily_routine_check.schedule_rules import rules_for_trigger_window


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


if __name__ == "__main__":
    unittest.main()
