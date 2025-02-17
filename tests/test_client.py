"""Define tests for the client object."""
# pylint: disable=protected-access
import asyncio
from datetime import datetime, timedelta
import json

import aiohttp
import pytest

from regenmaschine import Client
from regenmaschine.errors import RequestError, TokenExpiredError, UnknownAPICallError

import tests.async_mock as mock
from tests.common import (
    TEST_ACCESS_TOKEN,
    TEST_API_VERSION,
    TEST_EMAIL,
    TEST_HOST,
    TEST_HW_VERSION,
    TEST_MAC,
    TEST_NAME,
    TEST_PASSWORD,
    TEST_PORT,
    TEST_SW_VERSION,
    load_fixture,
)


@pytest.mark.asyncio
async def test_legacy_login(authenticated_local_client):
    """Test loading a local controller through the legacy method."""
    async with authenticated_local_client:
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(
                TEST_HOST, TEST_PASSWORD, port=TEST_PORT, use_ssl=False
            )
            controller = next(iter(client.controllers.values()))

            assert controller._access_token == TEST_ACCESS_TOKEN
            assert controller.api_version == TEST_API_VERSION
            assert controller.hardware_version == TEST_HW_VERSION
            assert controller.mac == TEST_MAC
            assert controller.name == TEST_NAME
            assert controller.software_version == TEST_SW_VERSION


@pytest.mark.asyncio
async def test_load_local(authenticated_local_client):
    """Test loading a local controller."""
    async with authenticated_local_client:
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(TEST_HOST, TEST_PASSWORD, TEST_PORT, False)

            assert len(client.controllers) == 1

            controller = client.controllers[TEST_MAC]
            assert controller._access_token == TEST_ACCESS_TOKEN
            assert controller.api_version == TEST_API_VERSION
            assert controller.hardware_version == TEST_HW_VERSION
            assert controller.mac == TEST_MAC
            assert controller.name == TEST_NAME
            assert controller.software_version == TEST_SW_VERSION


@pytest.mark.asyncio
@pytest.mark.parametrize("provision_name_response", [json.dumps({"name": "89"})])
async def test_load_local_string_name(authenticated_local_client):
    """Test loading a local controller whose name (per the API) is not a string."""
    async with authenticated_local_client:
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(TEST_HOST, TEST_PASSWORD, TEST_PORT, False)

            assert len(client.controllers) == 1

            controller = client.controllers[TEST_MAC]
            assert isinstance(controller.name, str)
            assert controller.name == "89"


@pytest.mark.asyncio
async def test_load_local_skip(aresponses, authenticated_local_client):
    """Test skipping the loading of a local controller if it's already loaded."""
    authenticated_local_client.add(
        f"{TEST_HOST}:{TEST_PORT}",
        "/api/4/auth/login",
        "post",
        aresponses.Response(text=load_fixture("auth_login_response.json"), status=200),
    )
    authenticated_local_client.add(
        f"{TEST_HOST}:{TEST_PORT}",
        "/api/4/provision/wifi",
        "get",
        aresponses.Response(
            text=load_fixture("provision_wifi_response.json"), status=200
        ),
    )

    async with authenticated_local_client:
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(TEST_HOST, TEST_PASSWORD, TEST_PORT, True)
            controller = client.controllers[TEST_MAC]

            await client.load_local(TEST_HOST, TEST_PASSWORD, TEST_PORT, True)
            assert len(client.controllers) == 1
            assert client.controllers[TEST_MAC] == controller


@pytest.mark.asyncio
async def test_load_local_failure(aresponses):
    """Test loading a local controller and receiving a fail response."""
    aresponses.add(
        f"{TEST_HOST}:{TEST_PORT}",
        "/api/4/auth/login",
        "post",
        aresponses.Response(text=None, status=500),
    )

    with pytest.raises(RequestError):
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(TEST_HOST, TEST_PASSWORD, TEST_PORT, False)


