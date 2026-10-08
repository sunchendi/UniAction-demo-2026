"""Local prototype authentication; not school SSO or a production security review.

Reference checked 2026-10-03:
https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html
https://docs.python.org/3/library/hashlib.html
https://docs.python.org/3/library/secrets.html
"""
import base64
import hashlib
import hmac
import re
import secrets

PASSWORD_ITERATIONS = 600_000
SESSION_SECONDS = 8 * 3600
SESSION_COOKIE = "uniaction_session"
SESSION_PATTERN = re.compile(r"^[A-Za-z0-9_-]{43}$")
AUTH_WINDOW_SECONDS = 15 * 60


def hash_password(password):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_ITERATIONS)
    return "$".join(["pbkdf2_sha256", str(PASSWORD_ITERATIONS), base64.b64encode(salt).decode("ascii"), base64.b64encode(digest).decode("ascii")])


def verify_password(password, encoded):
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$")
        rounds = int(iterations)
        if algorithm != "pbkdf2_sha256" or rounds < PASSWORD_ITERATIONS or rounds > 5_000_000:
            return False
        salt = base64.b64decode(salt_text, validate=True)
        expected = base64.b64decode(digest_text, validate=True)
        if len(salt) < 16 or len(expected) != 32:
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def new_session_token():
    return secrets.token_urlsafe(32)


def token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


# A full-cost dummy verification prevents an unknown username from skipping KDF work.
DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))
