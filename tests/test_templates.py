import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from fastapi.testclient import TestClient
from main import app, get_template
from database import get_db
import models

client = TestClient(app)

def test_get_template_logic():
    db = next(get_db())
    # Create test template
    tpl = models.Template(type="test_tpl", title="Hello {{name}}", body="Your code is {{code}}", placeholders=["name", "code"])
    db.add(tpl)
    db.commit()

    title, body = get_template(db, "test_tpl", "Fallback Title", "Fallback Body", name="Alice", code="1234")

    assert title == "Hello Alice"
    assert body == "Your code is 1234"

    db.delete(tpl)
    db.commit()
