"""Pydantic v2 request/response schemas — field ranges match the pandera source schema."""
from pydantic import BaseModel, Field


class SensorReading(BaseModel):
    air_temp: float = Field(..., ge=295.0, le=310.0, description="Air temperature (K)")
    process_temp: float = Field(..., ge=305.0, le=315.0, description="Process temperature (K)")
    rotational_speed: int = Field(..., ge=1100, le=3000, description="Rotational speed (rpm)")
    torque: float = Field(..., ge=3.0, le=80.0, description="Torque (Nm)")
    tool_wear: int = Field(..., ge=0, le=260, description="Tool wear (min)")
    product_type: str = Field(default="M", pattern="^[LMH]$", description="Quality class: L, M, or H")

    model_config = {
        "json_schema_extra": {
            "example": {
                "air_temp": 298.1,
                "process_temp": 308.6,
                "rotational_speed": 1551,
                "torque": 42.8,
                "tool_wear": 0,
                "product_type": "M",
            }
        }
    }


class PredictionResponse(BaseModel):
    prediction_id: int
    failure_probability: float
    predicted_failure: bool
    failure_modes: dict[str, float]
    model_version: str


class MetricsResponse(BaseModel):
    auc: float
    precision: float
    recall: float
    f1: float
    total_predictions: int
    failure_rate_30d: float
    model_version: str
