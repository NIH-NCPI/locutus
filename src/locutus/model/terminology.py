from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus import persistence
from locutus.api import delete_collection

import pdb


class CodeAlreadyPresent(Exception):
    def __init__(self, code, terminology_id, existing_coding):
        self.code = code
        self.existing_coding = existing_coding
        self.terminology_id = terminology_id

        super().__init__(self.message())

    def message(self):
        return f"The code, {self.code}, is already present in the terminology, {self.terminology_id}. It's current display is '{self.existing_coding.display}"


"""
A terminology exists on its own within the project but can be referenced by 
variables as part of their data-type construction. 

Id:
This should be generated by the system, but can be provided by the user. 

Name:
A Human friendly name associated with the terminology. 

URL:
The terminology's "system" identifier. 

Description:
An optional block of text that is used to provide context for understanding the
terminology's purpose.

Codes:
(Currently, a List) of Codings. Each coding is defined within the scope of the 
terminology's "codes" property. Codings should not appear more than once inside
the "codes" array. 
"""


class Coding:
    def __init__(self, code, display="", system=None, description=""):
        self.code = code
        self.display = display
        self.system = system
        self.description = description

    class _Schema(Schema):
        code = fields.Str(
            required=True, error_messages={"required": "Codings *must* have a code "}
        )
        display = fields.Str()
        system = fields.URL()
        description = fields.Str()

        @post_load
        def build_code(self, data, **kwargs):
            # pdb.set_trace()
            return Coding(**data)

    def to_dict(self):
        obj = {"code": self.code, "display": self.display}

        if self.description != "":
            obj["description"] = self.description

        if self.system is not None:
            obj["system"] = self.system

        return obj


