"""Tests use a temporary database, never the class dataset."""
import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app({"TESTING": True, "DATABASE": str(tmp_path / "test.sqlite3")})
    return app.test_client()


def test_health(client):
    assert client.get("/api/v1/salud").json == {"estado": "ok"}


def test_crud(client):
    response = client.post("/api/v1/prestamos", json={"id": "DEMO-001", "edad": 30, "monto_inicial": 15000, "impago": 0})
    assert response.status_code == 201
    assert client.get("/api/v1/prestamos/DEMO-001").json["edad"] == 30
    assert len(client.get("/api/v1/prestamos?limit=10").json["datos"]) == 1
    assert client.get("/api/v1/estadisticas").json["total_prestamos"] == 1
    assert client.post("/api/v1/prestamos", json={"id": "DEMO-001"}).status_code == 409


def test_validation(client):
    assert client.post("/api/v1/prestamos", json={"edad": 18}).status_code == 400
    assert client.get("/api/v1/prestamos?limit=500").status_code == 400
    assert client.get("/api/v1/prestamos/inexistente").status_code == 404


def test_currency_same(client):
    assert client.get("/api/v1/tipos-cambio?base=EUR&destino=EUR").json["tipo_cambio"] == 1.0
