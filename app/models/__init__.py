"""Pacote de modelos SQLModel do domínio.

Importar este pacote garante que TODAS as tabelas sejam registradas no
metadata do SQLModel — necessário tanto para o Alembic (autogenerate)
quanto para `SQLModel.metadata.create_all()` nos testes, independente
de existir alguma rota/serviço usando o modelo diretamente.
"""

from app.models.role import Role  # noqa: F401
from app.models.ticket import Ticket  # noqa: F401
from app.models.user import User  # noqa: F401