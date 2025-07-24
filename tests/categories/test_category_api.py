import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from fastapi.testclient import TestClient
from app.main import app
client = TestClient(app)

def test_categories_endpoint_protection():
    response = client.get("/categories/")
    assert response.status_code in [401, 403]

def test_categories_by_id_protection():
    response = client.get("/categories/test-uuid")
    assert response.status_code in [401, 403]

def test_categories_add_protection():
    response = client.post("/categories/add/", json={})
    assert response.status_code in [401, 403]

def test_categories_update_protection():
    response = client.put("/categories/update/test-uuid", json={})
    assert response.status_code in [401, 403]

def test_categories_delete_protection():
    response = client.delete("/categories/delete/test-uuid")
    assert response.status_code in [401, 403] 