# Authorization

Locutus now requires every API request to carry a credential, and enforces
per-resource ownership/institution access on top of that. This page is a
high-level reference for what changed and every endpoint that's new because
of it. For the actual login/session mechanics (how the front end obtains and
sends credentials, cookie behavior, known gaps), see
[Frontend Auth Guide](auth-frontend.md) instead -- this page assumes that
part and focuses on the API surface.

## What changed on every existing endpoint

- **Every endpoint now requires authentication.** A request with no session
  and no API token gets `401`. The one exception is `GET /api/version`
  (health checks can't authenticate).
- **`Study`, `Table`, `Terminology`, and `DataDictionary`** each carry
  `owner_id`, `visibility`, and `access` fields, stamped automatically from
  the caller on create -- any `owner_id`/`access` sent in a request body is
  ignored. A caller without at least read access to a specific resource gets
  `403` (or `404` if it doesn't exist at all -- existence itself isn't
  revealed to a caller who couldn't read it anyway).
- **`GET /api/Table`, `/api/Study`, `/api/Terminology`, `/api/DataDictionary`**
  are filtered to what the caller can actually see, rather than returning
  every resource in the system.
- **`PUT /<Type>/<id>`** (create-or-update) endpoints still work the same
  way, but now require write access on update, and the caller becomes owner
  on create.

See [Frontend Auth Guide](auth-frontend.md#4-everything-else-whats-different-now)
for the visibility levels (Institution/Registered/Public/Restricted) and
what each one means for read vs. write access.

## Login & sessions

Covered in full in [Frontend Auth Guide](auth-frontend.md). Summary:

### https://[APPURL]/api/auth/google
#### POST
Verifies a Google ID token (obtained client-side via Google Identity
Services) and starts a session for the corresponding user. First login for
an email not already provisioned (see below) returns `403`.

### https://[APPURL]/api/session/terminate
#### POST
Logs out -- clears the current session.

### https://[APPURL]/api/session/status
#### GET
Cheap "is any session active" check. Predates this work; doesn't return the
full profile (`role`, `institutionIds`) the way the Google login response
does.

### https://[APPURL]/api/user/me
#### GET
Self-service "who am I" -- returns the identical shape the Google login
response does (`user_id`, `email`, `role`, `institutionIds`), re-fetched
fresh rather than cached. Lets the front end resume a session on reload
(or an API token caller check its own identity) without needing to
re-prompt Google sign-in or decode anything client-side. Works via either
credential path (session cookie or `Authorization: Bearer lct_...`), same
as any other `@require_auth` endpoint.

## API tokens
For CLI/script access instead of a browser session --
`Authorization: Bearer lct_...`.

### https://[APPURL]/api/tokens
#### POST
Creates a token for the current user. Interactive sessions only -- an
existing API token can't be used to mint another one. Body: `{"name": str,
"expiresAt"?: ISO 8601}`. Returns `{"tokenId": str, "token": "lct_..."}` --
the raw token is shown exactly once.

#### GET
Lists the current user's own tokens (metadata only -- never the token or
its hash).

Revoking a token never deletes it. The token is marked with `revokedAt`/
`revokedBy`/`revokeReason` and stops working on its very next request, and
the document is kept so an admin can still see when it was last used.
Revoked tokens drop out of the owner's own `GET /api/tokens` list. Every
revocation is recorded in the [audit log](#audit-log).

Tokens don't expire unless created with `expiresAt`. A revoked token is
kept for `REVOKED_TOKEN_RETENTION_DAYS` (default `365`) after it was
revoked, then Mongo deletes it automatically (a TTL index on `revokedAt`,
set up at startup). `0` keeps revoked tokens forever. The audit log entry
for the revocation is kept either way.

### https://[APPURL]/api/tokens/[id]
#### DELETE
Revokes one of the current user's own tokens. `404` if it doesn't exist,
isn't theirs, or is already revoked.

### https://[APPURL]/api/tokens/revoke
#### POST
Revokes a token by its raw value, whoever owns it -- for any signed-in user
who finds a token somewhere it shouldn't be (a log, a commit, a chat
message). Holding the value is already enough to use the token, so it's
enough to revoke it too. Body: `{"token": "lct_...", "reason"?: str}`.
Always returns the same `200` whether or not anything was revoked, so it
can't be used to test whether a string is a live token. `400` if `token` is
missing.

### https://[APPURL]/api/admin/tokens/[id]
#### DELETE
Admin-only: revokes any user's token (e.g. offboarding). Optional body:
`{"reason": str}`. `404` if it doesn't exist or is already revoked.

### https://[APPURL]/api/admin/users/[id]/tokens
#### GET
Admin-only: lists every token the user has, revoked ones included. Same
fields as `GET /api/tokens`, plus `userId`, `revokedAt`, `revokedBy`, and
`revokeReason` -- never the token or its hash. `404` if the user doesn't
exist.

#### DELETE
Admin-only: revokes all of the user's active tokens. Optional body:
`{"reason": str}`. Returns `{"revoked": int, "tokenIds": [str]}`. Lighter
than [disabling](#httpsappurlapiadminusersiddisable) the account: the user
can still sign in and create new tokens. `404` if the user doesn't exist.

## Institution access on a resource
Any user with write access to a `Study`/`Table`/`Terminology`/
`DataDictionary` can grant or remove another institution's access to it --
not just the owner.

### https://[APPURL]/api/[Study|Table|Terminology|DataDictionary]/[id]/access/institutions/[institution_id]
#### PUT
Adds or updates an institution's role on the resource. Body:
`{"role"?: "editor"|"viewer"}`, defaults to `"editor"`.

#### DELETE
Removes the institution's access to the resource. `404` if it wasn't
already granted.

## Resource visibility
Owner-only -- unlike institution access above, a caller with write access
via an institution grant (not literal ownership) can't change this.

### https://[APPURL]/api/[Study|Table|Terminology|DataDictionary]/[id]/visibility
#### PUT
Sets the resource's visibility. Body: `{"visibility": "Institution"|
"Registered"|"Public"}`. `Restricted` isn't a valid value here -- it's
driven by explicit per-user grants, not a plain toggle.

## Admin: institutions
All endpoints below require the system-level admin role
(`@require_admin`) -- independent of ownership/editor access on individual
resources.

### https://[APPURL]/api/admin/institutions
#### POST
Creates an institution. Body: `{"id"?: str, "name": str, "allowedEmails"?:
[str]}`. `409` if `id` is supplied and already exists (never silently
overwrites). `400` if any `allowedEmails` entry isn't a plausible email
address (a pragmatic "looks like an email" check, not full RFC 5322
validation) -- the whole request is rejected, nothing is partially created.

#### GET
Lists all institutions. Each institution's `memberIds` (raw user ids) is
accompanied by a resolved `members` array -- one entry per id that still
resolves to a real `User` (a stale/deleted id is silently skipped, not
errored on), each shaped `{"id", "email", "displayName", "role",
"lastLoginAt"}`. `lastLoginAt` is `null` for a provisioned account that has
never actually logged in. `memberIds` itself is unchanged -- `members` is
purely additive.

### https://[APPURL]/api/admin/institutions/[id]
#### GET
Fetches one institution by id. Same `members` enrichment as the list
endpoint above.

### https://[APPURL]/api/admin/institutions/[id]/allowlist
Pre-registering emails that are allowed to create an account under this
institution on first Google login.

#### GET
Lists the institution's currently allowed emails.

#### POST
Adds one or more emails. Body: `{"emails": [str]}` (or `{"email": str}` for
a single one). Adding an already-present email is a no-op. `400` if any
entry isn't a plausible email address -- same check and same
reject-the-whole-batch behavior as institution creation above.

### https://[APPURL]/api/admin/institutions/[id]/allowlist/[email]
#### DELETE
Removes one email from the allowlist. `404` if it wasn't on the list. If
that email already has an account, this also revokes the account's access
to this institution -- both the institution's `memberIds` and the user's
own `institutionIds` drop this institution, not just the allowlist entry.

## Admin: users
All endpoints below require the system-level admin role
(`@require_admin`), same as the institution endpoints above. A user
directory independent of any one institution -- `memberIds`/`allowedEmails`
only ever show who belongs to *that* institution, not everyone in the
system.

### https://[APPURL]/api/admin/users
#### GET
Lists every user (`User.to_dict()` -- `id`, `email`, `displayName`,
`institutionIds`, `role`, `googleSub`, `lastLoginAt`, `disabledAt`,
`disabledBy`). Disabled accounts are included, not filtered out, so an
admin can find and re-enable them.

### https://[APPURL]/api/admin/users/[id]
#### GET
Fetches one user by id. `404` if it doesn't exist.

### https://[APPURL]/api/admin/users/[id]/disable
#### POST
Off-boarding without deletion: blocks this account from logging in or
using its existing session/API tokens, but touches nothing else -- owned
resources, provenance, and institution membership (`institutionIds`/
`memberIds`) are all left exactly as they are, intact for historical
reference. Sets `disabledAt`/`disabledBy`; an already-active session or
API token for this account stops working on its very next request, and a
disabled account can't start a fresh session either -- all three fall
through to the same plain `401` an unauthenticated caller gets, not a
distinct "disabled" message. Idempotent. `403` if `id` is the calling
admin's own account -- no admin can lock themselves out with no other
admin available to reverse it. `404` if the user doesn't exist.

### https://[APPURL]/api/admin/users/[id]/enable
#### POST
Reverses a disable -- clears `disabledAt`/`disabledBy`. Idempotent. `404`
if the user doesn't exist.

### https://[APPURL]/api/admin/users/[id]/promote
#### POST
Grants the system-level admin role (`role: "admin"`). Returns the updated
user. Takes effect on that user's very next request, whether they use a
session or an API token -- the role is read from the stored user on every
request, so no re-login is needed. Idempotent. `404` if the user doesn't
exist.

### https://[APPURL]/api/admin/users/[id]/demote
#### POST
Returns an admin to the normal user role (`role: "user"`). Returns the
updated user. Like promotion, it takes effect on that user's very next
request. Idempotent. `403` if `id` is the calling admin's own account --
since an admin can't demote themselves, the system can never be left
without an admin. `404` if the user doesn't exist.

Disable, enable, promote, and demote each accept an optional body of
`{"reason": str}` and are recorded in the audit log below. A request that's
rejected (`403`/`404`) isn't recorded.

## Audit log

### https://[APPURL]/api/admin/audit
#### GET
Admin-only: who disabled, enabled, promoted, or demoted an account, and who
revoked which API tokens, newest first. Each event is `{"id", "at",
"action", "actorId", "targetUserId", "targetTokenIds", "reason"}`, where
`action` is one of `user.disable`, `user.enable`, `user.promote`,
`user.demote`, `token.revoke` (one token, by its owner or an admin),
`token.revoke_all`, or `token.revoke_by_value`. Optional query params:
`userId` (matches the user as either actor or target), `action`, and
`limit` (default 100, max 1000). `400` for an unknown `action` or a bad
`limit`.

## Responding to a suspect token or account

| Situation | Response |
|---|---|
| One token is exposed (pasted in a log, chat, or commit) | Anyone signed in: `POST /api/tokens/revoke` with the value. An admin who knows the id: `DELETE /api/admin/tokens/[id]`. |
| A user's machine is lost or all their tokens are suspect | Admin: `DELETE /api/admin/users/[id]/tokens`. Their browser sign-in keeps working. |
| The account itself is compromised, or the person has left | Admin: `POST /api/admin/users/[id]/disable`. Ends sessions and tokens and blocks sign-in. |
| Something system-wide (e.g. the session secret leaked) | No endpoint; see below. |

`GET /api/admin/users/[id]/tokens` shows each token's `lastUsedAt`, and
`GET /api/admin/audit?userId=[id]` shows what's been done to the account
so far.

For a system-wide emergency, act on the database directly. In `mongosh`
against the locutus database:

```js
// End every browser session (everyone has to sign in again).
db.sessions.deleteMany({})

// Revoke every API token.
db.ApiToken.updateMany(
  { revokedAt: null },
  { $set: { revokedAt: new Date(), revokedBy: "emergency", revokeReason: "global revoke" } }
)
```

The app's `SECRET_KEY` is generated fresh each time it starts (see
`locutus/sessions.py`), so restarting it also rotates that.

### Future work: where a change came from

When cleaning up after a suspect token, `lastUsedAt` shows only its most
recent use, and provenance records the user behind a change but not how
it was made. You can list everything a user changed between a suspected
leak and the revocation, but you can't separate what the token did from
the person's own edits in the browser. Recording the source on each
provenance entry -- the web app, a direct API call, Talon, and so on, plus
the token id when the request came in with a token -- would make that
exact. Request identity already knows whether a token was used, so most
of the work is threading it through to everywhere provenance is written,
and having clients like Talon identify themselves (e.g. a `User-Agent` or
custom header).

## Aggregate/export endpoints

### https://[APPURL]/api/harmony?[params]
#### GET
**Response shape changed.** Previously a bare list; now
`{"harmony": [...], "omitted": [...]}`. Resources the caller can't read (or
that don't exist) are silently left out of `harmony` rather than 403ing the
whole request, and their ids are reported back in `omitted` so the caller
knows what to go request access to. See [Harmony File End Points](harmony.md)
for the rest of this endpoint's params and output format, which are
unchanged.

### https://[APPURL]/api/SideLoad
#### POST
Unchanged request/response shape, but now collects every distinct
`table_id` referenced in the uploaded CSV and requires write access to all
of them -- `403` with the list of inaccessible ids before writing anything,
rather than partially applying the batch. See [Side Load](sideload.md) for
the CSV format itself.
