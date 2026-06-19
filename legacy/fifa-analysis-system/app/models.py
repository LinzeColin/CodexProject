from typing import List, Optional

from pydantic import BaseModel, Field

from .constants import DISCLAIMER


class TeamIn(BaseModel):
    name: str
    country: Optional[str] = None
    team_type: str = "national"
    fifa_rank: Optional[int] = Field(default=None, ge=1)


class CompetitionIn(BaseModel):
    name: str
    season: Optional[str] = None
    region: Optional[str] = None


class MatchIn(BaseModel):
    competition_id: Optional[int] = None
    home_team_id: int
    away_team_id: int
    match_time: str
    venue: Optional[str] = None
    status: str = "scheduled"
    home_score: Optional[int] = None
    away_score: Optional[int] = None
    importance: int = Field(default=3, ge=1, le=5)


class TeamStatsIn(BaseModel):
    team_id: int
    matches_played: int = Field(default=0, ge=0)
    recent_points: int = Field(default=0, ge=0)
    recent_goals_for: float = Field(default=0, ge=0)
    recent_goals_against: float = Field(default=0, ge=0)
    home_win_rate: Optional[float] = Field(default=None, ge=0, le=1)
    away_win_rate: Optional[float] = Field(default=None, ge=0, le=1)
    injury_impact: float = Field(default=0, ge=0, le=1)
    fatigue_index: float = Field(default=0, ge=0, le=1)
    news_sentiment: float = Field(default=0, ge=-1, le=1)
    trend_score: float = Field(default=0, ge=-1, le=1)


class CrawlSourceIn(BaseModel):
    name: str
    base_url: str
    source_type: str = "public"
    terms_note: Optional[str] = None
    enabled: bool = True


class PredictionRequest(BaseModel):
    match_id: int


class BacktestRequest(BaseModel):
    model_version: Optional[str] = None


class ReportRequest(BaseModel):
    include_prediction: bool = True


class FactorOut(BaseModel):
    name: str
    source: str
    formula: str
    weight: float
    value: float
    effect: str


class PredictionOut(BaseModel):
    prediction_id: int
    match_id: int
    home_team: str
    away_team: str
    competition: Optional[str]
    match_time: str
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    recommended_result: str
    confidence_level: str
    key_factors: List[FactorOut]
    missing_data_warnings: List[str]
    model_version: str
    generated_at: str
    disclaimer: str
