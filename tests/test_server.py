from fastapi.testclient import TestClient

from tag_sensor.server.application import app


def test_read_main():
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "<title>Tag Sensor</title>" in response.text
        # assert response.json() == {"msg": "Hello World"}
