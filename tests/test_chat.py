from fastapi.testclient import TestClient
from main import app

def test_chat_empty_message_returns_400(client):
    resp = client.post("/chat", json={"message": "   "})
    assert resp.status_code == 400
    assert resp.json() == {"error": "Message cannot be empty"}

def test_chat_with_context_items(client, create_user_item, monkeypatch):
    # 1. Створюємо дані через фабрику
    create_user_item(email="yaroslav@gmail.com", title="Test Document 1")
    
    # 2. Мокаємо chain, щоб перевірити, чи передався контекст
    import main
    class SpyChain:
        def invoke(self, inputs):
            # Перевіряємо, що документ потрапив у контекст
            context = inputs.get("context_text", "")
            assert "Test Document 1" in context
            return {"answer": "I saw the document", "used_context": True}

    monkeypatch.setattr(main, "chain", SpyChain())

    # 3. Викликаємо чат
    resp = client.post("/chat", json={"message": "read my docs"})
    assert resp.status_code == 200
    assert resp.json()["answer"] == "I saw the document"

def test_chat_llm_failure_returns_502(client, monkeypatch):
    import main
    class FakeChain:
        def invoke(self, *args, **kwargs):
            raise RuntimeError("LLM Failure")

    monkeypatch.setattr(main, "chain", FakeChain())
    resp = client.post("/chat", json={"message": "hello"})
    assert resp.status_code == 502