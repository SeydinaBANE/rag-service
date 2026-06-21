import pytest

from app.governance import (
    AccessDeniedError,
    AuditLog,
    IdempotencyGuard,
    Permission,
    Principal,
    RBACPolicy,
    mask_pii,
)
from app.observability import METRICS


def test_rbac_allows_operator_write():
    policy = RBACPolicy()
    operator = Principal(user_id="u1", roles=frozenset({"operator"}))
    policy.authorize(operator, Permission.WRITE)


def test_rbac_denies_viewer_write():
    policy = RBACPolicy()
    viewer = Principal(user_id="u2", roles=frozenset({"viewer"}))
    with pytest.raises(AccessDeniedError):
        policy.authorize(viewer, Permission.WRITE)
    assert METRICS.counters["governance.access_denied"] == 1


def test_rbac_permissions_union_across_roles():
    policy = RBACPolicy()
    principal = Principal(user_id="u3", roles=frozenset({"viewer", "operator"}))
    assert policy.permissions_of(principal) == frozenset({Permission.READ, Permission.WRITE})


def test_mask_pii_redacts_email_and_phone():
    masked = mask_pii("contact a@b.com au 06 12 34 56 78")
    assert "a@b.com" not in masked
    assert "[email]" in masked
    assert "[phone]" in masked


def test_idempotency_guard_blocks_replay():
    guard = IdempotencyGuard()
    assert guard.is_new("k1") is True
    assert guard.is_new("k1") is False


def test_audit_log_records_entry():
    audit = AuditLog()
    principal = Principal(user_id="u1", roles=frozenset({"operator"}))
    audit.record(principal, action="index", resource="rag", allowed=True)
    assert len(audit.entries) == 1
    assert audit.entries[0].allowed is True
    assert audit.entries[0].action == "index"
