#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

export PYTHONPATH="${PYTHONPATH:-src}"

MAX_SOURCES="${MAX_SOURCES:-3}"
MAX_PAGES_PER_SOURCE="${MAX_PAGES_PER_SOURCE:-2}"
MAX_LINKS_PER_PAGE="${MAX_LINKS_PER_PAGE:-20}"
MAX_ANALYZE="${MAX_ANALYZE:-20}"
MAX_INTERPRETATION_DOCUMENTS="${MAX_INTERPRETATION_DOCUMENTS:-10}"
MIN_EXTERNAL_REFERENCES="${MIN_EXTERNAL_REFERENCES:-5}"
MIN_EXTERNAL_PLATFORMS="${MIN_EXTERNAL_PLATFORMS:-2}"
QUALITY_RULES_FILE="${QUALITY_RULES_FILE:-rules/quality_gates.json}"
INDUSTRY_PRIORITY_FILE="${INDUSTRY_PRIORITY_FILE:-config/industry_priorities.json}"
AI_RESEARCH_POLICY_REQUEST_FILE="${AI_RESEARCH_POLICY_REQUEST_FILE:-}"
FETCH_INTERPRETATION_RESULTS="${FETCH_INTERPRETATION_RESULTS:-1}"
FETCH_SEARCH_RESULT_PAGES="${FETCH_SEARCH_RESULT_PAGES:-1}"
INTERPRETATION_REQUEST_TIMEOUT="${INTERPRETATION_REQUEST_TIMEOUT:-20}"
INTERPRETATION_REQUEST_RETRIES="${INTERPRETATION_REQUEST_RETRIES:-1}"
INTERPRETATION_REQUEST_DELAY_SECONDS="${INTERPRETATION_REQUEST_DELAY_SECONDS:-0.2}"
BILIBILI_COOKIE_FILE="${BILIBILI_COOKIE_FILE:-}"
SEARCH_SECRETS_FILE="${SEARCH_SECRETS_FILE:-}"
PLATFORM_AUTH_FILE="${PLATFORM_AUTH_FILE:-}"
MIN_AUTHORITY_SCORE="${MIN_AUTHORITY_SCORE:-60}"
ANALYSIS_MODE="${ANALYSIS_MODE:-template}"
ALLOW_INSECURE_TLS="${ALLOW_INSECURE_TLS:-1}"
DOCUMENT_SINCE="${DOCUMENT_SINCE:-2025-01-01}"
AUTOMATION_RUN_ID="${AUTOMATION_RUN_ID:-$(date +%Y%m%d%H%M%S)}"
AUTOMATION_DASHBOARD="${AUTOMATION_DASHBOARD:-reports/automation_run_dashboard.html}"
CURRENT_STEP_KEY=""
CURRENT_STEP_LABEL=""
CURRENT_STEP_ACTIVE=0

record_step() {
  local step_key="$1"
  local step_label="$2"
  local status="$3"
  local exit_code="${4:-}"
  local error_summary="${5:-}"
  local record_args=(
    --db data/source_registry.sqlite
    automation-step
    --data-dir data
    --run-id "$AUTOMATION_RUN_ID"
    --step-key "$step_key"
    --step-label "$step_label"
    --status "$status"
  )
  if [[ -n "$exit_code" ]]; then
    record_args+=(--exit-code "$exit_code")
  fi
  if [[ -n "$error_summary" ]]; then
    record_args+=(--error-summary "$error_summary")
  fi
  python3 -m source_registry "${record_args[@]}" >/dev/null
}

render_automation_dashboard() {
  python3 -m source_registry --db data/source_registry.sqlite automation-dashboard \
    --data-dir data \
    --output "$AUTOMATION_DASHBOARD" >/dev/null || true
}

cleanup_on_exit() {
  local exit_code=$?
  if [[ "$exit_code" -ne 0 && "$CURRENT_STEP_ACTIVE" -eq 1 ]]; then
    set +e
    record_step "$CURRENT_STEP_KEY" "$CURRENT_STEP_LABEL" failed "$exit_code" "script exited before step completed"
    render_automation_dashboard
    python3 -m source_registry --db data/source_registry.sqlite automation-lock-clean \
      --data-dir data \
      --content-db data/policy_documents.sqlite >/dev/null || true
  fi
}

trap cleanup_on_exit EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

run_step() {
  local step_key="$1"
  local step_label="$2"
  shift 2
  record_step "$step_key" "$step_label" running
  CURRENT_STEP_KEY="$step_key"
  CURRENT_STEP_LABEL="$step_label"
  CURRENT_STEP_ACTIVE=1
  set +e
  "$@"
  local exit_code=$?
  set -e
  if [[ "$exit_code" -eq 0 ]]; then
    record_step "$step_key" "$step_label" completed "$exit_code"
    CURRENT_STEP_ACTIVE=0
  else
    record_step "$step_key" "$step_label" failed "$exit_code" "command exited non-zero"
    CURRENT_STEP_ACTIVE=0
    render_automation_dashboard
    exit "$exit_code"
  fi
}

