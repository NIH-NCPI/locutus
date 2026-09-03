"""
Google sign-in (Auth Requirements spec, M1 Path A / M2 / S3). The front end
uses Google Identity Services directly and hands us the resulting ID token
-- we never talk to Google's token endpoint or hold a client secret, we
only verify a JWT that's already been issued.
"""

import logging
import os

from flask import request, session
from flask_restful import Resource
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

import locutus
from locutus.api import default_headers
from locutus.model.institution import Institution
from locutus.model.user import User

logger = logging.getLogger(__name__)

_google_request = google_requests.Request()


def _is_bootstrap_admin_email(email: str) -> bool:
    """Checks the small, separately-seeded admin-bootstrap email list (see
    the Auth Requirements spec, M2's first-admin-bootstrap decision) --
    deliberately not the same list as any Institution's allowedEmails,
    since institution membership and system-level admin role are
    independent dimensions."""
    doc = locutus.persistence().collection("Config").document("bootstrap").get()
    if not doc.exists:
        return False
    return email in doc.to_dict().get("adminEmails", [])


class GoogleLogin(Resource):
    def post(self):
        """Verifies a Google ID token and starts a session for the
        corresponding user, per the S3 email-allowlist first-login flow.

        Body: { "credential": "<Google ID token>" }
        """
        body = request.get_json(silent=True) or {}
        credential = body.get("credential")
        if not credential:
            return (
                {"message": "This action requires the parameter: 'credential'"},
                400,
                default_headers,
            )

        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            logger.error("GOOGLE_CLIENT_ID is not configured")
            return (
                {"message": "Google sign-in is not configured on this server"},
                500,
                default_headers,
            )

        try:
            claims = id_token.verify_oauth2_token(
                credential, _google_request, audience=client_id
            )
        except (GoogleAuthError, ValueError) as e:
            logger.info(f"Google ID token verification failed: {e}")
            return {"message": "Invalid credential"}, 401, default_headers

        if not claims.get("email_verified"):
            return (
                {"message": "Google account email is not verified"},
                401,
                default_headers,
            )

        google_sub = claims["sub"]
        email = claims["email"]

        user = User.find_by_google_sub(google_sub)
        if user is None:
            user = User.find_by_email(email)
            if user is not None:
                # Existing account (e.g. seeded directly) logging in with
                # Google for the first time -- link it rather than
                # re-running allowlist checks against an already-approved
                # account.
                user.google_sub = google_sub
                user.save()

        if user is None:
            institution_ids = [
                institution.id
                for institution in Institution.all()
                if institution.allows_email(email) and institution.id is not None
            ]
            is_admin = _is_bootstrap_admin_email(email)

            if not institution_ids and not is_admin:
                return (
                    {
                        "message": "This account isn't provisioned yet -- "
                        "contact your administrator."
                    },
                    403,
                    default_headers,
                )

            user = User(
                email=email,
                display_name=claims.get("name"),
                institution_ids=institution_ids,
                role=User.Role.Admin if is_admin else User.Role.User,
                google_sub=google_sub,
            ).save()

        session["user_id"] = user.id

        return (
            {
                "user_id": user.id,
                "email": user.email,
                "role": user.role,
                "institutionIds": user.institution_ids,
            },
            200,
            default_headers,
        )
