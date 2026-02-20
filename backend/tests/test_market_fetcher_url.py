# backend/tests/test_market_fetcher_url.py
from types import SimpleNamespace

def test_agmarknet_http_fetcher_uses_resource_id_and_key(monkeypatch):
    # Arrange env: set a fake API key
    monkeypatch.setenv("KM_DATA_GOV_IN_API_KEY", "TEST_KEY")

    # Import after env set so settings pick it up
    from backend.app.services import market as m

    captured = {}

    class FakeResponse:
        def raise_for_status(self):  # no-op
            return None
        def json(self):
            return {"records": []}

    class FakeClient:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def get(self, url, params=None):
            captured["url"] = url
            captured["params"] = dict(params or {})
            return FakeResponse()

    # Monkeypatch httpx.Client to our fake
    import httpx
    monkeypatch.setattr(httpx, "Client", FakeClient)

    # Act
    out = m.agmarknet_http_fetcher("Kolkata")

    # Assert: correct URL & params
    assert out == []
    assert captured["url"].endswith("/" + m.RESOURCE_ID)
    assert captured["params"]["api-key"] == "TEST_KEY"
    assert captured["params"]["format"] == "json"
    assert captured["params"]["filters[district]"] == "Kolkata"
