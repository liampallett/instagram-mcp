import httpx
import pytest

from src.client import InstagramClient, InstagramProfile

def test_get_profile_success():
    def mock_handler(request : httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "12345",
                "username": "test_user",
                "account_type": "MEDIA_CREATOR",
            },
        )

    transport = httpx.MockTransport(mock_handler)

    with httpx.Client(
            transport=transport,
            base_url="https://graph.instagram.com",
    ) as http_client:
        with InstagramClient("fake_token", http_client) as instagram:
            profile = instagram.get_profile()

    assert isinstance(profile, InstagramProfile)
    assert profile.id == "12345"
    assert profile.username == "test_user"
    assert profile.account_type == "MEDIA_CREATOR"

def test_get_profile_failure():
    def mock_handler(request : httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "Invalid token"})

    transport = httpx.MockTransport(mock_handler)
    with pytest.raises(httpx.HTTPStatusError) as exc_info:
        with httpx.Client(
                transport=transport,
                base_url="https://graph.instagram.com",
        ) as http_client:
            with InstagramClient("fake_token", http_client) as instagram:
                instagram.get_profile()

    assert exc_info.value.response.status_code == 401

def test_instagram_client_internal_ownership():
    instagram = InstagramClient("fake token")
    instagram.close()
    assert instagram.httpx_client.is_closed

def test_instagram_client_external_ownership():
    with httpx.Client() as http_client:
        instagram = InstagramClient("fake_token", http_client)
        instagram.close()

        assert not http_client.is_closed

    assert http_client.is_closed
    with pytest.raises(RuntimeError):
        instagram.get_profile()

def test_close_wrapper():
    instagram = InstagramClient("fake token")
    instagram.close()
    with pytest.raises(RuntimeError):
        instagram.get_profile()

def test_invalid_token():
    with pytest.raises(ValueError):
        InstagramClient("")


def test_repeated_close():
    instagram = InstagramClient("fake token")
    instagram.close()
    instagram.close()