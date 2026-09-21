"""Modelo de dados para regras do motor de triagem automática."""

from sqlmodel import Field, SQLModel

from app.models.enums import NivelAtendimento, PrioridadeChamado


class TriageRule(SQLModel, table=True):
    """Regra configurável de classificação/atribuição automática de chamados.

    Condições vazias (None) não restringem a regra nessa dimensão. Ações
    também são opcionais individualmente, mas pelo menos uma deve estar
    preenchida (validado na camada de service). Regras são avaliadas em
    ordem de execution_order (depois id); em caso de mais de uma regra
    alterando o mesmo campo, a última regra que casar prevalece.
    """

    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(max_length=150)
    is_active: bool = Field(default=True)
    execution_order: int = Field(default=0)

    condition_category_id: int | None = Field(default=None, foreign_key="category.id")
    condition_keyword: str | None = Field(default=None, max_length=100)
    condition_outside_business_hours: bool = Field(default=False)

    action_priority: PrioridadeChamado | None = Field(default=None)
    action_team_id: int | None = Field(default=None, foreign_key="team.id")
    action_level: NivelAtendimento | None = Field(default=None)