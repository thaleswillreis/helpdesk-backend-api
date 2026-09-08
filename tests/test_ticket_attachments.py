"""Testes de anexos de chamados (Tarefa 3.4). Requer MinIO ativo (docker compose up minio minio-init)."""

from fastapi.testclient import TestClient


def test_upload_valid_attachment(client: TestClient, make_user, make_category, auth_headers) -> None:
    """Um upload de arquivo permitido deve ser aceito e retornar metadados."""
    make_user("solic_att1@example.com", "senha-forte-123", "solicitante")
    category = make_category("Hardware Att")
    headers = auth_headers("solic_att1@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/attachments",
        files={"file": ("print.png", b"fake-image-bytes", "image/png")},
        headers=headers,
    )

    assert response.status_code == 201
    assert response.json()["original_filename"] == "print.png"


def test_upload_with_disallowed_extension_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Upload de extensão não permitida deve ser rejeitado."""
    make_user("solic_att2@example.com", "senha-forte-123", "solicitante")
    category = make_category("Software Att")
    headers = auth_headers("solic_att2@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    response = client.post(
        f"/tickets/{ticket['id']}/attachments",
        files={"file": ("script.exe", b"conteudo", "application/octet-stream")},
        headers=headers,
    )

    assert response.status_code == 422


def test_upload_exceeding_size_limit_returns_422(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Upload maior que o limite configurado deve ser rejeitado."""
    make_user("solic_att3@example.com", "senha-forte-123", "solicitante")
    category = make_category("Rede Att")
    headers = auth_headers("solic_att3@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    oversized_content = b"0" * (11 * 1024 * 1024)  # 11 MB > limite de 10 MB
    response = client.post(
        f"/tickets/{ticket['id']}/attachments",
        files={"file": ("grande.pdf", oversized_content, "application/pdf")},
        headers=headers,
    )

    assert response.status_code == 422


def test_download_url_is_generated_for_existing_attachment(
    client: TestClient, make_user, make_category, auth_headers
) -> None:
    """Deve ser possível gerar uma URL de download para um anexo existente."""
    make_user("solic_att4@example.com", "senha-forte-123", "solicitante")
    category = make_category("Sistemas Att")
    headers = auth_headers("solic_att4@example.com", "senha-forte-123")

    ticket = client.post(
        "/tickets",
        json={"title": "T", "description": "D", "category_id": category.id},
        headers=headers,
    ).json()

    uploaded = client.post(
        f"/tickets/{ticket['id']}/attachments",
        files={"file": ("doc.pdf", b"conteudo-pdf", "application/pdf")},
        headers=headers,
    ).json()

    response = client.get(
        f"/tickets/{ticket['id']}/attachments/{uploaded['id']}/download", headers=headers
    )

    assert response.status_code == 200
    assert "download_url" in response.json()
    assert response.json()["download_url"].startswith("http")