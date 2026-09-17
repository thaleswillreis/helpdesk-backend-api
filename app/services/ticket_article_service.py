"""Regras de negócio para o vínculo entre chamados e artigos da base de conhecimento."""

import re
from sqlalchemy import column, func
from sqlmodel import Session, select

from app.core.roles import is_staff
from app.models.article import Article
from app.models.enums import ArticleStatus
from app.models.ticket import Ticket
from app.models.ticket_article import TicketArticle
from app.models.user import User
from app.services.article_service import search_articles



class TicketNotFoundError(Exception):
    """Levantado quando o chamado informado não existe ou não é visível ao usuário."""


class ArticleNotFoundError(Exception):
    """Levantado quando o artigo informado não existe."""


class DuplicateLinkError(Exception):
    """Levantado ao tentar vincular um artigo já vinculado ao mesmo chamado."""


class LinkNotFoundError(Exception):
    """Levantado quando o vínculo entre chamado e artigo não existe."""


class TicketNotYetResolvedError(Exception):
    """Levantado ao tentar marcar solução em chamado que nunca foi resolvido."""


def _check_ticket_visibility(session: Session, ticket_id: int, current_user: User) -> Ticket:
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise TicketNotFoundError("Chamado não encontrado.")
    if not is_staff(current_user) and ticket.requester_id != current_user.id:
        raise TicketNotFoundError("Chamado não encontrado.")
    return ticket


def link_article(
    session: Session, ticket_id: int, article_id: int, current_user: User
) -> TicketArticle:
    """Vincula um artigo a um chamado como referência geral (não marca como solução)."""
    _check_ticket_visibility(session, ticket_id, current_user)

    if session.get(Article, article_id) is None:
        raise ArticleNotFoundError("Artigo não encontrado.")

    existing = session.exec(
        select(TicketArticle).where(
            TicketArticle.ticket_id == ticket_id, TicketArticle.article_id == article_id
        )
    ).first()
    if existing is not None:
        raise DuplicateLinkError("Este artigo já está vinculado a este chamado.")

    link = TicketArticle(ticket_id=ticket_id, article_id=article_id, linked_by=current_user.id)
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def list_linked_articles(
    session: Session, ticket_id: int, current_user: User
) -> list[TicketArticle]:
    """Lista os artigos vinculados a um chamado, respeitando visibilidade de rascunho."""
    _check_ticket_visibility(session, ticket_id, current_user)

    query = select(TicketArticle).where(TicketArticle.ticket_id == ticket_id)
    links = list(session.exec(query))

    if is_staff(current_user):
        return links

    visible_links = []
    for link in links:
        article = session.get(Article, link.article_id)
        if article is not None and article.status == "published":
            visible_links.append(link)
    return visible_links


def set_resolution(
    session: Session, ticket_id: int, article_id: int, is_resolution: bool
) -> TicketArticle:
    """Marca (ou desmarca) um vínculo como a solução do chamado.

    Marcar como solução exige que o chamado já tenha sido resolvido em algum
    momento (resolved_at preenchido) — não precisa ser o status atual, pois o
    chamado pode já ter avançado para 'fechado'.
    """
    link = session.exec(
        select(TicketArticle).where(
            TicketArticle.ticket_id == ticket_id, TicketArticle.article_id == article_id
        )
    ).first()
    if link is None:
        raise LinkNotFoundError("Vínculo entre chamado e artigo não encontrado.")

    if is_resolution:
        ticket = session.get(Ticket, ticket_id)
        if ticket is None or ticket.resolved_at is None:
            raise TicketNotYetResolvedError(
                "O chamado precisa já ter sido resolvido para marcar um artigo como solução."
            )

        # Garante um único artigo de solução por chamado: desmarca os demais.
        other_links = session.exec(
            select(TicketArticle).where(
                TicketArticle.ticket_id == ticket_id,
                TicketArticle.is_resolution.is_(True),
                TicketArticle.id != link.id,
            )
        )
        for other in other_links:
            other.is_resolution = False
            session.add(other)

    link.is_resolution = is_resolution
    session.add(link)
    session.commit()
    session.refresh(link)
    return link


def unlink_article(session: Session, ticket_id: int, article_id: int) -> None:
    """Remove o vínculo entre um chamado e um artigo."""
    link = session.exec(
        select(TicketArticle).where(
            TicketArticle.ticket_id == ticket_id, TicketArticle.article_id == article_id
        )
    ).first()
    if link is None:
        raise LinkNotFoundError("Vínculo entre chamado e artigo não encontrado.")

    session.delete(link)
    session.commit()


def suggest_articles(
    session: Session, ticket_id: int, current_user: User, limit: int = 10
) -> list[Article]:
    """Sugere artigos publicados da mesma categoria do chamado.

    Usa OU lógico entre as palavras do título do chamado (não E, como na busca
    explícita da Tarefa 5.2) — para sugestão, uma única palavra relevante em
    comum já é um bom indício, exigir todas as palavras seria bem mais
    restritivo do que o esperado nesse contexto.
    """
    ticket = _check_ticket_visibility(session, ticket_id, current_user)

    words = [w for w in re.split(r"\W+", ticket.title) if len(w) >= 3]

    base_stmt = select(Article).where(
        Article.category_id == ticket.category_id, Article.status == ArticleStatus.PUBLISHED
    )

    if words:
        search_vector = column("search_vector")
        term_queries = [
            func.plainto_tsquery("simple", word).op("||")(func.plainto_tsquery("helpdesk_ptbr", word))
            for word in words
        ]
        combined_query = term_queries[0]
        for term_query in term_queries[1:]:
            combined_query = combined_query.op("||")(term_query)

        rank = func.ts_rank(search_vector, combined_query)
        ranked_stmt = (
            base_stmt.where(search_vector.op("@@")(combined_query))
            .order_by(rank.desc())
            .limit(limit)
        )
        results = list(session.exec(ranked_stmt))
        if results:
            return results

    # Sem palavras aproveitáveis no título, ou nenhuma bateu: cai para
    # qualquer artigo publicado da mesma categoria, ainda uma sugestão útil.
    fallback_stmt = base_stmt.limit(limit)
    return list(session.exec(fallback_stmt))