from pydantic import BaseModel, Field, field_validator, model_validator

from app.schemas.enums import Agregator, NodeType
from app.schemas.patterns import NEO4J_ID_PATTERN
from app.schemas.validators import validate_max_level


class ConfigByImpactRequest(BaseModel):
    requirement_file_id: str = Field(
        pattern=NEO4J_ID_PATTERN
    )
    max_level: int = Field(...)
    impact: float = Field(
        ge=0,
        le=10
    )
    node_type: NodeType
    agregator: Agregator

    @field_validator("max_level")
    def validate_max_level(cls, value):
        return validate_max_level(value)

    @model_validator(mode='before')
    def set_max_level_to_square(cls, values):
        if values.get('max_level') != -1:
            values['max_level'] = values.get('max_level', 1) * 2
        return values
