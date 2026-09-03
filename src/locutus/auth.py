"""
Auth middleware (Auth Requirements spec, M6): three decorators route
handlers use to gate access, plus the identity-resolution and permission
logic they share.

Every read of a user/resource/token document here goes through the storage
abstraction layer (locutus.persistence()) rather than pymongo/Firestore
directly, so this module works unmodified on both backends.
"""

import hashlib
import logging
from collections.abc import Callable
from datetime import UTC, datetime
from functools import wraps
from typing import TypedDict, cast, overload

from flask import g, request, session
from flask.typing import ResponseReturnValue

import locutus
from locutus.api import default_headers
from locutus.model.user import User
from locutus.model.visibility import Visibility

logger = logging.getLogger(__name__)

TOKEN_PREFIX = "lct_"
_BEARER_PREFIX = "Bearer "

_RouteBound = Callable[..., ResponseReturnValue]


class CurrentUser(TypedDict):
    user_id: str
    institutionIds: list[str]
    role: str


def hash_token(token: str) -> str:
    """SHA-256 of a raw API token. Tokens are long and random (M8), so
    speed isn't a concern -- shared here so token creation (M9) and lookup
    (this module) always hash the same way."""
    return hashlib.sha256(token.encode()).hexdigest()


def _user_context(user_doc: dict) -> CurrentUser:
    return {
        "user_id": user_doc["id"],
        "institutionIds": user_doc.get("institutionIds", []),
        "role": user_doc.get("role", User.Role.User),
    }


def _resolve_via_token(token: str) -> CurrentUser | None:
    token_doc = locutus.persistence().get_api_token(hash_token(token))
    if token_doc is None:
        return None

    expires_at = token_doc.get("expiresAt")
    if expires_at is not None:
        # pymongo returns naive datetimes by default even though we always
        # write UTC-aware ones (M8) -- normalize before comparing, or a
        # naive-vs-aware comparison raises instead of just being wrong.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=UTC)
        if expires_at < datetime.now(UTC):
            return None

    user_doc = locutus.persistence().get_user(token_doc["userId"])
    if user_doc is None:
        return None

    # Fire-and-forget per M6 -- a failure here must never fail the request
    # this token is actually trying to make.
    try:
        token_id = token_doc.get("id") or str(token_doc.get("_id"))
        locutus.persistence().update_token_last_used(token_id)
    except Exception:
        logger.exception("Failed to update API token lastUsedAt")

    return _user_context(user_doc)


def _resolve_via_session() -> CurrentUser | None:
    user_id = session.get("user_id")
    if not user_id:
        return None

    user_doc = locutus.persistence().get_user(user_id)
    if user_doc is None:
        return None

    return _user_context(user_doc)