run_step_quiet() {
  local step_key="$1"
  local step_label="$2"
  shift 2
  record_step "$step_key" "$step_label" running
  CURRENT_STEP_KEY="$step_key"
  CURRENT_STEP_LABEL="$step_label"
  CURRENT_STEP_ACTIVE=1
  set +e
  "$@" >/dev/null
  local exit_code=$?
  set -e
  if [[ "$exit_code" -eq 0 ]]; then
    record_step "$step_key" "$step_label" completed "$exit_code"
    CURRENT_STEP_ACTIVE=0
  else
    record_step "$step_key" "$step_label" failed "$exit_code" "command exited non-zero"
    CURRENT_STEP_ACTIVE=0
    render_automation_dashboard
    exit "$exit_code"
  fi
}

run_step_quiet pipeline_lock_clean "清理陈旧 pipeline lock" \
  python3 -m source_registry --db data/source_registry.sqlite automation-lock-clean \
  --data-dir data \
  --content-db data/policy_documents.sqlite

run_step_quiet init_registry "初始化来源库 schema" \
  python3 -m source_registry --db data/source_registry.sqlite init
run_step_quiet seed_registry "导入官方来源种子" \
  python3 -m source_registry --db data/source_registry.sqlite seed --seed-file config/seed_sources.json

if [[ -n "$AI_RESEARCH_POLICY_REQUEST_FILE" ]]; then
  REQUEST_PRIORITY_FILE="data/ai_research_policy_request_industries.json"
  run_step_quiet ai_research_priority "生成 AI 行研请求行业优先级" \
    python3 -m source_registry --db data/source_registry.sqlite ai-research-priority \
    --request-file "$AI_RESEARCH_POLICY_REQUEST_FILE" \
    --base-file "$INDUSTRY_PRIORITY_FILE" \
    --output "$REQUEST_PRIORITY_FILE"
  INDUSTRY_PRIORITY_FILE="$REQUEST_PRIORITY_FILE"
fi

args=(
  --db data/source_registry.sqlite
  run
  --content-db data/policy_documents.sqlite
  --data-dir data
  --report-dir reports
  --max-sources "$MAX_SOURCES"
  --max-pages-per-source "$MAX_PAGES_PER_SOURCE"
  --max-links-per-page "$MAX_LINKS_PER_PAGE"
  --max-analyze "$MAX_ANALYZE"
  --max-interpretation-documents "$MAX_INTERPRETATION_DOCUMENTS"
  --min-external-references "$MIN_EXTERNAL_REFERENCES"
  --min-external-platforms "$MIN_EXTERNAL_PLATFORMS"
  --quality-rules-file "$QUALITY_RULES_FILE"
  --interpretation-request-timeout "$INTERPRETATION_REQUEST_TIMEOUT"
  --interpretation-request-retries "$INTERPRETATION_REQUEST_RETRIES"
  --interpretation-request-delay-seconds "$INTERPRETATION_REQUEST_DELAY_SECONDS"
  --min-authority-score "$MIN_AUTHORITY_SCORE"
  --interpretation-source-file config/interpretation_sources.json
  --industry-priority-file "$INDUSTRY_PRIORITY_FILE"
  --document-since "$DOCUMENT_SINCE"
  --analysis-mode "$ANALYSIS_MODE"
  --mode automation
  --json
)

if [[ "$ALLOW_INSECURE_TLS" == "1" ]]; then
  args+=(--allow-insecure-tls)
fi

if [[ "$FETCH_INTERPRETATION_RESULTS" == "1" ]]; then
  args+=(--fetch-interpretation-results)
fi

if [[ "$FETCH_SEARCH_RESULT_PAGES" == "1" ]]; then
  args+=(--fetch-search-result-pages)
fi

if [[ -n "$BILIBILI_COOKIE_FILE" ]]; then
  args+=(--bilibili-cookie-file "$BILIBILI_COOKIE_FILE")
fi

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step pipeline_run "采集、分析并生成单文件 PDF 报告" \
  python3 -m source_registry "${args[@]}"

run_step_quiet ops_dashboard "生成运营总览 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite ops-dashboard \
  --content-db data/policy_documents.sqlite \
  --data-dir data \
  --analysis-mode "$ANALYSIS_MODE" \
  --min-external-references "$MIN_EXTERNAL_REFERENCES" \
  --min-external-platforms "$MIN_EXTERNAL_PLATFORMS" \
  --quality-rules-file "$QUALITY_RULES_FILE" \
  --output reports/policy_ops_dashboard.html

