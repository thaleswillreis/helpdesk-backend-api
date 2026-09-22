"""Contratos de entrada/saída para itens do catálogo de serviços."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.enums import ApprovalTimeoutAction


class ServiceCatalogItemCreate(BaseModel):
    """Dados para criar um item do catálogo."""

    name: str = Field(max_length=150)
    description: str = Field(min_length=1)
    category_id: int
    subcategory_id: int | None = None
    requires_approval: bool = False
    auto_approve_if_vip: bool = False
    approval_timeout_hours: int | None = Field(default=None, gt=0)
    approval_timeout_action: ApprovalTimeoutAction | None = None

    @model_validator(mode="after")
    def _timeout_fields_together(self) -> "ServiceCatalogItemCreate":
        has_hours = self.approval_timeout_hours is not None
        has_action = self.approval_timeout_action is not None
        if has_hours != has_action:
            raise ValueError(
                "approval_timeout_hours e approval_timeout_action devem ser informados juntos."
            )
        return self


class ServiceCatalogItemUpdate(BaseModel):
    """Campos que podem ser atualizados em um item do catálogo."""

    name: str | None = Field(default=None, max_length=150)
    description: str | None = Field(default=None, min_length=1)
    category_id: int | None = None
    subcategory_id: int | None = None
    is_active: bool | None = None
    requires_approval: bool | None = None
    auto_approve_if_vip: bool | None = None
    approval_timeout_hours: int | None = Field(default=None, gt=0)
    approval_timeout_action: ApprovalTimeoutAction | None = None


class ServiceCatalogItemRead(BaseModel):
    """Dados públicos de um item do catálogo."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    category_id: int
    subcategory_id: int | None
    is_active: bool
    requires_approval: bool
    auto_approve_if_vip: bool
    approval_timeout_hours: int | None
    approval_timeout_action: ApprovalTimeoutAction | None
