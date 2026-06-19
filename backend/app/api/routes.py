from pathlib import Path
from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.models.schemas import AnalysisCase, CaseCreateRequest, DashboardSummary, ModelProviderConfig, ReportArtifact
from app.services import db
from app.services.analysis import analyze_case
from app.services.reporting import generate_case_report

router = APIRouter(prefix="/api")


@router.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "wuhan-kaiming-assistant"}


@router.post("/cases", response_model=AnalysisCase)
def create_case(payload: CaseCreateRequest) -> dict:
    title = payload.title or {
        "dynamic": "旋转窑动态调测分析",
        "fault": "回转窑运行故障诊断",
        "gear": "大齿圈齿面修复评估",
        "machining": "机械加工工艺建议",
        "other": "综合工业运维咨询",
    }.get(payload.module.value, "工业运维分析")
    result = analyze_case(payload.module, payload.input_data, payload.uploaded_rows)
    case_id = db.create_case(payload.module.value, title, payload.input_data, payload.uploaded_file_name, result)
    case_data = db.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=500, detail="案例创建后读取失败")
    if payload.auto_generate_report:
        artifact = generate_report(case_id)
        if artifact.status != "ready":
            case_data = db.get_case(case_id)
            raise HTTPException(status_code=500, detail=artifact.message)
    case_data = db.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case_data


@router.get("/cases", response_model=List[AnalysisCase])
def list_cases(limit: int = 50) -> list:
    return db.list_cases(limit=limit)


@router.get("/cases/{case_id}", response_model=AnalysisCase)
def get_case(case_id: int) -> dict:
    case_data = db.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="案例不存在")
    return case_data


@router.post("/reports/{case_id}", response_model=ReportArtifact)
def generate_report(case_id: int) -> ReportArtifact:
    case_data = db.get_case(case_id)
    if not case_data:
        raise HTTPException(status_code=404, detail="案例不存在")
    try:
        path = generate_case_report(case_data)
        db.update_case_report(case_id, str(path), "ready")
        db.add_report(case_id, str(path), "ready", "PDF 报告生成成功")
        return ReportArtifact(case_id=case_id, path=str(path), status="ready", message="PDF 报告生成成功")
    except Exception as exc:  # noqa: BLE001 - API boundary
        db.update_case_report(case_id, None, "failed")
        db.add_report(case_id, "", "failed", str(exc))
        return ReportArtifact(case_id=case_id, path="", status="failed", message=f"PDF 报告生成失败：{exc}")


@router.get("/reports/{case_id}/download")
def download_report(case_id: int) -> FileResponse:
    case_data = db.get_case(case_id)
    if not case_data or not case_data.get("report_path"):
        raise HTTPException(status_code=404, detail="报告不存在")
    path = Path(case_data["report_path"])
    if not path.exists():
        raise HTTPException(status_code=404, detail="报告文件不存在")
    return FileResponse(str(path), media_type="application/pdf", filename=path.name)


@router.get("/dashboard/summary", response_model=DashboardSummary)
def dashboard_summary() -> dict:
    return db.dashboard_summary()


@router.get("/settings/models", response_model=List[ModelProviderConfig])
def get_models() -> list:
    return db.get_model_configs()


@router.put("/settings/models", response_model=List[ModelProviderConfig])
def put_models(configs: List[ModelProviderConfig]) -> list:
    return db.replace_model_configs([item.model_dump() for item in configs])

