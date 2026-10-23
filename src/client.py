from dataclasses import dataclass
import httpx
import os
from dotenv import load_dotenv

from types import TracebackType

load_dotenv()

@dataclass
class InstagramProfile:
    id: str
    username: str
    account_type: str

class InstagramClient:
    _owns_http_client: bool

    def __init__(self, access_token: str, httpx_client: httpx.Client | None = None) -> None:
        self._closed: bool = False
        if not access_token:
            raise ValueError("Error: Need to supply an Instagram token")
        self.access_token: str = access_token

        if httpx_client is None:
            self.httpx_client: httpx.Client = httpx.Client(
                base_url="https://graph.instagram.com",
                timeout=10.0,
            )
            self._owns_http_client = True
        else:
            self.httpx_client = httpx_client
            self._owns_http_client = False

    def get_profile(self) -> InstagramProfile:
        if self._closed:
            raise RuntimeError("Error: tried to use closed wrapper")
        r = self.httpx_client.get(
            "me",
            params={
                "fields": "id,username,account_type",
                "access_token": self.access_token
            },
        )
        r.raise_for_status()
        data = r.json()
        return InstagramProfile(**data)

    def close(self) -> None:
        if self._closed:
            return
        if self._owns_http_client:
            self.httpx_client.close()
        self._closed = True

    def __enter__(self) -> InstagramClient:
        return self

    def __exit__(self, exc_type: type[BaseException] | None, exc_val: BaseException | None, exc_tb: TracebackType | None) -> None:
        self.close()

token = os.getenv("INSTAGRAM_ACCESS_TOKEN")

if not token:
    raise ValueError("INSTAGRAM_ACCESS_TOKEN is not set")

with InstagramClient(token) as ic:
    profile = ic.get_profile()

print(profile)