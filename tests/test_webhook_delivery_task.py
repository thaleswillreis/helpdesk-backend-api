"""Testes da tarefa de entrega de webhook e da assinatura HMAC (Tarefa 7.2)."""

import hashlib
import hmac

from app.tasks.webhook_tasks import _sign_payload


def test_sign_payload_produces_expected_hmac_sha256() -> None:
    """A assinatura gerada deve ser um HMAC-SHA256 válido do corpo com o segredo."""
    secret = "minha-chave-secreta"
    body = b'{"event": "ticket.status_changed"}'

    expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    assert _sign_payload(secret, body) == expected


def test_sign_payload_differs_for_different_secrets() -> None:
    """Segredos diferentes devem produzir assinaturas diferentes para o mesmo corpo."""
    body = b'{"event": "ticket.assigned"}'

    signature_a = _sign_payload("secret-a", body)
    signature_b = _sign_payload("secret-b", body)

    assert signature_a != signature_b
