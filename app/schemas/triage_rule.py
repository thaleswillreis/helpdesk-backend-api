"""Contratos de entrada/saída para regras do motor de triagem."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import NivelAtendimento, PrioridadeChamado


class TriageRuleCreate(BaseModel):
    """Dados para criar uma regra de triagem."""

    name: str = Field(max_length=150)
    is_active: bool = True
    execution_order: int = 0

    condition_category_id: int | None = None
    condition_keyword: str | None = Field(default=None, max_length=100)
    condition_outside_business_hours: bool = False

    action_priority: PrioridadeChamado | None = None
    action_team_id: int | None = None
    action_level: NivelAtendimento | None = None

    @model_validator(mode="after")
    def _at_least_one_action(self) -> "TriageRuleCreate":
        if not any([self.action_priority, self.action_team_id, self.action_level]):
            raise ValueError("A regra precisa definir pelo menos uma ação.")
        return self


class TriageRuleUpdate(BaseModel):
    """Campos que podem ser atualizados em uma regra de triagem existente."""

    name: str | None = Field(default=None, max_length=150)
    is_active: bool | None = None
    execution_order: int | None = None
    condition_category_id: int | None = None
    condition_keyword: str | None = Field(default=None, max_length=100)
    condition_outside_business_hours: bool | None = None
    action_priority: PrioridadeChamado | None = None
    action_team_id: int | None = None
    action_level: NivelAtendimento | None = None


class TriageRuleRead(BaseModel):
    """Dados públicos de uma regra de triagem."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool
    execution_order: int
    condition_category_id: int | None
    condition_keyword: str | None
    condition_outside_business_hours: bool
    action_priority: PrioridadeChamado | None
    action_team_id: int | None
    action_level: NivelAtendimento | None