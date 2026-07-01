from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class ModuleType(str, Enum):
    dynamic = "dynamic"
    fault = "fault"
    gear = "gear"
    machining = "machining"
    other = "other"


class UserRole(str, Enum):
    admin = "admin"
    engineer = "engineer"
    viewer = "viewer"


class VisualizationSpec(BaseModel):
    id: str
    title: str
    kind: Literal["line", "bar", "gauge", "radar", "heatmap", "matrix", "timeline", "topology", "table"]
    description: str
    echarts_option: Dict[str, Any] = Field(default_factory=dict)
    data: Dict[str, Any] = Field(default_factory=dict)


class AnalysisResult(BaseModel):
    module: ModuleType
    title: str
    summary: str
    risk_level: Literal["normal", "warning", "critical"]
    risk_score: int = Field(ge=0, le=100)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    suggestions: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    visualizations: List[VisualizationSpec] = Field(default_factory=list)
    model_status: Dict[str, Any] = Field(default_factory=dict)


class CaseCreateRequest(BaseModel):
    module: ModuleType
    title: Optional[str] = None
    input_data: Dict[str, Any] = Field(default_factory=dict)
    uploaded_file_name: Optional[str] = None
    uploaded_rows: List[Dict[str, Any]] = Field(default_factory=list)
    role: UserRole = UserRole.engineer
    auto_generate_report: bool = True


class AnalysisCase(BaseModel):
    id: int
    module: ModuleType
    title: str
    input_data: Dict[str, Any]
    uploaded_file_name: Optional[str] = None
    result: AnalysisResult
    report_path: Optional[str] = None
    report_status: Literal["pending", "ready", "failed"] = "pending"
    created_at: str
    updated_at: str


class ReportArtifact(BaseModel):
    case_id: int
    path: str
    status: Literal["ready", "failed"]
    message: str


class ModelProviderConfig(BaseModel):
    provider: str
    base_url: str = ""
    model: str = ""
    api_key: str = ""
    enabled: bool = False
    priority: int = 100


class DashboardSummary(BaseModel):
    total_cases: int
    report_count: int
    risk_distribution: Dict[str, int]
    module_distribution: Dict[str, int]
    recent_cases: List[Dict[str, Any]]
    model_health: List[Dict[str, Any]]
    kpis: Dict[str, Any]