@pytest.mark.asyncio
async def test_load_remote(authenticated_remote_client, event_loop):
    """Test loading a remote client."""
    async with authenticated_remote_client:
        async with aiohttp.ClientSession(loop=event_loop) as session:
            client = Client(session=session)
            await client.load_remote(TEST_EMAIL, TEST_PASSWORD)

            assert len(client.controllers) == 1

            controller = client.controllers[TEST_MAC]
            assert controller._access_token == TEST_ACCESS_TOKEN
            assert controller.api_version == TEST_API_VERSION
            assert controller.hardware_version == TEST_HW_VERSION
            assert controller.mac == TEST_MAC
            assert controller.name == TEST_NAME
            assert controller.software_version == TEST_SW_VERSION


@pytest.mark.asyncio
async def test_load_remote_skip(aresponses, authenticated_remote_client):
    """Test skipping the loading of a remote client if it's already loaded."""
    authenticated_remote_client.add(
        "my.rainmachine.com",
        "/login/auth",
        "post",
        aresponses.Response(
            text=load_fixture("remote_auth_login_1_response.json"), status=200
        ),
    )
    authenticated_remote_client.add(
        "my.rainmachine.com",
        "/devices/get-sprinklers",
        "post",
        aresponses.Response(
            text=load_fixture("remote_sprinklers_response.json"), status=200
        ),
    )

    async with authenticated_remote_client:
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_remote(TEST_EMAIL, TEST_PASSWORD, True)
            controller = client.controllers[TEST_MAC]

            await client.load_remote(TEST_EMAIL, TEST_PASSWORD, True)
            assert len(client.controllers) == 1
            assert client.controllers[TEST_MAC] == controller


@pytest.mark.asyncio
async def test_load_remote_failure(aresponses):
    """Test loading a remote client and receiving a fail response."""
    aresponses.add(
        "my.rainmachine.com",
        "/login/auth",
        "post",
        aresponses.Response(
            text=load_fixture("unauthenticated_response.json"), status=401
        ),
    )

    with pytest.raises(TokenExpiredError):
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_remote(TEST_EMAIL, TEST_PASSWORD)


@pytest.mark.asyncio
async def test_remote_error_known(aresponses):
    """Test that remote error handling works."""
    aresponses.add(
        "my.rainmachine.com",
        "/login/auth",
        "post",
        aresponses.Response(
            text=load_fixture("remote_error_known_response.json"), status=200
        ),
    )

    with pytest.raises(RequestError):
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_remote(TEST_EMAIL, TEST_PASSWORD)


@pytest.mark.asyncio
async def test_remote_error_http_body(aresponses):
    """Test that remote error handling works."""
    aresponses.add(
        "my.rainmachine.com",
        "/login/auth",
        "post",
        aresponses.Response(
            text=load_fixture("remote_error_http_body_response.json"), status=200
        ),
    )

    with pytest.raises(RequestError):
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_remote(TEST_EMAIL, TEST_PASSWORD)


@pytest.mark.asyncio
async def test_remote_error_unknown(aresponses):
    """Test that remote error handling works."""
    aresponses.add(
        "my.rainmachine.com",
        "/login/auth",
        "post",
        aresponses.Response(
            text=load_fixture("remote_error_unknown_response.json"), status=200
        ),
    )

    with pytest.raises(RequestError):
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_remote(TEST_EMAIL, TEST_PASSWORD)


@pytest.mark.asyncio
async def test_request_timeout(authenticated_local_client):
    """Test whether the client properly raises an error on timeout."""

    async def long_running_login(*args, **kwargs):  # pylint: disable=unused-argument
        """Define a method that takes 0.5 seconds to execute."""
        await asyncio.sleep(0.5)

    with mock.patch.object(aiohttp.ClientResponse, "json", long_running_login):
        async with authenticated_local_client:
            async with aiohttp.ClientSession() as session:
                with pytest.raises(RequestError):
                    client = Client(session=session, request_timeout=0.1)
                    await client.load_local(
                        TEST_HOST, TEST_PASSWORD, port=TEST_PORT, use_ssl=False
                    )