platform_coverage_args=(
  --db data/source_registry.sqlite
  platform-coverage
  --content-db data/policy_documents.sqlite
  --interpretation-source-file config/interpretation_sources.json
  --output reports/platform_coverage_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  platform_coverage_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  platform_coverage_args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step_quiet platform_coverage "生成平台覆盖矩阵 dashboard" \
  python3 -m source_registry "${platform_coverage_args[@]}"

run_step_quiet platform_parsers "生成平台解析器能力 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite platform-parsers \
  --parser-file config/platform_parsers.json \
  --output reports/platform_parser_dashboard.html

platform_parser_validation_args=(
  --db data/source_registry.sqlite
  platform-parser-validate
  --parser-file config/platform_parsers.json
  --output reports/platform_parser_validation_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  platform_parser_validation_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  platform_parser_validation_args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step_quiet platform_parser_validation "生成平台解析器验收 dashboard" \
  python3 -m source_registry "${platform_parser_validation_args[@]}"

run_step_quiet platform_parser_samples "生成平台解析样本验收 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite platform-parser-samples \
  --content-db data/policy_documents.sqlite \
  --parser-file config/platform_parsers.json \
  --output reports/platform_parser_sample_dashboard.html

run_step_quiet crawl_policy "生成抓取策略 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite crawl-policy \
  --policy-file config/crawl_policies.json \
  --output reports/crawl_policy_dashboard.html

run_step_quiet attachment_parsers "生成附件解析能力 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite attachment-parsers \
  --parser-file config/attachment_parsers.json \
  --output reports/attachment_parser_dashboard.html

setup_wizard_args=(
  --db data/source_registry.sqlite
  setup-wizard
  --content-db data/policy_documents.sqlite
  --interpretation-source-file config/interpretation_sources.json
  --output reports/setup_wizard_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  setup_wizard_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  setup_wizard_args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step_quiet setup_wizard "生成接入向导 dashboard" \
  python3 -m source_registry "${setup_wizard_args[@]}"

credential_doctor_args=(
  --db data/source_registry.sqlite
  credential-doctor
  --output reports/credential_doctor_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  credential_doctor_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  credential_doctor_args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step_quiet credential_doctor "生成凭据体检 dashboard" \
  python3 -m source_registry "${credential_doctor_args[@]}"

platform_auth_validate_args=(
  --db data/source_registry.sqlite
  platform-auth-validate
  --output reports/platform_auth_validation_dashboard.html
)

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  platform_auth_validate_args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step_quiet platform_auth_validate "生成平台授权验证 dashboard" \
  python3 -m source_registry "${platform_auth_validate_args[@]}"

search_secret_intake_args=(
  --db data/source_registry.sqlite
  search-secret-intake
  --output reports/search_secret_intake_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  search_secret_intake_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

run_step_quiet search_secret_intake "生成搜索 API 接入清单 dashboard" \
  python3 -m source_registry "${search_secret_intake_args[@]}"

search_validate_args=(
  --db data/source_registry.sqlite
  search-validate
  --offline
  --output reports/search_validation_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  search_validate_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

run_step_quiet search_validate "生成搜索 API 验证 dashboard" \
  python3 -m source_registry "${search_validate_args[@]}"

run_step_quiet report_check "生成报告产物自检 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite report-check \
  --content-db data/policy_documents.sqlite \
  --output reports/report_artifact_check_dashboard.html

run_step_quiet quality_gates "生成质量门槛 dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite quality-gates \
  --content-db data/policy_documents.sqlite \
  --data-dir data \
  --analysis-mode "$ANALYSIS_MODE" \
  --quality-rules-file "$QUALITY_RULES_FILE" \
  --output reports/quality_gates_dashboard.html

automation_readiness_args=(
  --db data/source_registry.sqlite
  automation-readiness
  --content-db data/policy_documents.sqlite
  --data-dir data
  --analysis-mode "$ANALYSIS_MODE"
  --quality-rules-file "$QUALITY_RULES_FILE"
  --schedule-time 09:00
  --schedule-time 21:00
  --output reports/automation_readiness_dashboard.html
)

if [[ -n "$SEARCH_SECRETS_FILE" ]]; then
  automation_readiness_args+=(--search-secrets-file "$SEARCH_SECRETS_FILE")
fi

if [[ -n "$PLATFORM_AUTH_FILE" ]]; then
  automation_readiness_args+=(--platform-auth-file "$PLATFORM_AUTH_FILE")
fi

run_step_quiet automation_readiness "生成自动化运行就绪 dashboard" \
  python3 -m source_registry "${automation_readiness_args[@]}"

run_step_quiet benchmark_dashboard "生成参考模型 benchmark dashboard" \
  python3 -m source_registry --db data/source_registry.sqlite benchmark-dashboard \
  --benchmark-file config/benchmark_models.json \
  --output reports/benchmark_dashboard.html

render_automation_dashboard
