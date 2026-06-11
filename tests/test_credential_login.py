"""Tests for the automated username/password (Azure AD B2C) login.

These tests stub out Home Assistant and aiohttp so they can run with a plain
``python3 tests/test_credential_login.py`` (no Home Assistant install needed),
and they are also discoverable by pytest.

They exercise the server-side login that replaces the old manual
"copy the fordapp:// token out of your browser" flow:

  authorize page -> parse transId/csrf -> SelfAsserted (credentials)
  -> confirmed (capture code) -> token exchange.
"""
import asyncio
import importlib.util
import os
import sys
import types

COMPONENT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "custom_components",
    "fordpass",
)


def _install_stubs():
    """Register minimal homeassistant/aiohttp stubs so the module imports."""
    if "homeassistant" not in sys.modules:
        ha = types.ModuleType("homeassistant")
        exceptions = types.ModuleType("homeassistant.exceptions")

        class HomeAssistantError(Exception):
            """Stub of homeassistant.exceptions.HomeAssistantError."""

        exceptions.HomeAssistantError = HomeAssistantError
        helpers = types.ModuleType("homeassistant.helpers")
        aiohttp_client = types.ModuleType("homeassistant.helpers.aiohttp_client")
        aiohttp_client.async_get_clientsession = lambda hass: None
        ha.exceptions = exceptions
        ha.helpers = helpers
        helpers.aiohttp_client = aiohttp_client
        sys.modules["homeassistant"] = ha
        sys.modules["homeassistant.exceptions"] = exceptions
        sys.modules["homeassistant.helpers"] = helpers
        sys.modules["homeassistant.helpers.aiohttp_client"] = aiohttp_client
    if "aiohttp" not in sys.modules:
        aiohttp = types.ModuleType("aiohttp")

        class ClientTimeout:
            def __init__(self, *args, **kwargs):
                pass

        aiohttp.ClientTimeout = ClientTimeout
        sys.modules["aiohttp"] = aiohttp


