from enum import StrEnum


class Visibility(StrEnum):
    """Who can read a resource by default, absent an explicit owner/access
    grant (see the Auth Requirements spec, M4/M5). Acts as a switch, not a
    stacked set of checks -- exactly one of these governs a given resource:

    Public: any requester, including unauthenticated ones. Not enforced
        this release (see W3) -- included now so the schema doesn't need a
        migration when it is.
    Registered: any authenticated user, regardless of institution. This is
        what "visibility" meant before this enum existed, and remains the
        default for both new documents and ones saved before M4 shipped.
    Institution: checked against the resource's access.institutions map.
    Restricted: checked against the resource's access.users map.
    """

    Public = "Public"
    Registered = "Registered"
    Institution = "Institution"
    Restricted = "Restricted"