def _resolve_identity() -> tuple[CurrentUser | None, bool]:
    """Returns (user, resolved_via_api_token). Path B (API token) is tried
    first since a Bearer lct_ header unambiguously means Path B; anything
    else falls back to the session (Path A)."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith(_BEARER_PREFIX):
        token = auth_header[len(_BEARER_PREFIX) :]
        if token.startswith(TOKEN_PREFIX):
            return _resolve_via_token(token), True

    return _resolve_via_session(), False


def get_permission(resource: dict, current_user: CurrentUser) -> str | None:
    """Returns "editor", "viewer", or None, per the M5 access matrix.

    visibility is a switch, not a stacked set of checks -- exactly one of
    Institution/Restricted/Registered/Public governs a resource's default
    access. Owner always gets "editor" regardless of visibility. A resource
    saved before M4 (no visibility key at all) reads as Registered, per
    that migration decision -- any authenticated user, same as "public"
    meant before this enum existed.
    """
    # Persisted as owner_id (snake_case), matching this codebase's field
    # naming convention -- not the spec doc's ownerId, which was sketched
    # without seeing the actual schema (see the Phase 1.3 note).
    if resource.get("owner_id") == current_user["user_id"]:
        return "editor"

    visibility = resource.get("visibility") or Visibility.Registered

    if visibility == Visibility.Institution:
        institutions = resource.get("access", {}).get("institutions", {})
        for institution_id in current_user["institutionIds"]:
            if institution_id in institutions:
                return institutions[institution_id]
        return None

    if visibility == Visibility.Restricted:
        users = resource.get("access", {}).get("users", {})
        return users.get(current_user["user_id"])

    if visibility in (Visibility.Registered, Visibility.Public):
        # Public isn't enforced yet (W3) -- every caller already had to
        # authenticate to get here, so it behaves like Registered for now.
        return "viewer"

    return None


@overload
def require_auth[Route: _RouteBound](f: Route) -> Route: ...
@overload
def require_auth[Route: _RouteBound](
    f: None = None, *, interactive_only: bool = False
) -> Callable[[Route], Route]: ...


def require_auth(f=None, *, interactive_only: bool = False):
    """Resolves the caller's identity (Path A: session, or Path B: an
    lct_ API token) and sets g.current_user. 401s if neither resolves.

    interactive_only=True additionally 403s a request resolved via an API
    token -- for endpoints like token creation (M9) that must not let a
    token mint another token.
    """

    def decorator[Route: _RouteBound](func: Route) -> Route:
        @wraps(func)
        def wrapped(*args, **kwargs):
            user, via_token = _resolve_identity()
            if user is None:
                return {"message": "Authentication required"}, 401, default_headers
            if interactive_only and via_token:
                return (
                    {"message": "This action requires an interactive session"},
                    403,
                    default_headers,
                )
            g.current_user = user
            return func(*args, **kwargs)

        # wraps() can't tell pyright that a wrapper adding new early-return
        # branches (401/403 tuples) still honors func's declared signature
        # from the caller's perspective -- it does (those are valid Flask
        # responses too), so this is a real cast, not a suppression.
        return cast(Route, wrapped)

    if f is not None:
        return decorator(f)
    return decorator


def require_admin[Route: _RouteBound](func: Route) -> Route:
    """Resolves identity like require_auth, and additionally 403s any
    non-admin caller. Independent of the resource-level editor/viewer
    roles below -- this is the system-level role from the User model."""

    @wraps(func)
    def wrapped(*args, **kwargs):
        user, _ = _resolve_identity()
        if user is None:
            return {"message": "Authentication required"}, 401, default_headers
        if user["role"] != User.Role.Admin:
            return {"message": "Admin access required"}, 403, default_headers
        g.current_user = user
        return func(*args, **kwargs)

    return cast(Route, wrapped)


def _require_resource_access[Route: _RouteBound](
    resource_type: str, id_param: str, need_write: bool
) -> Callable[[Route], Route]:
    def decorator(func: Route) -> Route:
        @wraps(func)
        def wrapped(*args, **kwargs):
            user, _ = _resolve_identity()
            if user is None:
                return {"message": "Authentication required"}, 401, default_headers

            resource_id = kwargs.get(id_param)
            resource = locutus.persistence().get_resource(resource_type, resource_id)
            if resource is None:
                return (
                    {"message": f"{resource_type} not found: {resource_id}"},
                    404,
                    default_headers,
                )

            permission = get_permission(resource, user)
            allowed = permission == "editor" if need_write else permission is not None
            if not allowed:
                return {"message": "Forbidden"}, 403, default_headers

            g.current_user = user
            return func(*args, **kwargs)

        return cast(Route, wrapped)

    return decorator


def require_read_access[Route: _RouteBound](
    resource_type: str, id_param: str
) -> Callable[[Route], Route]:
    """404s if resource_type/id_param (a URL kwarg) doesn't exist; 403s if
    it exists but current_user has neither owner, institution, nor public
    access. For a Simple-derived entity (a vote, a comment), pass the
    nearest Serializable ancestor's resource_type/id_param instead -- e.g.
    a vote nested under /Terminology/<id>/... decorates as
    ("Terminology", "id"), not as the vote itself."""
    return _require_resource_access(resource_type, id_param, need_write=False)


def require_write_access[Route: _RouteBound](
    resource_type: str, id_param: str
) -> Callable[[Route], Route]:
    """Same as require_read_access, but 403s unless current_user is the
    owner or has editor access via their institution/user grant."""
    return _require_resource_access(resource_type, id_param, need_write=True)
