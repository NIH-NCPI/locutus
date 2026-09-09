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

### https://[APPURL]/api/tokens/[id]
#### DELETE
Revokes one of the current user's own tokens.

### https://[APPURL]/api/admin/tokens/[id]
#### DELETE
Admin-only: revokes any user's token (e.g. offboarding).

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
overwrites).

#### GET
Lists all institutions.

### https://[APPURL]/api/admin/institutions/[id]
#### GET
Fetches one institution by id.

### https://[APPURL]/api/admin/institutions/[id]/allowlist
Pre-registering emails that are allowed to create an account under this
institution on first Google login.

#### GET
Lists the institution's currently allowed emails.

#### POST
Adds one or more emails. Body: `{"emails": [str]}` (or `{"email": str}` for
a single one). Adding an already-present email is a no-op.

### https://[APPURL]/api/admin/institutions/[id]/allowlist/[email]
#### DELETE
Removes one email from the allowlist. `404` if it wasn't on the list.

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
