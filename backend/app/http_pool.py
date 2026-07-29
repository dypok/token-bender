import httpx

_client: httpx.AsyncClient | None = None


async def init_pool():
    global _client
    _client = httpx.AsyncClient(
        timeout=httpx.Timeout(45.0, connect=5.0),
    )


async def close_pool():
    global _client
    if _client:
        await _client.aclose()
        _client = None


def get_http() -> httpx.AsyncClient:
    if _client is None:
        raise RuntimeError("HTTP pool not initialized")
    return _client
