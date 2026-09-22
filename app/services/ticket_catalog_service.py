"""Regras de negócio para abertura de chamados via catálogo de serviços."""

from sqlmodel import Session, select

from app.models.catalog_item_field import CatalogItemField
from app.models.enums import CatalogFieldType, StatusChamado
from app.models.service_catalog_item import ServiceCatalogItem
from app.models.ticket import Ticket
from app.models.ticket_catalog_answer import TicketCatalogAnswer
from app.models.user import User
from app.schemas.ticket import TicketCreate
from app.schemas.ticket_catalog import TicketFromCatalogCreate
from app.services.ticket_service import create_ticket
from app.services.system_user_service import get_system_user
from app.services.ticket_approval_service import approve_ticket


class CatalogItemNotFoundError(Exception):
    """Levantado quando o item de catálogo informado não existe ou está inativo."""


class MissingRequiredAnswerError(Exception):
    """Levantado quando um campo obrigatório não foi respondido."""


class InvalidAnswerValueError(Exception):
    """Levantado quando uma resposta não é compatível com o tipo do campo."""


class UnknownFieldError(Exception):
    """Levantado quando uma resposta referencia um campo que não pertence ao item."""


def _validate_answers(fields: list[CatalogItemField], answers: list) -> dict[int, str]:
    """Valida as respostas contra os campos configurados e retorna um mapa field_id -> value."""
    fields_by_id = {f.id: f for f in fields}
    answers_by_field = {a.field_id: a.value for a in answers}

    for field_id in answers_by_field:
        if field_id not in fields_by_id:
            raise UnknownFieldError(
                f"Campo (id={field_id}) não pertence a este item de catálogo."
            )

    for field in fields:
        value = answers_by_field.get(field.id)

        if field.is_required and (value is None or value.strip() == ""):
            raise MissingRequiredAnswerError(f"O campo '{field.label}' é obrigatório.")

        if value is None or value.strip() == "":
            continue

        if field.field_type == CatalogFieldType.NUMBER:
            try:
                float(value)
            except ValueError as exc:
                raise InvalidAnswerValueError(
                    f"O campo '{field.label}' precisa ser um número."
                ) from exc

        if field.field_type == CatalogFieldType.SELECT:
            if not field.options or value not in field.options:
                raise InvalidAnswerValueError(
                    f"O campo '{field.label}' precisa ser um dos valores: "
                    f"{', '.join(field.options or [])}."
                )

    return answers_by_field


def create_ticket_from_catalog(
    session: Session, data: TicketFromCatalogCreate, current_user: User
) -> Ticket:
    """Abre um chamado a partir de um item do catálogo, validando e registrando as respostas."""
    item = session.get(ServiceCatalogItem, data.catalog_item_id)
    if item is None or not item.is_active:
        raise CatalogItemNotFoundError("Item de catálogo não encontrado ou inativo.")

    fields = list(
        session.exec(
            select(CatalogItemField).where(CatalogItemField.catalog_item_id == item.id)
        )
    )
    answers_by_field = _validate_answers(fields, data.answers)

    ticket_data = TicketCreate(
        title=item.name,
        description=item.description,
        category_id=item.category_id,
        subcategory_id=item.subcategory_id,
        priority=data.priority,
        requester_id=data.requester_id,
    )
    ticket = create_ticket(session, ticket_data, current_user)

    ticket.catalog_item_id = item.id
    if item.requires_approval:
        ticket.status = StatusChamado.AGUARDANDO_APROVACAO
    session.add(ticket)

    for field_id, value in answers_by_field.items():
        session.add(
            TicketCatalogAnswer(ticket_id=ticket.id, field_id=field_id, value=value)
        )

    session.commit()
    session.refresh(ticket)

    if item.requires_approval and item.auto_approve_if_vip:
        requester = session.get(User, ticket.requester_id)
        if requester is not None and requester.is_vip:
            system_user = get_system_user(session)
            ticket = approve_ticket(
                session,
                ticket.id,
                True,
                "Aprovação automática: solicitante VIP.",
                system_user,
            )

    return ticket


def get_catalog_answers(session: Session, ticket_id: int) -> list[dict]:
    """Retorna as respostas do formulário de um chamado, com o rótulo de cada campo."""
    query = (
        select(TicketCatalogAnswer, CatalogItemField)
        .join(CatalogItemField, TicketCatalogAnswer.field_id == CatalogItemField.id)
        .where(TicketCatalogAnswer.ticket_id == ticket_id)
    )

    return [
        {"field_id": field.id, "label": field.label, "value": answer.value}
        for answer, field in session.exec(query)
    ]
