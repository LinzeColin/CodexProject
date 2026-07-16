from __future__ import annotations

from pathlib import Path


PFI_ROOT = Path(__file__).resolve().parents[1]


def test_formal_shell_loads_the_stage10_backend_job_client_before_shell() -> None:
    index = (PFI_ROOT / "web/index.html").read_text(encoding="utf-8")
    timeline_ref = '<script src="./app/components/jobTimeline.js"></script>'
    runtime_ref = '<script src="./app/jobs/runtimeJobs.js"></script>'
    shell_ref = '<script src="./app/shell.js"></script>'

    assert timeline_ref in index
    assert runtime_ref in index
    assert index.index(timeline_ref) < index.index(runtime_ref) < index.index(shell_ref)


def test_runtime_job_adapter_maps_only_persisted_backend_state_and_real_units() -> None:
    source = (PFI_ROOT / "web/app/jobs/runtimeJobs.js").read_text(encoding="utf-8")

    assert 'schema: "PFIV025Stage10RuntimeJobsClientV1"' in source
    assert 'source: "durable_job_api"' in source
    assert 'progressTruth: "completed_units_over_total_units_only"' in source
    assert "timerBasedProgress: false" in source
    assert 'pollPurpose: "read_persisted_state_only"' in source
    assert "externalNetworkCalls: 0" in source
    for backend_state in (
        "queued",
        "running",
        "retrying",
        "succeeded",
        "failed",
        "cancelled",
        "dead_letter",
    ):
        assert f"{backend_state}:" in source
    assert 'retrying: "retrying"' in source
    assert 'dead_letter: "dead_letter"' in source
    assert "normalized.updatedAt >= currentUpdatedAt" in source
    for truth_field in (
        "job.progress?.completed_units",
        "job.progress?.total_units",
        "job.revision",
        "job.trace?.trace_id",
        "job.observability?.retry_count",
        "job.observability?.cache_fallback_used",
        "job.error?.code",
        "job.result?.artifact_uri",
    ):
        assert truth_field in source
    assert "setTimeout" not in source
    assert "setInterval" not in source
    assert "Date.now()" not in source


def test_cache_refresh_posts_then_polls_sqlite_without_synthetic_stage_timers() -> None:
    shell = (PFI_ROOT / "web/app/shell.js").read_text(encoding="utf-8")

    assert 'runtimeApiJson("/api/jobs/cache-refresh"' in shell
    assert "pollRuntimeJob(submitted.poll_uri" in shell
    assert "runtimeJobs.ingest(submitted.job)" in shell
    assert "job.progress?.completed_units" not in shell  # adapter owns optional chaining
    assert "progress.completed_units" in shell
    assert "progress.total_units" in shell
    assert "SQLite revision" in shell
    assert "restoreRuntimeJobsFromApi" in shell
    assert 'runtimeApiJson("/api/jobs?limit=20")' in shell
    assert "[...(payload.jobs || [])].reverse()" in shell
    assert 'job.job_type === "cache.refresh"' in shell
    for removed_fake_timer in ("skeletonTimer", "stageTimer", "durableTimer"):
        assert removed_fake_timer not in shell
    assert "cache-refresh-${Date.now()}" not in shell
    assert "jobApi?.succeed" not in shell
    assert "jobApi?.fail" not in shell


def test_timeline_renders_backend_trace_retry_error_and_result_without_timed_state() -> None:
    timeline = (PFI_ROOT / "web/app/components/jobTimeline.js").read_text(encoding="utf-8")

    assert 'job.source === "durable_job_api"' in timeline
    assert "SQLite revision" in timeline
    assert "job.traceId" in timeline
    assert "job.retryCount" in timeline
    assert "data-stage10-job-error" not in timeline  # DOM dataset is assigned as a property
    assert "error.dataset.stage10JobError" in timeline
    assert "result.dataset.stage10JobResult" in timeline
    assert '"retrying"' in timeline
    assert '"dead_letter"' in timeline
    assert 'retrying: "等待重试"' in timeline
    assert 'dead_letter: "死信"' in timeline
    assert "item.dataset.stage10BackendState = job.backendState" in timeline
    assert 'if (job.source === "durable_job_api") return;' in timeline
    assert "syntheticProgress" not in timeline
    assert "setInterval" not in timeline
