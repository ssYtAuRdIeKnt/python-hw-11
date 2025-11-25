import os
import pytest
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import Session

# Set fake DB URL before imports
os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

from fastapi.testclient import TestClient
from main import app
import db

db.engine = db.create_engine(
    os.environ["DATABASE_URL"],
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

@pytest.fixture(scope="function")
def client():
    db.Base.metadata.create_all(bind=db.engine)
    with TestClient(app) as c:
        yield c
    db.Base.metadata.drop_all(bind=db.engine)

@pytest.fixture
def create_user_item():
    def _create(email: str, title: str):
        with Session(db.engine) as session:
            item = db.UserItem(user_email=email, title=title)
            session.add(item)
            session.commit()
            return item
    return _create