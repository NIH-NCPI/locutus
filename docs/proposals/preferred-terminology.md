# Preferred Terminology Updates

## Overview and Goals

When updating locutus to require Curies for all mappings, we overlooked those
codes that come from locutus itself through "Preferred Terminologies". These are
terminologies that are loaded directly into Locutus and can be assigned like any
other code inside MapDragon despite having no presence inside those search APIs.

One of the big changes we recently implemented involved routing all mapped codes
through a process that uses curated systems and prefixes to ensure consistency
throughout all of map-dragon. This requires all terminologies that are going to
be saved have presence inside a curated CSV. Because Preferred Ontologies are
user defined, that creates real issues for the process, since those users should
have zero access to change that file.

### Goals

- Locutus must be able to identify all potential "Preferred Terminologies".
- Locutus must be able to apply suitable prefixes to codes if the codes aren't
  Curies themselves.
- Locutus should provide the front-end with a list of Curie prefixes in use (and
  what they mean) so that users safely assign prefixes to their terminologies.
- These new prefix/systems must be integrated into the vocabulary knowledge to
  ensure they are correctly integrated into the rest of the system

## Backend Design

### Prefix Definitions

The backend should provide a dump of all valid prefixes recognized by the system
along with any relevant metadata associated with the prefix. These include our
curated vocabulary list, the legacy search based list as well as all
prefix/terminologies from "preferred terminologies":

- prefix
- Vocabulary Name
- FHIR System
- URI
- known synonyms

For Preferred Terminologies, we will be able to generate the URI based on the
application's URL/Terminology/ID or something along those lines. Preferred
Terminologies will have no synomyms.

#### API Endpoint

##### GET /api/prefixes

Returns all valid prefixes, both from the official curated vocabulary entries as
well as the local "preferred terminology" entries.

##### GET /api/prefixes/lookup?prefix={}

Returns the prefix(es) associated with a preferred prefix or a synonym. While
each should be unique, it is not impossible to imagine that there are some
synonyms that not unique to a single vocabulary.

### Expanded Terminology Class

Expand Terminology definition to include two new properties:

- is_preferable: bool = False
- prefix: str = ""

By default, terminologies will not be "preferreable" and will not be allowed to
be assigned as a mapping. However, if the terminology.is_preferable is True, it
MUST have a unique prefix.

To enable these user defined terminologies, we must be able to identify all
terminologies that are deemed suitable for use as Preferred Ontologies. In
addition to the finding them, users must also be able to provide prefixes for
the codes or the terminology as a whole.

When locutus recieves codes from sideloads and the front-end, these prefixes and
systems will be considered alongside the official vocabulary sources and will be
permitted as suitable mappings.

## Front-End Design

Terminology New (load) and Edit Changes:

- Checkbox "Is Preferable", defaults to False for new
- Prefix (required if Is Preferable is checked). Fails validation at the
  front-end if the prefix matches any existing prefix. And then, again at the
  backend if the prefix is no longer available by the time it was recieved at
  the backend.

Prefix can not be changed once it has been saved. So, if the user is editing
something that was previously defined without one (because it was not "Is
Preferable") it can be assigned. Otherwise, it should be shown but not editable.

## Open Questions

### Terminologies as Valuesets

Do we want to have the ability to assign full Curies to a code inside one of
these terminologies? If so, we need to allow users to also define arbitrary
prefix -> vocabulary entries to support codes from vocabularies that aren't
currently recognized by the system

The backend would need to identify any "prefixes" encountered in codes against
recognized prefixes (including existing vocabulary prefixes/synonyms/and user
defined ones) and skip appending the terminology's prefix upon delivery.

### Prefix conflicts

By default, we prevent conflicts when a user tries to use an existing prefix.
However, if they choose a prefix that is currently available but is actually the
preferred prefix for a vocabulary we one day wish to integrate. How do we handle
that?

One option might be to require all Preferred Terminologies start with MD_ or
something along those lines.
