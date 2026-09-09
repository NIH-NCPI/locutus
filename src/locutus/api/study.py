import json

from bson import json_util
from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import (
    VALID_INSTITUTION_ROLES,
    VALID_VISIBILITY_TOGGLES,
    filter_readable,
    new_resource_access_fields,
    remove_institution_access,
    require_auth,
    require_read_access,
    require_write_access,
    require_write_access_or_create,
    set_institution_access,
    set_visibility,
)
from locutus.model.harmony_export import HarmonyFormat, HarmonyOutputFormat
from locutus.model.study import Study as mStudyTerm
from locutus.model.visibility import Visibility


class Studies(Resource):
    @require_auth
    def get(self):
        studies = filter_readable(mStudyTerm.get(return_instance=False), g.current_user)
        return (json.loads(json_util.dumps(studies)), 200, default_headers)

    @require_auth
    def post(self):
        sty = request.get_json()
        if "resource_type" in sty:
            del sty["resource_type"]

        return_code = 201
        msg = ""

        if "title" not in sty:
            return_code = 400
            msg = "Study Title Required"

        if "name" not in sty:
            return_code = 400
            msg = "Study Name Required"

        if return_code > 399:
            return msg, return_code, default_headers

        # owner_id/access are always derived from the authenticated caller,
        # never trusted from the request body (M4).
        sty.update(new_resource_access_fields(g.current_user))

        study = mStudyTerm(**sty)
        study.save()
        return json.loads(json_util.dumps(study.dump())), 201, default_headers

    def delete_dd_references(self, id):
        affected_ids = 0

        for study in mStudyTerm.get(return_instance=True):
            matched_references = study.remove_dd(id)

            if matched_references > 0:
                study.save()
                affected_ids += matched_references

        return affected_ids


class Study(Resource):
    @require_read_access("Study", "id")
    def get(self, id: str):
        # require_read_access already confirmed this id exists.
        study = mStudyTerm.get(id)
        assert study is not None
        return json.loads(json_util.dumps(study.dump())), 200, default_headers

    @require_write_access_or_create("Study", "id")
    def put(self, id: str):
        sty = request.get_json()
        if "id" not in sty:
            sty["id"] = id

        if "resource_type" in sty:
            del sty["resource_type"]

        # PUT fully replaces the object from the request body, so
        # owner_id/access must be resolved explicitly rather than trusted
        # from the client either way: preserve the existing resource's
        # values on an update, or stamp fresh ones from the authenticated
        # caller if this PUT is actually creating a new study at this id
        # (require_write_access_or_create already confirmed either is
        # allowed before this handler runs).
        existing = mStudyTerm.get(id, return_instance=False)
        if existing is not None:
            sty["owner_id"] = existing.get("owner_id")
            sty["access"] = existing.get("access")
        else:
            sty.update(new_resource_access_fields(g.current_user))

        study = mStudyTerm(**sty)
        study.save()
        return json.loads(json_util.dumps(study.dump())), 201, default_headers

    @require_write_access("Study", "id")
    def delete(self, id: str):
        # require_write_access already confirmed this id exists.
        study = mStudyTerm.get(id)
        assert study is not None
        t = study.dump()
        study.delete()

        return json.loads(json_util.dumps(t)), 200, default_headers


class StudyEdit(Resource):
    @require_write_access("Study", "id")
    def delete(self, id: str, dd_id: str):
        # require_write_access already confirmed this id exists.
        study = mStudyTerm.get(id)
        assert study is not None
        count = study.remove_dd(dd_id)
        if count < 1:
            return (
                f"{dd_id} id is not found in Study, {study.name}.",
                404,
                default_headers,
            )
        study.save()
        return json.loads(json_util.dumps(study.dump())), 200, default_headers


class StudyInstitutionAccess(Resource):
    """S1: any editor (not just the owner) can add or remove an
    institution's access to this study."""

    @require_write_access("Study", "id")
    def put(self, id: str, institution_id: str):
        body = request.get_json(silent=True) or {}
        role = body.get("role", "editor")
        if role not in VALID_INSTITUTION_ROLES:
            return (
                {"message": f"role must be one of {VALID_INSTITUTION_ROLES}"},
                400,
                default_headers,
            )

        resource = set_institution_access("Study", id, institution_id, role)
        return json.loads(json_util.dumps(resource)), 200, default_headers

    @require_write_access("Study", "id")
    def delete(self, id: str, institution_id: str):
        if not remove_institution_access("Study", id, institution_id):
            return (
                {"message": f"{institution_id} does not have access to this study"},
                404,
                default_headers,
            )

        # require_write_access already confirmed this id exists.
        study = mStudyTerm.get(id, return_instance=False)
        assert study is not None
        return json.loads(json_util.dumps(study)), 200, default_headers


class StudyVisibility(Resource):
    """S2: owner-only toggle of this study's visibility."""

    @require_write_access("Study", "id")
    def put(self, id: str):
        body = request.get_json(silent=True) or {}
        visibility = body.get("visibility")
        if visibility not in [v.value for v in VALID_VISIBILITY_TOGGLES]:
            return (
                {
                    "message": f"visibility must be one of {[v.value for v in VALID_VISIBILITY_TOGGLES]}"
                },
                400,
                default_headers,
            )

        # require_write_access only confirms editor access -- S2 is
        # stricter than that: owner only.
        resource = mStudyTerm.get(id, return_instance=False)
        assert resource is not None
        if resource.get("owner_id") != g.current_user["user_id"]:
            return (
                {"message": "Only the owner can change a resource's visibility"},
                403,
                default_headers,
            )

        updated = set_visibility("Study", id, Visibility(visibility))
        return json.loads(json_util.dumps(updated)), 200, default_headers


class StudyHarmony(Resource):
    @require_read_access("Study", "id")
    def get(self, id: str):
        data_format = request.args.get("format", "Whistle")
        file_format = request.args.get("file-format", "JSON")

        try:
            data_format = HarmonyFormat(data_format)
            file_format = HarmonyOutputFormat(file_format)
        except ValueError as e:
            return {"message_to_user": str(e)}, 400, default_headers

        print("Exporting Study Harmony: ")
        print(f"Harmony format: {data_format}")
        print(f"File format: {file_format}")
        # require_read_access already confirmed this id exists.
        t = mStudyTerm.get(id)
        assert t is not None

        try:
            harmony = t.as_harmony(
                harmony_format=data_format, harmony_output_format=file_format
            )
        except KeyError as e:
            return {"message_to_user": str(e)}, 400, default_headers
        return json.loads(json_util.dumps(harmony)), 200, default_headers
