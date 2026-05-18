from pydantic import BaseModel
from typing import List


class RiskDistribution(BaseModel):
    high: int
    medium: int
    low: int
    total: int


class InterventionStats(BaseModel):
    pending: int
    in_progress: int
    completed: int
    dismissed: int


class DashboardSummary(BaseModel):
    risk_distribution: RiskDistribution
    intervention_stats: InterventionStats
    total_students: int
    high_risk_percentage: float


class WeekTrend(BaseModel):
    week_number: int
    avg_risk_score: float
    high_risk_count: int
    medium_risk_count: int
    low_risk_count: int


class DashboardTrends(BaseModel):
    weeks: List[WeekTrend]
