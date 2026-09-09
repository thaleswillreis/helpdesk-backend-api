"""Pacote de modelos SQLModel do domínio.

Importar este pacote garante que TODAS as tabelas sejam registradas no
metadata do SQLModel — necessário tanto para o Alembic (autogenerate)
quanto para `SQLModel.metadata.create_all()` nos testes, independente
de existir alguma rota/serviço usando o modelo diretamente.
"""

from app.models.category import Category  # noqa: F401
from app.models.comment_mention import CommentMention  # noqa: F401
from app.models.role import Role  # noqa: F401
from app.models.sla_policy import SLAPolicy  # noqa: F401
from app.models.subcategory import Subcategory  # noqa: F401
from app.models.system_settings import SystemSettings  # noqa: F401
from app.models.team import Team  # noqa: F401
from app.models.team_membership import TeamMembership  # noqa: F401
from app.models.team_schedule import TeamSchedule  # noqa: F401
from app.models.ticket import Ticket  # noqa: F401
from app.models.ticket_attachment import TicketAttachment  # noqa: F401
from app.models.ticket_comment import TicketComment  # noqa: F401
from app.models.ticket_history import TicketHistory  # noqa: F401
from app.models.user import User  # noqa: F401