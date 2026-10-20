from typing import ClassVar

from marshmallow import Schema, fields, post_load
from term_wyrm.apis import available_apis

from locutus.model.exceptions import InvalidValueError


class OntoApiPreference:
    available_apis: ClassVar[set] = set(available_apis())

    def __init__(self, preferences=None):

        if preferences is None:
            preferences = {"api_preference": {}}

        for k in preferences:
            if k not in OntoApiPreference.available_apis:
                raise InvalidValueError(
                    k, valid_values=sorted(OntoApiPreference.available_apis)
                )
        self.api_preference = preferences

    def set_preference(self, api, preferences):
        self.api_preference[api] = preferences
        print(self.api_preference)

    def reset(self):
        self.api_preference = {}

    class _Schema(Schema):
        api_preference = fields.Dict(
            keys=fields.Str(), values=fields.List(fields.Str())
        )

        @post_load
        def build_coding(self, data, **kwargs):
            return OntoApiPreference(**data)

    def to_dict(self):
        return self.__class__._Schema().dump(self)
