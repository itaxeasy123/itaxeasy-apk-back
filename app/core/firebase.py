"""
Firebase Admin SDK integration.

OTP send/verify is handled entirely on-device by the Firebase Phone Auth SDK
(this is the free part). The backend's only job here is to VERIFY the Firebase
ID token the app forwards after a successful OTP verification, and to extract the
trusted phone number / Firebase UID from it.
"""
import os
import threading
from dataclasses import dataclass
from typing import Optional

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

from app.core.config import settings

_init_lock = threading.Lock()
_app: Optional[firebase_admin.App] = None


@dataclass
class FirebaseIdentity:
    uid: str
    phone_number: Optional[str]
    email: Optional[str]


def init_firebase() -> Optional[firebase_admin.App]:
    """
    Idempotently initialize the Firebase Admin app from the service-account JSON.

    Safe to call at startup. If the credentials file is missing we log a warning
    and return None instead of crashing, so the rest of the app (docs, health
    check, migrations) still works during early setup. Token verification will
    then fail clearly at request time until the credentials are provided.
    """
    global _app
    if _app is not None:
        return _app

    with _init_lock:
        if _app is not None:
            return _app

        cred_path = settings.FIREBASE_CREDENTIALS_PATH
        if not cred_path or not os.path.exists(cred_path):
            print(
                f"[firebase] WARNING: credentials file not found at "
                f"'{cred_path}'. Phone-OTP auth will be unavailable until you "
                f"add the service-account JSON (see README)."
            )
            return None

        options = {}
        if settings.FIREBASE_PROJECT_ID:
            options["projectId"] = settings.FIREBASE_PROJECT_ID

        cred = credentials.Certificate(cred_path)
        _app = firebase_admin.initialize_app(cred, options or None)
        print("[firebase] Admin SDK initialized.")
        return _app


def verify_id_token(id_token: str) -> FirebaseIdentity:
    """
    Verify a Firebase ID token and return the trusted identity.

    Raises ValueError with a human-readable message on any failure so the
    caller (auth service) can map it to an HTTP 401.
    """
    app = init_firebase()
    if app is None:
        raise ValueError(
            "Firebase is not configured on the server. "
            "Missing service-account credentials."
        )

    try:
        decoded = firebase_auth.verify_id_token(id_token, app=app)
    except firebase_auth.ExpiredIdTokenError as e:
        print(f"[firebase] Token verification failed: ExpiredToken - {e}")
        raise ValueError("Firebase token has expired. Please sign in again.")
    except firebase_auth.RevokedIdTokenError as e:
        print(f"[firebase] Token verification failed: RevokedToken - {e}")
        raise ValueError("Firebase token has been revoked. Please sign in again.")
    except Exception as e:
        import traceback
        print(f"[firebase] Token verification failed with exception: {type(e).__name__} - {e}")
        traceback.print_exc()
        raise ValueError(f"Invalid Firebase token: {e}")

    uid = decoded.get("uid")
    if not uid:
        raise ValueError("Firebase token is missing a user id.")

    return FirebaseIdentity(
        uid=uid,
        phone_number=decoded.get("phone_number"),
        email=decoded.get("email"),
    )
