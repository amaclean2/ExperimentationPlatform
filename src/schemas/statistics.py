from pydantic import BaseModel, Field
from typing import Optional, List


class ConfidenceInterval(BaseModel):
    lower: float = Field(..., description="Lower bound of confidence interval (%)")
    upper: float = Field(..., description="Upper bound of confidence interval (%)")


class VariantResult(BaseModel):
    variant_id: int
    variant_name: str
    conversions: int
    total_users: int
    conversion_rate: float = Field(..., description="Conversion rate as percentage")
    confidence_interval: Optional[ConfidenceInterval] = None
    p_value: Optional[float] = Field(None, description="P-value from statistical test (comparison to control)")
    is_significant: Optional[bool] = Field(None, description="Whether result is statistically significant")
    relative_uplift: Optional[float] = Field(None, description="Percentage uplift compared to control")
    is_control: bool = Field(default=False, description="Whether this is the control variant")


class Winner(BaseModel):
    variant_id: int
    variant_name: str
    relative_uplift: float


class ExperimentStatisticsResponse(BaseModel):
    experiment_id: int
    experiment_name: str
    conversion_event_type: str
    confidence_level: float
    significance_threshold: float
    variants: List[VariantResult]
    winner: Optional[Winner] = None


class StatisticsRequest(BaseModel):
    conversion_event_type: str = Field(
        default="conversion",
        description="Event type to use for conversion counting"
    )
    confidence_level: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
        description="Confidence level for interval calculations (0.0-1.0)"
    )
    significance_threshold: float = Field(
        default=0.05,
        ge=0.0,
        le=1.0,
        description="P-value threshold for statistical significance (0.0-1.0)"
    )