class Terminology(Serializable):
    _id_prefix = "tm"

    def __init__(
        self,
        id=None,
        name=None,
        url=None,
        description=None,
        codes=None,
        resource_type=None,
    ):
        super().__init__(
            id=id, collection_type="Terminology", resource_type="Terminology"
        )
        self.id = id
        self.name = name
        self.description = description
        self.url = url
        self.codes = []

        # pdb.set_trace()

        # This probably doesn't make sense, stashing the system in at this
        # point, but we'll trust knuth for the time being and fix it when it is
        # clear that it is a bad idea.
        if codes is not None:
            for code in codes:
                if type(code) is dict:
                    code = Coding(**code)
                # print(code)
                code.system = self.url
                self.codes.append(code)

        super().identify()

    def keys(self):
        return [self.url, self.name]

    def build_code_dict(self):
        codings = {}
        for code in self.codes:
            codings[code.code] = code

        return codings

    def build_code_list(mapping):
        codes = []
        code_id = mapping["code"]

        for coding in mapping["codes"]:
            codes.append(Coding(**coding))

        return codes

    def add_code(self, code, display, description=None):

        for cc in self.codes:
            if cc.code == code:
                raise CodeAlreadyPresent(code, self.id, cc)

        new_coding = Coding(
            code=code, display=display, system=self.url, description=description
        )
        self.codes.append(new_coding)
        self.save()

    def remove_code(self, code):
        code_found = False
        for cc in self.codes:
            if cc.code == code:
                self.codes.remove(cc)
                self.delete_mappings(code)
                self.save()
                code_found = True
        if not code_found:
            msg = f"The terminology, '{self.name}' ({self.id}), has no code, '{code}'"
            print(msg)
            raise KeyError(msg)

    def rename_code(self, original_code, new_code, new_display, new_description=""):
        status = 200

        print(
            f"Renaming Code, {original_code} to {new_code} with new display: {new_display} and new description: {new_description}"
        )
        for code in self.codes:
            if code.code == original_code:

                # It's not unreasonable we have only been asked to update the
                # display, so no need to wastefully change all of the details
                # about the code when the end result is the same
                if original_code != new_code:
                    code.code = new_code

                    # Since we found a matching code, we'll pull the mappings and
                    # save those under the new code after deleting the old ones.
                    mappings = self.mappings(original_code)
                    if original_code in mappings and mappings[original_code] != []:
                        self.set_mapping(new_code, mappings[original_code])
                        self.delete_mappings(original_code)

                if new_display is not None:
                    code.display = new_display

                if new_description != "":
                    code.description = new_description
                self.save()
                return True
        return False

    def delete_mappings(self, code=None):
        if code is not None:
            tmref = (
                persistence()
                .collection("Terminology")
                .document(self.id)
                .collection("mappings")
                .document(code)
            )
            print(f"Deleting mappings for code, {code}, from Terminology, {self.name}")
            time_of_delete = tmref.delete()
            return time_of_delete
        else:
            mapref = (
                persistence()
                .collection("Terminology")
                .document(self.id)
                .collection("mappings")
            )
            print(f"Deleting all mappings for Terminology, {self.name} ")
            mapping_count = delete_collection(mapref)
            return mapping_count

    def mappings(self, code=None):
        codes = {}
        if code is None:
            for mapping in (
                persistence()
                .collection(self.resource_type)
                .document(self.id)
                .collection("mappings")
                .stream()
            ):
                mapping = mapping.to_dict()

                code_id = mapping["code"]
                codes[code_id] = Terminology.build_code_list(mapping)

        else:
            mapping = (
                persistence()
                .collection(self.resource_type)
                .document(self.id)
                .collection("mappings")
                .document(code)
                .get()
                .to_dict()
            )
            if mapping is not None:
                code_id = mapping["code"]
                codes[code_id] = Terminology.build_code_list(mapping)
            else:
                codes[code] = []

        return codes

    def set_mapping(self, code, codings):
        doc = {"code": code, "codes": []}

        for coding in codings:
            doc["codes"].append(coding.to_dict())

        persistence().collection(self.resource_type).document(self.id).collection(
            "mappings"
        ).document(code).set(doc)

    class _Schema(Schema):
        id = fields.Str()
        name = fields.Str(required=True)
        url = fields.URL(required=True)
        description = fields.Str()
        codes = fields.List(fields.Nested(Coding._Schema))
        resource_type = fields.Str()

        @post_load
        def build_terminology(self, data, **kwargs):
            return Terminology(**data)


"""
_term_data = {
    1: Terminology(
        name="Race",
        url="https://includedcc.org/fhir/CodeSystem/data-dictionary/participant/race",
        description="Race of Participant",
        codes=[
            Coding(code="American Indian or Alaska Native"),
            Coding(code="Asian"),
            Coding(code="Black or African American"),
            Coding(code="More than one race"),
            Coding(code="Native Hawaiian or Other Pacific Islander"),
            Coding(code="Other"),
            Coding(code="White"),
            Coding(code="Prefer not to answer"),
            Coding(code="Unknown"),
            Coding(code="East Asian"),
            Coding(code="Latin American"),
            Coding(code="Middle Eastern or North African"),
            Coding(code="South Asian"),
        ],
    ),
    2: Terminology(
        name="Sex",
        url="https://includedcc.org/fhir/CodeSystem/data-dictionary/participant/sex",
        description="Sex of Participant",
        codes=[
            Coding(code="Female"),
            Coding(code="Male"),
            Coding(code="Other"),
            Coding(code="Unknown"),
        ],
    ),
    3: Terminology(
        name="Family Relationship",
        url="https://includedcc.org/fhir/CodeSystem/data-dictionary/participant/family_relationship",
        description="Relationship of Participant to proband",
        codes=[
            Coding(code="Proband"),
            Coding(code="Father"),
            Coding(code="Mother"),
            Coding(code="Sibling"),
            Coding(code="Other relative"),
            Coding(code="Unrelated control"),
        ],
    ),
}


def terminologies(id=None):
    if id is None:
        terms = [v for k, v in _term_data.items()]
        return terms
    return _term_data[id]
"""
