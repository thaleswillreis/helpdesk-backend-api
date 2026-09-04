"""Testes de modelagem do Ticket (Tarefa 2.1)."""

from sqlmodel import Session

from app.core.security import hash_password
from app.models.enums import PrioridadeChamado, StatusChamado
from app.models.ticket import Ticket
from app.models.user import User


def _create_user(session: Session, email: str) -> User:
    user = User(name="Usuário Teste", email=email, hashed_password=hash_password("senha123456"))
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def test_ticket_created_with_default_status_aberto(session: Session) -> None:
    """Um ticket novo deve nascer com status 'aberto' por padrão e sem técnico atribuído."""
    requester = _create_user(session, "solicitante_ticket@example.com")

    ticket = Ticket(
        title="Impressora não imprime",
        description="Fila de impressão travada no setor financeiro.",
        priority=PrioridadeChamado.MEDIA,
        category="Hardware",
        requester_id=requester.id,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    assert ticket.status == StatusChamado.ABERTO
    assert ticket.assigned_to is None
    assert ticket.id is not None


def test_ticket_priority_vip_is_stored_correctly(session: Session) -> None:
    """A prioridade VIP deve ser persistida e recuperada corretamente."""
    requester = _create_user(session, "solicitante_vip@example.com")

    ticket = Ticket(
        title="Notebook do diretor não liga",
        description="Usuário VIP sem acesso ao notebook.",
        priority=PrioridadeChamado.VIP,
        status=StatusChamado.EM_ATENDIMENTO,
        category="Hardware",
        requester_id=requester.id,
    )
    session.add(ticket)
    session.commit()
    session.refresh(ticket)

    assert ticket.priority == PrioridadeChamado.VIP