"""Polite HTTP client for dataset downloads: honest User-Agent, delay, retries with backoff."""

import logging
import time
from collections.abc import Callable

import requests

log = logging.getLogger(__name__)

USER_AGENT = (
    "epc-ai-assistant/0.1 (portfolio research; +https://github.com/HondaAbuElNaga/epc-ai-assistant)"
)
# Temporary server-side problems worth retrying. 403/404 are final: retrying won't help.
RETRY_STATUSES = {429, 500, 502, 503, 504}
MAX_RETRY_AFTER = 60.0


class PoliteClient:
    """Wraps a requests.Session. Waits `delay` seconds between requests and retries
    429/5xx and connection errors with exponential backoff (backoff, 2*backoff, 4*backoff...).

    `session` and `sleep` are parameters so tests can pass fakes and run without network.
    """

    def __init__(
        self,
        session: requests.Session | None = None,
        *,
        delay: float = 1.0,
        timeout: float = 60.0,
        max_retries: int = 3,
        backoff: float = 2.0,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self.session = session or requests.Session()
        self.session.headers["User-Agent"] = USER_AGENT
        self.delay = delay
        self.timeout = timeout
        self.max_retries = max_retries
        self.backoff = backoff
        self.sleep = sleep
        self._first = True

    def _wait_turn(self) -> None:
        if not self._first and self.delay > 0:
            self.sleep(self.delay)
        self._first = False

    def _retry_wait(self, attempt: int, response=None) -> float:
        retry_after = response.headers.get("Retry-After") if response is not None else None
        if retry_after and retry_after.isdigit():
            return min(float(retry_after), MAX_RETRY_AFTER)
        return self.backoff * 2**attempt

    def get(self, url: str, **kwargs) -> requests.Response:
        """GET with politeness and retries. Returns the final response (any status code);
        raises only if connection errors persist after all retries."""
        for attempt in range(self.max_retries + 1):
            self._wait_turn()
            last_try = attempt == self.max_retries
            try:
                response = self.session.get(url, timeout=self.timeout, **kwargs)
            except (requests.ConnectionError, requests.Timeout) as exc:
                if last_try:
                    raise
                wait = self._retry_wait(attempt)
                log.warning("%s: %s; retry %d in %.1fs", url, exc, attempt + 1, wait)
                self.sleep(wait)
                continue
            if response.status_code in RETRY_STATUSES and not last_try:
                wait = self._retry_wait(attempt, response)
                log.warning(
                    "%s: HTTP %d; retry %d in %.1fs", url, response.status_code, attempt + 1, wait
                )
                response.close()
                self.sleep(wait)
                continue
            return response
        raise AssertionError("unreachable")
