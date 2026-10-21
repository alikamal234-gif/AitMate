"""Security, Authentication, and Secret Redaction Utilities."""

import re
from typing import Any, Dict
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from backend.app.core.config import settings

# HTTP Bearer scheme for token validation
security_scheme = HTTPBearer(auto_error=False)

# Patterns that match API keys, tokens, or common secret structures
SECRET_PATTERNS = [
    (re.compile(r"sk-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE), "[REDACTED_API_KEY]"),
    (re.compile(r"bearer\s+[a-zA-Z0-9_\-\.]{16,}", re.IGNORECASE), "Bearer [REDACTED_TOKEN]"),
    (re.compile(r"glpat-[a-zA-Z0-9_\-]{16,}", re.IGNORECASE), "[REDACTED_GITLAB_TOKEN]"),
    (re.compile(r"password['\"]?\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE), 'password="[REDACTED_PWD]"'),
]


def redact_secrets(content: str) -> str:
    """Scrub sensitive strings matching common secret patterns."""
    if not isinstance(content, str):
        return content
    redacted = content
    for pattern, replacement in SECRET_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def redact_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively scrub sensitive keys and values in a dictionary."""
    sanitized: Dict[str, Any] = {}
    sensitive_keys = {"password", "secret", "token", "api_key", "authorization", "cookie"}
    for k, v in data.items():
        if any(sk in k.lower() for sk in sensitive_keys):
            sanitized[k] = "[REDACTED]"
        elif isinstance(v, dict):
            sanitized[k] = redact_dict(v)
        elif isinstance(v, str):
            sanitized[k] = redact_secrets(v)
        else:
            sanitized[k] = v
    return sanitized


async def verify_session_token(
    credentials: HTTPAuthorizationCredentials = Security(security_scheme),
) -> str:
    """Validate incoming HTTP Bearer token against the current session token."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Missing Bearer token in Authorization header.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    provided_token = credentials.credentials.strip()
    expected_token = settings.API_TOKEN.strip()

    if provided_token != expected_token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden. Invalid or expired session token.",
        )

    return provided_token