def _load_module():
    """Load fordpass.fordpass_new without executing the package __init__."""
    _install_stubs()
    if "fordpass" not in sys.modules:
        pkg = types.ModuleType("fordpass")
        pkg.__path__ = [COMPONENT_DIR]
        sys.modules["fordpass"] = pkg
    for name in ("const", "fordpass_new"):
        spec = importlib.util.spec_from_file_location(
            f"fordpass.{name}", os.path.join(COMPONENT_DIR, f"{name}.py")
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules[f"fordpass.{name}"] = module
        spec.loader.exec_module(module)
    return sys.modules["fordpass.fordpass_new"]


fordpass_new = _load_module()


SAMPLE_LOGIN_PAGE = """
<html><head><script>
var SETTINGS = {"remoteResource":"x","hosts":{"tenant":"/t"},
"transId":"StateProperties=eyJUSUQiOiJ0ZXN0In0",
"csrf":"csrf-token-abc123","api":"CombinedSigninAndSignup"};
</script></head><body>login</body></html>
"""


# --- Fakes ----------------------------------------------------------------

class FakeResponse:
    def __init__(self, status=200, text="", json_data=None, headers=None):
        self.status = status
        self._text = text
        self._json = json_data
        self.headers = headers or {}

    async def text(self):
        return self._text

    async def json(self):
        return self._json

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


class FakeSession:
    """Routes requests to scripted responses by URL substring, records calls."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def _resolve(self, method, url, **kwargs):
        self.calls.append({"method": method, "url": url, **kwargs})
        for fragment, response in self.routes.items():
            if fragment in url:
                return response
        raise AssertionError(f"No fake route for {method} {url}")

    def get(self, url, **kwargs):
        return self._resolve("GET", url, **kwargs)

    def post(self, url, **kwargs):
        return self._resolve("POST", url, **kwargs)


class FakeStore:
    def __init__(self):
        self.saved = None

    async def async_save(self, data):
        self.saved = data

    async def async_load(self):
        return self.saved


def _make_vehicle(session):
    v = fordpass_new.Vehicle("user@example.com", "hunter2", "", "USA", FakeStore(), None)
    v.session = session
    return v


def _success_routes():
    return {
        "oauth2/v2.0/authorize": FakeResponse(200, text=SAMPLE_LOGIN_PAGE),
        "/SelfAsserted": FakeResponse(200, json_data={"status": "200"}, text='{"status":"200"}'),
        "CombinedSigninAndSignup/confirmed": FakeResponse(
            302, headers={"Location": "fordapp://userauthorized/?code=THECODE123"}
        ),
        "oauth2/v2.0/token": FakeResponse(200, json_data={"access_token": "idp-tok"}),
        "cat-with-b2c-access-token": FakeResponse(
            200,
            json_data={
                "access_token": "cat-tok",
                "refresh_token": "refresh-tok",
                "expires_in": 3600,
            },
        ),
    }


# --- Tests ----------------------------------------------------------------

def test_extract_login_settings_parses_transid_and_csrf():
    result = fordpass_new.Vehicle._extract_login_settings(SAMPLE_LOGIN_PAGE)
    assert result == ("StateProperties=eyJUSUQiOiJ0ZXN0In0", "csrf-token-abc123")


def test_extract_login_settings_missing_block_returns_none():
    assert fordpass_new.Vehicle._extract_login_settings("<html>no settings</html>") is None


def test_auth_happy_path():
    session = FakeSession(_success_routes())
    vehicle = _make_vehicle(session)
    assert asyncio.run(vehicle.auth()) is True

    # Credentials were posted to SelfAsserted with the CSRF token.
    sa = next(c for c in session.calls if "/SelfAsserted" in c["url"])
    assert sa["data"]["signInName"] == "user@example.com"
    assert sa["data"]["password"] == "hunter2"
    assert sa["headers"]["X-Csrf-Token"] == "csrf-token-abc123"

    # The captured code (not the whole fordapp:// URL) reached the token exchange.
    tok = next(c for c in session.calls if "oauth2/v2.0/token" in c["url"])
    assert tok["data"]["code"] == "THECODE123"

    # Final CAT token was persisted.
    assert vehicle.token_store.saved["access_token"] == "cat-tok"


def test_auth_bad_credentials_raises_invalid_credentials():
    routes = _success_routes()
    routes["/SelfAsserted"] = FakeResponse(
        200, json_data={"status": "400", "message": "Invalid password"},
        text='{"status":"400","message":"Invalid password"}',
    )
    vehicle = _make_vehicle(FakeSession(routes))
    try:
        asyncio.run(vehicle.auth())
    except fordpass_new.InvalidCredentials as ex:
        assert "Invalid password" in str(ex)
    else:
        raise AssertionError("expected InvalidCredentials")


def test_auth_akamai_block_raises_login_flow_error():
    # Akamai returns a 403 "Access Denied" HTML page on the credential POST.
    routes = _success_routes()
    routes["/SelfAsserted"] = FakeResponse(
        403, text="<HTML><HEAD><TITLE>Access Denied</TITLE></HEAD><BODY>...</BODY></HTML>"
    )
    vehicle = _make_vehicle(FakeSession(routes))
    try:
        asyncio.run(vehicle.auth())
    except fordpass_new.LoginFlowError:
        pass
    else:
        raise AssertionError("expected LoginFlowError")


def test_auth_blocked_login_page_raises_login_flow_error():
    routes = _success_routes()
    routes["oauth2/v2.0/authorize"] = FakeResponse(200, text="<html>blocked</html>")
    vehicle = _make_vehicle(FakeSession(routes))
    try:
        asyncio.run(vehicle.auth())
    except fordpass_new.LoginFlowError:
        pass
    else:
        raise AssertionError("expected LoginFlowError")


def test_auth_no_code_in_redirect_raises_login_flow_error():
    routes = _success_routes()
    routes["CombinedSigninAndSignup/confirmed"] = FakeResponse(
        302, headers={"Location": "https://login.ford.com/error"}
    )
    vehicle = _make_vehicle(FakeSession(routes))
    try:
        asyncio.run(vehicle.auth())
    except fordpass_new.LoginFlowError:
        pass
    else:
        raise AssertionError("expected LoginFlowError")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"PASS {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
