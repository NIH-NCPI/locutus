# Frontend Auth Guide

This describes how the front end (map-dragon) should log a user in, keep them
logged in, log them out, and what changes about calling the rest of the API
now that every endpoint requires authentication.

## 1. Logging in

Locutus does not implement its own login form or hold a Google client
secret. The front end uses **Google Identity Services (GIS)** directly to
get a signed ID token, then hands that token to Locutus, which verifies it
server-side and starts a session.

1. Load Google's GIS script and get a **Google ID token** for the signed-in
   user (a JWT credential string) using the frontend's own `GOOGLE_CLIENT_ID`.
   This part is entirely between the browser and Google -- Locutus is not
   involved yet.
2. POST that credential to Locutus:

   ```
   POST /api/auth/google
   Content-Type: application/json

   { "credential": "<the Google ID token from GIS>" }
   ```

3. On success (`200`), Locutus:
   - Verifies the token's signature and audience against its own
     server-side `GOOGLE_CLIENT_ID` (must be the same OAuth client as the
     frontend's).
   - Finds or creates the `User`.
   - Sets a session cookie on the response (`Set-Cookie`).
   - Returns the user's profile:

     ```json
     {
       "user_id": "u-abc123",
       "email": "person@example.org",
       "role": "user",
       "institutionIds": ["inst-xyz"]
     }
     ```

   The front end should hang on to this response (see [Section 3](#3-checking-whos-logged-in--rehydrating-after-a-reload)) --
   it's the only place `role`/`institutionIds` are returned.

4. From this point on, the browser sends the session cookie automatically
   on every request to the API (same-origin `fetch`/`XHR` calls do this by
   default; see the CORS note below if the front end is on a different
   origin than the API).

### First-login provisioning

A brand-new Google account is only allowed to create a `User` record if:
- its email is on the `allowedEmails` list of at least one `Institution`
  (exact match, no domain wildcards), **or**
- its email is on the server's separate admin-bootstrap allowlist (used
  only to seed the very first admin).

If neither applies, `POST /api/auth/google` returns:

```
403
{ "message": "This account isn't provisioned yet -- contact your administrator." }
```

The front end should show this message as-is rather than a generic
error -- it's the expected response for "ask an admin to add your email to
an institution," not a bug.

Other failure responses from this endpoint:
- `400` -- request body was missing `credential`.
- `401` -- the Google token didn't verify (expired, wrong audience, tampered)
  or the Google account's email isn't verified.
- `500` -- the server itself isn't configured with a `GOOGLE_CLIENT_ID`
  (an ops/deploy issue, not something the front end can fix).

## 2. Logging out

```
POST /api/session/terminate
```

Clears the session server-side and the cookie. No body required. Safe to
call even when there's no active session (already logged out, expired
server-side, a double-fire from the UI) -- it always returns `200` rather
than erroring, so the front end doesn't need to guard this call on knowing
whether a session is currently active.

## 3. Checking who's logged in / rehydrating after a reload

**There is currently no "whoami" endpoint that returns the full user
profile (`role`, `institutionIds`, `email`) after the fact.** That shape is
only ever returned once, in the `POST /api/auth/google` response.

Until a whoami endpoint exists, the practical options are:
- Cache the login response client-side (e.g. in memory + `sessionStorage`)
  and treat "no cached profile" as logged-out, prompting a fresh Google
  sign-in on reload. This is the simplest option but means a hard refresh
  always re-triggers the Google sign-in flow.
- Ask backend for a small `GET /api/user/me`-style addition if silent
  session resumption (reload without re-prompting Google) is a real
  requirement. Flag this to the backend if you need it -- it's a small,
  contained addition to `locutus/auth.py`'s existing `require_auth`
  machinery.

`GET /api/session/status` does exist, but it predates this auth work and
only returns `{"user_id": ..., "affiliation": ...}` -- no `role` or
`institutionIds`. It's useful only as a cheap "is *any* session active"
check, not for rehydrating a full profile.

## 4. Everything else: what's different now

Previously most endpoints were open. As of this work, **every API endpoint
requires a logged-in caller**, and most also enforce per-resource
permissions:

- **No session (or an expired one) → `401`**
  ```json
  { "message": "Authentication required" }
  ```
  Treat any `401` from any endpoint as "redirect to login," globally --
  e.g. in a shared `fetch` wrapper or Axios/interceptor, rather than
  handling it endpoint-by-endpoint.

- **Logged in, but not allowed to touch that specific resource → `403`**
  ```json
  { "message": "Forbidden" }
  ```
  This means the resource exists but the current user has neither
  ownership nor institution/user-level access to it. Show this as a
  permission error, not a generic failure -- retrying or logging in again
  won't help.

- **Resource genuinely doesn't exist → `404`**, unchanged from before.

### Ownership and visibility

Every Table/Study/Terminology/DataDictionary now carries `owner_id` and
`access` fields, set automatically from the logged-in caller on create --
the frontend never needs to (and can't) set these itself; any `owner_id`/
`access` sent in a POST/PUT body is ignored and overwritten server-side.

A resource's `visibility` determines who besides the owner can see/edit it:
- **Institution** -- shared with the owner's institution, at "editor" or
  "viewer" per user.
- **Restricted** -- shared with specific users, at "editor" or "viewer".
- **Registered** (the default) -- any logged-in user can view; only the
  owner can edit -- **except** a resource with no owner at all (anything
  that predates this work and has never been touched since) is editable by
  any user who belongs to at least one institution, not just the owner.
  There's no way to know which institution a resource like that "belongs"
  to, so any real institution member gets editor rather than the resource
  being locked forever. A logged-in user who isn't a member of any
  institution still only gets view access to these, same as any other
  Registered resource.
- **Public** -- not yet enforced; currently behaves like Registered.

### List endpoints are now filtered, not global

`GET /api/Table`, `/api/Study`, `/api/Terminology`, and
`/api/DataDictionary` still return an array the same shape as before, but
it's now **filtered down to what the logged-in caller can actually see**
(same rule as above) rather than every resource in the system. A user
who owns nothing and isn't a member of any institution with shared
resources may legitimately get back `[]`. This is expected behavior, not
an error state to special-case in the UI.

### PUT-as-create still works the same way

`PUT /api/Table/<id>` (and the Study/Terminology/DataDictionary
equivalents) still create a new resource if `<id>` doesn't exist yet, or
update it if it does -- no change here. The caller becomes the owner on
create, same as `POST`.

## 5. API tokens (probably not needed for the UI itself)

Locutus also supports long-lived **API tokens** (`Authorization: Bearer
lct_...`) as an alternative to the session cookie, meant for scripts and
service-to-service calls rather than the interactive web app. Relevant
only if the UI ever needs to show a "manage your API tokens" settings
page:

- `POST /api/tokens` -- creates a token (`{"name": "...", "expiresAt"?:
  "<ISO 8601>"}` → `{"tokenId": "...", "token": "lct_..."}`). The raw
  token is shown **exactly once**, on creation. This endpoint deliberately
  refuses to work if called using an existing API token (`403`) -- it must
  be called from an active browser session, so a stolen token can't be
  used to mint another one.
- `GET /api/tokens` -- lists the current user's own tokens (metadata only,
  no raw token or hash).
- `DELETE /api/tokens/<id>` -- revokes one of the current user's own
  tokens.

## 6. Known gaps / things to double-check before relying on this

A few things surfaced while wiring this up that may affect the frontend
depending on how it's deployed:

- **Cross-origin (frontend and API on different origins, e.g. a Vite dev
  server on one port talking to Flask on another) needs two things to line
  up on the backend, or every call after login will silently 401.** Both
  are backend config now, not code -- if you're seeing "login succeeds but
  everything after it 401s," this is almost certainly why; ask whoever
  runs the backend locally to check/set these two env vars (a `.env` file
  in the backend's working directory is picked up automatically):
  - `CORS_ALLOWED_ORIGINS` -- comma-separated list of origins allowed to
    make credentialed requests. Defaults to `http://localhost:5173` (Vite's
    default port) if unset -- if the frontend dev server is running on a
    different port or host, this needs to include that exact origin.
  - `SESSION_COOKIE_SAMESITE` -- defaults to `Lax`, which **never** attaches
    the session cookie to a cross-site `fetch()`/XHR call (only to a real
    top-level browser navigation). This is the actual cause of "the login
    response sets a cookie, but the very next API call comes back 401
    anyway" -- for a cross-origin setup this needs to be set to `None` in
    the backend's env. (Requires `Secure` cookies, which the backend
    already sets -- see below.)

  The frontend side of this: send `fetch(..., { credentials: "include" })`
  (or Axios's `withCredentials: true`) on every call, regardless of same-
  or cross-origin. Same-origin production deployments (API and app behind
  the same host) aren't affected by either of the two env vars above.
- **`SESSION_COOKIE_SECURE = True`.** The session cookie is marked
  `Secure`, meaning browsers will only send it over HTTPS. Chrome/Firefox
  treat `http://localhost` specifically (not `127.0.0.1`, not a LAN IP, not
  a custom hostname) as an exception to this, so a same-origin or
  cross-origin dev setup where both sides are literally on `localhost`
  (just different ports) should still work. If login appears to succeed
  but the session doesn't stick and you're not on `localhost`, check this
  next, after `SESSION_COOKIE_SAMESITE` above.
- **`POST /api/session/start` still exists but should not be used.** It
  predates the Google login work and starts a session for whatever
  `user_id` the caller sends, with no credential check at all. It's being
  left in place only because nothing has removed it yet -- don't wire the
  new login flow to it.
- **No whoami endpoint** -- see [Section 3](#3-checking-whos-logged-in--rehydrating-after-a-reload) above.
