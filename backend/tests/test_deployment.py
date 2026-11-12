"""Deployment URL and same-origin routing checks."""

from fastapi.testclient import TestClient
import pytest

from app.core.config import Settings


@pytest.mark.parametrize("url", [
    "postgres://user:pass@db:5432/orders",
    "postgresql://user:pass@db:5432/orders",
    "postgresql+psycopg://user:pass@db:5432/orders",
])
def test_database_url_uses_psycopg(url: str) -> None:
    settings = Settings(_env_file=None, database_url=url)
    assert settings.database_url == "postgresql+psycopg://user:pass@db:5432/orders"


def test_spa_fallback_preserves_api_and_docs(tmp_path, monkeypatch) -> None:
    import app.main as main

    app_dir = tmp_path / "app"
    app_dir.mkdir()
    dist = tmp_path / "frontend_dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text("<html>test frontend</html>")
    (dist / "assets" / "app.js").write_text("test asset")
    monkeypatch.setattr(main, "__file__", str(app_dir / "main.py"))
    with TestClient(main.create_app()) as client:
        assert "test frontend" in client.get("/orders/123").text
        assert client.get("/assets/app.js").text == "test asset"
        assert client.get("/assets/missing.js").status_code == 404
        assert client.get("/api/missing").status_code == 404
        assert client.get("/health").status_code == 200
        assert client.get("/docs").status_code == 200
