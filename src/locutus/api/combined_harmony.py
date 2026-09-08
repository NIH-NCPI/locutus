"""Generic Harmony export that allows users to specify one or more IDs to add to a single harmony result"""

import json

from bson import json_util
from flask import g, request
from flask_restful import Resource

from locutus.api import default_headers
from locutus.auth import readable_ids, require_auth
from locutus.model.harmony_export import HarmonyFormat, HarmonyOutputFormat
from locutus.model.study import build_combined_harmony


def _split_ids(raw: str) -> list[str]:
    return [i for i in raw.split(",") if i] if raw else []


class CombinedHarmony(Resource):
    @require_auth
    def get(self):
        data_format = request.args.get("format", "Whistle")
        file_format = request.args.get("file-format", "JSON")
        study_ids = _split_ids(request.args.get("studies", ""))
        dd_ids = _split_ids(request.args.get("datadictionaries", ""))
        table_ids = _split_ids(request.args.get("tables", ""))

        try:
            data_format = HarmonyFormat(data_format)
            file_format = HarmonyOutputFormat(file_format)
        except ValueError as e:
            return {"message_to_user": str(e)}, 400, default_headers

        # M11: silently omit ids current_user can't read (or that don't
        # exist) from the aggregate export, rather than 403ing the whole
        # request over one inaccessible id -- but report what was left out
        # rather than just silently returning a partial result.
        readable_study_ids, omitted_study_ids = readable_ids(
            "Study", study_ids, g.current_user
        )
        readable_dd_ids, omitted_dd_ids = readable_ids(
            "DataDictionary", dd_ids, g.current_user
        )
        readable_table_ids, omitted_table_ids = readable_ids(
            "Table", table_ids, g.current_user
        )

        harmony = build_combined_harmony(
            study_ids=",".join(readable_study_ids),
            dd_ids=",".join(readable_dd_ids),
            table_ids=",".join(readable_table_ids),
            harmony_format=data_format,
            harmony_output_format=file_format,
        )

        omitted = omitted_study_ids + omitted_dd_ids + omitted_table_ids

        return (
            json.loads(json_util.dumps({"harmony": harmony, "omitted": omitted})),
            200,
            default_headers,
        )
