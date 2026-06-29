"""
MSG91 SMS Flow integration (https://control.msg91.com).

Since the approved templates are registered as SMS Flow templates instead of
the dedicated OTP product templates, we generate and store the OTP code locally
in a memory cache, and deliver it via the MSG91 v5 Flow API.
"""
import httpx

from app.core.config import settings



class Msg91Error(Exception):
    """Raised when MSG91 returns an error (bad config, etc.)."""


def normalize_mobile(phone: str) -> str:
    """
    Convert any Indian phone input to MSG91's expected `91XXXXXXXXXX` form
    (country code, no '+'). Accepts '+91 98765 43210', '9876543210', etc.
    """
    digits = "".join(c for c in (phone or "") if c.isdigit())
    if len(digits) > 10 and digits.startswith("91"):
        return digits
    return "91" + digits[-10:]


def _require_config() -> None:
    if not settings.MSG91_AUTH_KEY:
        raise Msg91Error(
            "MSG91 is not configured on the server "
            "(MSG91_AUTH_KEY missing)."
        )


def _check_response(resp: httpx.Response, fallback: str) -> dict:
    """MSG91 OTP API returns 200 with {"type": "success"|"error", "message": ...}."""
    try:
        data = resp.json()
    except ValueError:
        raise Msg91Error(f"{fallback} (unexpected response: {resp.text[:200]})")
    if isinstance(data, dict) and data.get("type") == "success":
        return data
    message = data.get("message") if isinstance(data, dict) else None
    raise Msg91Error(str(message or fallback))


async def send_otp(phone: str) -> str:
    """Send an OTP via MSG91's dedicated SendOTP API."""
    _require_config()
    mobile = normalize_mobile(phone)

    # Build query parameters
    params = {
        "mobile": mobile,
        "authkey": settings.MSG91_AUTH_KEY,
        "otp_length": settings.MSG91_OTP_LENGTH,
        "expiry": settings.MSG91_OTP_EXPIRY_MINUTES,
    }

    # Only pass custom template_id if it's explicitly configured.
    # If left empty, MSG91 uses its own default global DLT-approved template!
    if settings.MSG91_TEMPLATE_ID:
        params["template_id"] = settings.MSG91_TEMPLATE_ID

    if settings.MSG91_SENDER_ID:
        params["sender"] = settings.MSG91_SENDER_ID

    url = f"{settings.MSG91_BASE_URL}/otp"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, params=params)

    data = _check_response(resp, "Could not send OTP. Please try again.")
    # Return the request ID from MSG91
    return str(data.get("request_id", ""))


async def verify_otp(phone: str, otp: str) -> None:
    """Verify the OTP using MSG91's verify API."""
    _require_config()
    mobile = normalize_mobile(phone)

    params = {
        "mobile": mobile,
        "otp": otp,
        "authkey": settings.MSG91_AUTH_KEY,
    }

    url = f"{settings.MSG91_BASE_URL}/otp/verify"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)

    # MSG91 returns type="success" on successful verification, or type="error" with "message"
    _check_response(resp, "Invalid or expired OTP. Please try again.")


async def resend_otp(phone: str, channel: str = "text") -> None:
    """Resend a fresh OTP via MSG91's retry API."""
    _require_config()
    mobile = normalize_mobile(phone)

    params = {
        "mobile": mobile,
        "authkey": settings.MSG91_AUTH_KEY,
        "retrytype": "voice" if channel == "voice" else "text",
    }

    url = f"{settings.MSG91_BASE_URL}/otp/retry"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)

    _check_response(resp, "Could not resend OTP. Please try again.")


async def verify_widget_token(access_token: str) -> str:
    """
    Verify the MSG91 SendOTP Widget access token and return the verified mobile number.
    """
    _require_config()

    headers = {
        "Content-Type": "application/json",
        "authkey": settings.MSG91_AUTH_KEY,
    }

    payload = {
        "authkey": settings.MSG91_AUTH_KEY,
        "access-token": access_token,
    }

    url = "https://control.msg91.com/api/v5/widget/verifyAccessToken"

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(url, headers=headers, json=payload)

    if resp.status_code != 200:
        raise Msg91Error(
            f"MSG91 verification returned status code {resp.status_code}: {resp.text[:200]}"
        )

    try:
        data = resp.json()
    except ValueError:
        raise Msg91Error(f"Invalid JSON response from MSG91: {resp.text[:200]}")

    if isinstance(data, dict):
        if data.get("type") == "error":
            message = data.get("message", "Token verification failed")
            raise Msg91Error(str(message))

        # Extract mobile number from response (can be in data.mobile, data.data.mobile, etc.)
        mobile = None
        inner_data = data.get("data")
        if isinstance(inner_data, dict):
            mobile = inner_data.get("mobile") or inner_data.get("phone")
        elif isinstance(inner_data, str) and inner_data.isdigit():
            mobile = inner_data

        if not mobile:
            mobile = data.get("mobile") or data.get("phone")

        if mobile:
            return str(mobile)

        # Success fallback scan
        if data.get("type") == "success" or data.get("status") == "success":
            import re
            numbers = re.findall(r"\b\d{10,12}\b", resp.text)
            if numbers:
                return numbers[0]

        raise Msg91Error(
            f"Could not extract verified mobile number from MSG91 response: {resp.text[:200]}"
        )
    else:
        raise Msg91Error(
            f"Unexpected response format from MSG91: {resp.text[:200]}"
        )