@pytest.mark.asyncio
async def test_request_unknown_api_call(aresponses, authenticated_local_client):
    """Test that an unknown API call is handled."""
    async with authenticated_local_client:
        authenticated_local_client.add(
            f"{TEST_HOST}:{TEST_PORT}",
            "/api/4/zone",
            "get",
            aresponses.Response(
                text=load_fixture("unknown_api_call_response.json"), status=400
            ),
        )

        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(
                TEST_HOST, TEST_PASSWORD, port=TEST_PORT, use_ssl=False
            )
            controller = next(iter(client.controllers.values()))

            with pytest.raises(UnknownAPICallError):
                _ = await controller.zones.all()


@pytest.mark.asyncio
async def test_request_unparseable_response(aresponses, authenticated_local_client):
    """Test a response that can't be parsed as JSON."""
    async with authenticated_local_client:
        authenticated_local_client.add(
            f"{TEST_HOST}:{TEST_PORT}",
            "/api/4/zone",
            "get",
            aresponses.Response(text="404 Not Found", status=404),
        )

        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(
                TEST_HOST, TEST_PASSWORD, port=TEST_PORT, use_ssl=False
            )
            controller = next(iter(client.controllers.values()))

            with pytest.raises(RequestError):
                _ = await controller.zones.all()


@pytest.mark.asyncio
async def test_token_expired_explicit_exception(aresponses):
    """Test that the appropriate error is thrown when a token expires explicitly."""
    aresponses.add(
        f"{TEST_HOST}:{TEST_PORT}",
        "/api/4/auth/login",
        "post",
        aresponses.Response(
            text=load_fixture("unauthenticated_response.json"), status=401
        ),
    )

    with pytest.raises(TokenExpiredError):
        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(TEST_HOST, TEST_PASSWORD, TEST_PORT, False)


@pytest.mark.asyncio
async def test_token_expired_implicit_exception(authenticated_local_client):
    """Test that the appropriate error is thrown when a token expires implicitly."""
    async with authenticated_local_client:
        with pytest.raises(TokenExpiredError):
            async with aiohttp.ClientSession() as session:
                client = Client(session=session)
                await client.load_local(
                    TEST_HOST, TEST_PASSWORD, port=TEST_PORT, use_ssl=False
                )
                controller = next(iter(client.controllers.values()))

                controller._access_token_expiration = datetime.now() - timedelta(
                    hours=1
                )
                await controller.request("get", "random/endpoint")


@pytest.mark.asyncio
async def test_retry_only_once_on_server_disconnected(
    aresponses, authenticated_local_client
):
    """Test we retry on server disconnected."""
    async with authenticated_local_client:
        authenticated_local_client.add(
            f"{TEST_HOST}:{TEST_PORT}",
            "/api/4/restrictions/raindelay",
            "get",
            aresponses.Response(
                text=load_fixture("restrictions_raindelay_response.json"), status=200
            ),
        )

        async with aiohttp.ClientSession() as session:
            client = Client(session=session)
            await client.load_local(
                TEST_HOST, TEST_PASSWORD, port=TEST_PORT, use_ssl=False
            )
            controller = next(iter(client.controllers.values()))
            patcher = None

            def _raise_and_stop_patch(*args, **kwargs):
                nonlocal patcher
                patcher.stop()
                raise aiohttp.ServerDisconnectedError

            patcher = mock.patch.object(
                session, "request", side_effect=_raise_and_stop_patch
            )
            patcher.start()

            data = await controller.restrictions.raindelay()
            assert data["delayCounter"] == -1

            with pytest.raises(RequestError), mock.patch.object(
                session, "request", side_effect=aiohttp.ServerDisconnectedError
            ):
                await controller.restrictions.raindelay()
