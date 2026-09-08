"""Regras de negócio para comentários e menções em chamados."""

from sqlmodel import Session, select

from app.core.roles import is_staff
from app.models.comment_mention import CommentMention
from app.models.ticket import Ticket
from app.models.ticket_comment import TicketComment
from app.models.user import User
from app.schemas.ticket_comment import TicketCommentCreate


class TicketNotFoundError(Exception):
    """Levantado quando o chamado informado não existe ou não é visível ao usuário."""


class ForbiddenInternalCommentError(Exception):
    """Levantado quando um solicitante tenta criar um comentário interno."""


class InvalidMentionError(Exception):
    """Levantado quando um usuário mencionado não existe ou está inativo."""


def _check_ticket_visibility(session: Session, ticket_id: int, current_user: User) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")
    if not is_staff(current_user) and ticket.requester_id != current_user.id:
        raise TicketNotFoundError("Chamado não encontrado.")
    return ticket


def create_comment(
    session: Session, ticket_id: int, data: TicketCommentCreate, current_user: User
) -> tuple[TicketComment, list[int]]:
    """Cria um comentário no chamado, validando permissão e menções."""
    _check_ticket_visibility(session, ticket_id, current_user)

    if data.is_internal and not is_staff(current_user):
        raise ForbiddenInternalCommentError(
            "Somente admin/tecnico pode criar comentários internos."
        )

    for user_id in data.mentioned_user_ids:
        mentioned = session.get(User, user_id)
        if mentioned is None or not mentioned.is_active:
            raise InvalidMentionError(
                f"Usuário mencionado (id={user_id}) não encontrado ou inativo."
            )

    comment = TicketComment(
        ticket_id=ticket_id,
        author_id=current_user.id,
        content=data.content,
        is_internal=data.is_internal,
    )
    session.add(comment)
    session.commit()
    session.refresh(comment)

    for user_id in data.mentioned_user_ids:
        session.add(CommentMention(comment_id=comment.id, mentioned_user_id=user_id))
    session.commit()

    return comment, data.mentioned_user_ids


def list_comments(session: Session, ticket_id: int, current_user: User) -> list[dict]:
    """Lista comentários visíveis ao usuário, com as menções de cada um."""
    _check_ticket_visibility(session, ticket_id, current_user)

    query = select(TicketComment).where(TicketComment.ticket_id == ticket_id)
    if not is_staff(current_user):
        query = query.where(TicketComment.is_internal.is_(False))
    query = query.order_by(TicketComment.created_at)

    comments = list(session.exec(query))

    result = []
    for comment in comments:
        mention_query = select(CommentMention.mentioned_user_id).where(
            CommentMention.comment_id == comment.id
        )
        mentioned_ids = list(session.exec(mention_query))
        result.append(
            {
                "id": comment.id,
                "ticket_id": comment.ticket_id,
                "author_id": comment.author_id,
                "content": comment.content,
                "is_internal": comment.is_internal,
                "created_at": comment.created_at,
                "mentioned_user_ids": mentioned_ids,
            }
        )

    return result