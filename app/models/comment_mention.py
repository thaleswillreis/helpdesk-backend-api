"""Modelo de dados para menções a usuários dentro de um comentário."""

from sqlmodel import Field, SQLModel


class CommentMention(SQLModel, table=True):
    """Vínculo de um usuário mencionado em um comentário."""

    comment_id: int = Field(foreign_key="ticketcomment.id", primary_key=True)
    mentioned_user_id: int = Field(foreign_key="user.id", primary_key=True)