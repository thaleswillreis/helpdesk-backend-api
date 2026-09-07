"""Testes do histórico de alterações de chamados (Tarefa 2.4)."""

from fastapi.testclient import TestClient


def _ticket_payload(category_id: int, **overrides) -> dict:
    payload = {
        "title": "Impressora não imprime",
        "description": "Fila travada no setor financeiro.",
        "category_id": category_id,
    }
    payload.update(overrides)
    return payload


def test_status_change_creates_history_entry(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Alterar o status deve criar uma entrada no histórico."""
    make_user("tec_hist1@example.com", "senha-forte-123", "tecnico")
    make_user("solic_hist1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede")

    headers_solic = auth_headers("solic_hist1@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_hist1@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(category.id), headers=headers_solic).json()
    client.patch(
        f"/tickets/{created['id']}",
        json={"status": "em_atendimento", "comment": "Iniciando análise."},
        headers=headers_tec,
    )

    response = client.get(f"/tickets/{created['id']}/history", headers=headers_tec)

    assert response.status_code == 200
    events = response.json()
    assert len(events) == 1
    assert events[0]["field_name"] == "status"
    assert events[0]["old_value"] == "aberto"
    assert events[0]["new_value"] == "em_atendimento"
    assert events[0]["comment"] == "Iniciando análise."


def test_multiple_field_changes_create_multiple_entries(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Alterar vários campos no mesmo PATCH deve gerar uma entrada por campo."""
    tecnico = make_user("tec_hist2@example.com", "senha-forte-123", "tecnico")
    make_user("solic_hist2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Software")

    headers_solic = auth_headers("solic_hist2@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_hist2@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(category.id), headers=headers_solic).json()
    client.patch(
        f"/tickets/{created['id']}",
        json={"status": "em_atendimento", "assigned_to": tecnico.id},
        headers=headers_tec,
    )

    response = client.get(f"/tickets/{created['id']}/history", headers=headers_tec)

    fields_changed = {event["field_name"] for event in response.json()}
    assert fields_changed == {"status", "assigned_to"}


def test_no_op_update_does_not_create_history_entry(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Reenviar o mesmo valor de um campo não deve gerar entrada de histórico."""
    make_user("tec_hist3@example.com", "senha-forte-123", "tecnico")
    make_user("solic_hist3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Hardware")

    headers_solic = auth_headers("solic_hist3@example.com", "senha-forte-123")
    headers_tec = auth_headers("tec_hist3@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(category.id), headers=headers_solic).json()
    client.patch(f"/tickets/{created['id']}", json={"status": "aberto"}, headers=headers_tec)

    response = client.get(f"/tickets/{created['id']}/history", headers=headers_tec)

    assert response.json() == []


def test_solicitante_cannot_see_others_ticket_history(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Um solicitante não pode ver o histórico de chamado de outro usuário."""
    make_user("solic_hist4@example.com", "senha-forte-123", "solicitante")
    make_user("solic_hist5@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede 2")

    headers_a = auth_headers("solic_hist4@example.com", "senha-forte-123")
    headers_b = auth_headers("solic_hist5@example.com", "senha-forte-123")

    created = client.post("/tickets", json=_ticket_payload(category.id), headers=headers_a).json()

    response = client.get(f"/tickets/{created['id']}/history", headers=headers_b)

    assert response.status_code == 404