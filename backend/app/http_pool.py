import httpx

_client: httpx.AsyncClient | None = None


async def init_pool():
    global _client
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(60.0, connect=5.0),
    )


async def close_pool():
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_http() -> httpx.AsyncClient:
    assert _client is not None, "HTTP pool not initialized"
    return _client
