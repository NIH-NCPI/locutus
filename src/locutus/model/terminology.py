from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus import persistence
from locutus.api import delete_collection
from enum import StrEnum  # Adds 3.11 requirement or 3.6+ with StrEnum library
from datetime import datetime
import time

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

    class ChangeType(StrEnum):
        Create = "Create Terminology"
        AddTerm = "Add Term"
        RemoveTerm = "Remove Term"
        EditTerm = "Edit Term"
        AddMapping = "Add Mapping"
        RemoveMapping = "Remove Mapping"
        RemoveAllMappings = "Remove All Mappings"
        EditMapping = "Edit Mapping"
        ApprovalRequested = "Approval Requested"
        Approved = "Approved"
        ApprovalDenied = "Approval Denied"

    class MappingStatus(StrEnum):
        AwaitingApproval = "Awaiting Approval"
        Approved = "Approved"
        Rejected = "Rejected"

    def __init__(
        self,
        id=None,
        name=None,
        url=None,
        description=None,
        codes=None,
        resource_type=None,
        editor=None,
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

                if editor:
                    self.add_provenance(
                        Terminology.ChangeType.AddTerm,
                        editor=editor,
                        target="self",
                        new_value=code,
                    )
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

    def add_code(self, code, display, editor=None, description=None):
        for cc in self.codes:
            if cc.code == code:
                raise CodeAlreadyPresent(code, self.id, cc)

        new_coding = Coding(
            code=code, display=display, system=self.url, description=description
        )
        self.codes.append(new_coding)
        self.save()

        if editor:
            self.add_provenance(
                Terminology.ChangeType.AddTerm,
                editor=editor,
                target="self",
                new_value=code,
            )
            self.add_provenance(
                Terminology.ChangeType.AddTerm,
                editor=editor,
                target=code,
            )

    def remove_code(self, code, editor):
        code_found = False
        for cc in self.codes:
            if cc.code == code:
                self.codes.remove(cc)
                self.delete_mappings(code=code, editor=editor)
                self.save()
                self.add_provenance(
                    Terminology.ChangeType.RemoveTerm,
                    editor=editor,
                    target="self",
                    new_value=code,
                )
                code_found = True
        if not code_found:
            msg = f"The terminology, '{self.name}' ({self.id}), has no code, '{code}'"
            print(msg)
            raise KeyError(msg)

    def rename_code(
        self, original_code, new_code, new_display, editor, new_description=None
    ):
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
                        self.delete_mappings(code=original_code, editor=editor)

                if new_display is not None:
                    code.display = new_display

                if new_description is not None:
                    code.description = new_description

                self.save()
                # avoid using add_provenance if code did NOT change
                self.add_provenance(
                    change_type=Terminology.ChangeType.EditTerm,
                    target=original_code,
                    old_value=original_code,
                    new_value=new_code,
                    editor=editor,
                )
                return True
        return False

    def delete_mappings(self, editor, code=None):
        if code is not None:
            tmref = (
                persistence()
                .collection("Terminology")
                .document(self.id)
                .collection("mappings")
                .document(code)
            )

            mapping = tmref.get().to_dict()
            time_of_delete = 0
            if mapping is not None:
                # This is not super helpful, but at least we get some detail about which mappings were removed
                mapping = ",".join([x["code"] for x in mapping["codes"]])

                time_of_delete = tmref.delete()
                self.add_provenance(
                    change_type=Terminology.ChangeType.RemoveMapping,
                    target=code,
                    old_value=mapping,
                    editor=editor,
                    timestamp=time_of_delete,
                )
            else:
                print(
                    f"Deleting mappings for code, {code}, from Terminology, {self.name} but there were no mappings to be deleted."
                )
            return time_of_delete
        else:
            mapref = (
                persistence()
                .collection("Terminology")
                .document(self.id)
                .collection("mappings")
            )

            mapping_count = delete_collection(mapref)
            self.add_provenance(
                change_type=Terminology.ChangeType.RemoveAllMappings,
                target="self",
                old_value=f"{mapping_count} codes",
                editor=editor,
            )
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

    def get_provenance(self, code=None):
        prov = {}

        if code is None:
            for prv in (
                persistence()
                .collection(self.resource_type)
                .document(self.id)
                .collection("provenance")
                .stream()
            ):

                try:
                    prv = prv.to_dict()

                except:
                    print(
                        "Something other than a dict was encountered for provenance. This is not good."
                    )
                    print(prv)

                id = prv["target"]
                for change in prv["changes"]:
                    if "timestamp" in change:
                        if type(change["timestamp"]) is not str:
                            change["timestamp"] = change["timestamp"].strftime(
                                "%Y-%m-%d %I:%M%p"
                            )
                prov[id] = prv
        else:
            prv = (
                persistence()
                .collection(self.resource_type)
                .document(self.id)
                .collection("provenance")
                .document(code)
                .get()
                .to_dict()
            )
            if prv is not None and prv != {}:
                id = prv["target"]

                prov[id] = prv
                for change in prv["changes"]:
                    if "timestamp" in change:
                        if type(change["timestamp"]) is not str:
                            change["timestamp"] = change["timestamp"].strftime(
                                "%Y-%m-%d %I:%M%p"
                            )
            else:
                prov[code] = []
        # pdb.set_trace()

        return prov

    def add_provenance(
        self, change_type, editor, target=None, timestamp=None, **kwargs
    ):
        if target is None:
            target = "self"
        if timestamp is None:
            timestamp = datetime.now()

        timestamp = timestamp.strftime("%Y-%m-%d %I:%M%p")
        # cur_prov = None
        cur_prov = self.get_provenance(target)[target]
        if cur_prov is None or type(cur_prov) is list:
            cur_prov = {"target": target, "changes": []}

        baseprov = {
            "target": target,
            "timestamp": timestamp,
            "action": change_type,
            "editor": editor,
        }
        prov = {**kwargs, **baseprov}

        try:
            cur_prov["changes"].append(prov)
        except:
            print(f"Current Provenance isn't what we expected: {cur_prov}")
            # pdb.set_trace()

        # pdb.set_trace()

        persistence().collection(self.resource_type).document(self.id).collection(
            "provenance"
        ).document(target).set(cur_prov)

    # def add_provenance(self, code, change_type, old_value, new_value, editor, note="via locutus frontend", timestamp=None):

    def set_mapping(self, code, codings, editor):
        doc = {"code": code, "codes": []}

        new_mappings = []
        for coding in codings:
            doc["codes"].append(coding.to_dict())
            new_mappings.append(doc["codes"][-1]["code"])
        new_mappings = ",".join(new_mappings)

        tmref = (
            persistence()
            .collection(self.resource_type)
            .document(self.id)
            .collection("mappings")
        )

        old_mappings = ""
        try:
            assert code is not None
            mapping = tmref.document(code).get().to_dict()
        except:
            mapping = None
            print(f"weird mapping: {tmref.get()}")
            pdb.set_trace()
        change_type = Terminology.ChangeType.AddMapping
        if mapping is not None:
            # This is not super helpful, but at least we get some detail about which mappings were removed
            old_mappings = ",".join([x["code"] for x in mapping["codes"]])
            change_type = Terminology.ChangeType.EditMapping

        self.add_provenance(
            change_type=change_type,
            target=code,
            old_value=old_mappings,
            new_value=new_mappings,
            editor=editor,
        )

        tmref.document(code).set(doc)

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
