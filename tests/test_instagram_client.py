import httpx
import pytest

from src.client import InstagramClient, InstagramProfile, InstagramMedia

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


def test_get_media_success():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/me/media"
        assert request.url.params["access_token"] == "test-token"
        assert request.url.params["fields"] == "id,caption,media_type,timestamp"
        assert request.url.params["limit"] == "10"

        return httpx.Response(200, json={
            "data": [
                {
                    "id": "123",
                    "caption": "My first post",
                    "media_type": "IMAGE",
                    "timestamp": "2026-10-18T12:00:00+0000"
                },
                {
                    "id": "456",
                    "caption": "My second post",
                    "media_type": "CAROUSEL_ALBUM",
                    "timestamp": "2026-10-19T12:00:00+0000"
                }
            ]
        })

    http_client = httpx.Client(
        base_url="https://graph.instagram.com",
        transport=httpx.MockTransport(handler)
    )

    with http_client:
        with InstagramClient("test-token", httpx_client=http_client) as client:
            media = client.get_media()

    assert len(media) == 2
    assert all(isinstance(post, InstagramMedia) for post in media)
    assert media[0].id == "123"
    assert media[0].caption == "My first post"
    assert media[1].media_type == "CAROUSEL_ALBUM"


def test_get_media_no_caption():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "data": [
                {
                    "id": "789",
                    "media_type": "IMAGE",
                    "timestamp": "2026-10-20T12:00:00+0000"
                }
            ]
        })

    with httpx.Client(
        base_url="https://graph.instagram.com",
        transport=httpx.MockTransport(handler)
    ) as http_client:
        with InstagramClient("test-token", httpx_client=http_client) as client:
            media = client.get_media()

    assert len(media) == 1
    assert media[0].caption is None


def test_get_media_empty():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"data": []})

    with httpx.Client(
        base_url="https://graph.instagram.com",
        transport=httpx.MockTransport(handler)
    ) as http_client:
        with InstagramClient("test-token", httpx_client=http_client) as client:
            media = client.get_media()

    assert media == []
