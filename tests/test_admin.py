import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from main import app
from database import get_db
import models

client = TestClient(app)

def test_admin_get_users():
    response = client.get("/admin/users")
    assert response.status_code == 200
    assert type(response.json()) == list

def test_admin_templates():
    tpl_res = client.post("/admin/templates", json={"type": "SMS", "body": "test"})
    assert tpl_res.status_code == 200
    tpl_id = tpl_res.json()["id"]

    get_res = client.get("/admin/templates")
    assert get_res.status_code == 200

    put_res = client.put(f"/admin/templates/{tpl_id}", json={"type": "SMS", "body": "updated"})
    assert put_res.status_code == 200

    del_res = client.delete(f"/admin/templates/{tpl_id}")
    assert del_res.status_code == 200
