"""Cross-cutting governance: RBAC, PII masking, idempotency and audit.

Applied around business actions: authorize (or deny) by caller role, mask personal
data in outputs, make writes idempotent, and audit each decision. RBAC and PII masking
are wired in once an authentication layer provides a ``Principal``.
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import StrEnum

from app.logging import get_logger
from app.observability import METRICS

_logger = get_logger("app.governance")

_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_PHONE = re.compile(r"\b(?:\+?\d[\s.-]?){9,}\d\b")


class AccessDeniedError(RuntimeError):
    """Action refused by the RBAC policy."""


class Permission(StrEnum):
    """Atomic permissions exposed by the domain."""

    READ = "read"
    WRITE = "write"


@dataclass(frozen=True)
class Principal:
    """Authenticated caller: identifier and roles."""

    user_id: str
    roles: frozenset[str]


_ROLE_PERMISSIONS: dict[str, frozenset[Permission]] = {
    "viewer": frozenset({Permission.READ}),
    "operator": frozenset({Permission.READ, Permission.WRITE}),
}


class RBACPolicy:
    """Role-based access control policy."""

    def __init__(self, role_permissions: dict[str, frozenset[Permission]] | None = None) -> None:
        self._role_permissions = role_permissions or _ROLE_PERMISSIONS

    def permissions_of(self, principal: Principal) -> frozenset[Permission]:
        granted: set[Permission] = set()
        for role in principal.roles:
            granted |= self._role_permissions.get(role, frozenset())
        return frozenset(granted)

    def authorize(self, principal: Principal, permission: Permission) -> None:
        """Raise ``AccessDeniedError`` if the principal lacks the permission."""
        if permission not in self.permissions_of(principal):
            METRICS.incr("governance.access_denied")
            raise AccessDeniedError(f"{principal.user_id} not authorized for {permission}")


def mask_pii(text: str) -> str:
    """Redact emails and phone numbers in a text."""
    masked = _EMAIL.sub("[email]", text)
    return _PHONE.sub("[phone]", masked)


class IdempotencyGuard:
    """Prevents replay of a write: remembers keys already processed."""

    def __init__(self) -> None:
        self._seen: set[str] = set()

    def is_new(self, key: str) -> bool:
        """Return True the first time a key is seen, then record it."""
        if key in self._seen:
            return False
        self._seen.add(key)
        return True


@dataclass(frozen=True)
class AuditEntry:
    """Immutable audit entry."""

    user_id: str
    action: str
    resource: str
    allowed: bool
    timestamp: float


@dataclass
class AuditLog:
    """Append-only in-memory audit log (persist to DB/SIEM in production)."""

    entries: list[AuditEntry] = field(default_factory=list)

    def record(self, principal: Principal, action: str, resource: str, allowed: bool) -> None:
        entry = AuditEntry(
            user_id=principal.user_id,
            action=action,
            resource=resource,
            allowed=allowed,
            timestamp=time.time(),
        )
        self.entries.append(entry)
        _logger.info(
            "audit",
            extra={
                "user": principal.user_id,
                "action": action,
                "resource": resource,
                "allowed": allowed,
            },
        )
