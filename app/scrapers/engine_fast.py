import httpx
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.scrapers.middleware import AsyncRateLimiter, get_browser_headers
from app.config import settings

class FastEngine:
    """High-throughput async HTTP client for reverse-engineered REST/JSON/GraphQL endpoints."""

    def __init__(self, rate_limit_rps: float = 3.0, timeout: int = settings.SCRAPER_REQUEST_TIMEOUT):
        self.rate_limiter = AsyncRateLimiter(requests_per_second=rate_limit_rps)
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                http2=True,
                timeout=httpx.Timeout(self.timeout, connect=10.0),
                follow_redirects=True,
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._client

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def get_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        await self.rate_limiter.acquire()
        client = await self.get_client()

        req_headers = get_browser_headers()
        if headers:
            req_headers.update(headers)

        response = await client.get(url, params=params, headers=req_headers, cookies=cookies)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def post_json(
        self,
        url: str,
        json_data: Dict[str, Any],
        headers: Optional[Dict[str, str]] = None,
        cookies: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        await self.rate_limiter.acquire()
        client = await self.get_client()

        req_headers = get_browser_headers()
        if headers:
            req_headers.update(headers)

        response = await client.post(url, json=json_data, headers=req_headers, cookies=cookies)
        response.raise_for_status()
        return response.json()

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, httpx.HTTPStatusError)),
        reraise=True,
    )
    async def get_html(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> str:
        await self.rate_limiter.acquire()
        client = await self.get_client()

        req_headers = get_browser_headers()
        req_headers["Accept"] = "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        if headers:
            req_headers.update(headers)

        response = await client.get(url, params=params, headers=req_headers)
        response.raise_for_status()
        return response.text

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()
