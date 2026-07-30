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
    global _client
    if _client is None or _client.is_closed:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(45.0, connect=5.0))
    return _client
