"""Motor de regras de triagem automática (classificação/atribuição de chamados)."""

from datetime import UTC, datetime

from sqlmodel import Session, select

from app.models.category import Category
from app.models.team import Team
from app.models.team_schedule import TeamSchedule
from app.models.ticket import Ticket
from app.models.triage_rule import TriageRule
from app.schemas.triage_rule import TriageRuleCreate, TriageRuleUpdate
from app.services.business_time import expand_schedule, is_within_business_hours


class TriageRuleNotFoundError(Exception):
    """Levantado quando a regra de triagem informada não existe."""


class CategoryNotFoundError(Exception):
    """Levantado quando a categoria informada na condição não existe."""


class TeamNotFoundError(Exception):
    """Levantado quando a equipe informada na ação não existe."""


def _validate_references(
    session: Session, category_id: int | None, team_id: int | None
) -> None:
    if category_id is not None and session.get(Category, category_id) is None:
        raise CategoryNotFoundError("Categoria informada na condição não encontrada.")
    if team_id is not None and session.get(Team, team_id) is None:
        raise TeamNotFoundError("Equipe informada na ação não encontrada.")


def create_rule(session: Session, data: TriageRuleCreate) -> TriageRule:
    """Cria uma regra de triagem."""
    _validate_references(session, data.condition_category_id, data.action_team_id)

    rule = TriageRule(**data.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def list_rules(session: Session) -> list[TriageRule]:
    """Lista todas as regras de triagem, ordenadas pela ordem de execução."""
    query = select(TriageRule).order_by(TriageRule.execution_order, TriageRule.id)
    return list(session.exec(query))


def update_rule(session: Session, rule_id: int, data: TriageRuleUpdate) -> TriageRule:
    """Atualiza uma regra de triagem existente."""
    rule = session.get(TriageRule, rule_id)
    if rule is None:
        raise TriageRuleNotFoundError("Regra de triagem não encontrada.")

    update_data = data.model_dump(exclude_unset=True)
    final_category_id = update_data.get("condition_category_id", rule.condition_category_id)
    final_team_id = update_data.get("action_team_id", rule.action_team_id)
    if "condition_category_id" in update_data or "action_team_id" in update_data:
        _validate_references(session, final_category_id, final_team_id)

    for field, value in update_data.items():
        setattr(rule, field, value)

    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


def delete_rule(session: Session, rule_id: int) -> None:
    """Remove uma regra de triagem."""
    rule = session.get(TriageRule, rule_id)
    if rule is None:
        raise TriageRuleNotFoundError("Regra de triagem não encontrada.")

    session.delete(rule)
    session.commit()


def _keyword_matches(rule: TriageRule, ticket: Ticket) -> bool:
    keyword = rule.condition_keyword.lower()
    return keyword in ticket.title.lower() or keyword in ticket.description.lower()


def _outside_hours_matches(session: Session, ticket: Ticket) -> bool:
    if ticket.team_id is None:
        return False

    schedule = list(
        session.exec(select(TeamSchedule).where(TeamSchedule.team_id == ticket.team_id))
    )
    windows = expand_schedule(schedule)
    now = datetime.now(UTC)
    return not is_within_business_hours(now, windows)


def apply_triage_rules(session: Session, ticket: Ticket) -> None:
    """Avalia as regras ativas e aplica as ações das que casarem, em ordem.

    Muta `ticket` em memória (não comita); o chamador é responsável por
    persistir. Quando mais de uma regra altera o mesmo campo, a última regra
    que casar prevalece (ordem de execution_order, depois id).
    """
    rules = list_rules(session)

    for rule in rules:
        if not rule.is_active:
            continue

        if rule.condition_category_id is not None and rule.condition_category_id != ticket.category_id:
            continue
        if rule.condition_keyword and not _keyword_matches(rule, ticket):
            continue
        if rule.condition_outside_business_hours and not _outside_hours_matches(session, ticket):
            continue

        if rule.action_priority is not None:
            ticket.priority = rule.action_priority
        if rule.action_team_id is not None:
            ticket.team_id = rule.action_team_id
        if rule.action_level is not None:
            ticket.current_level = rule.action_level