from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus import persistence
from locutus.api import delete_collection
from locutus.model.exceptions import CodeAlreadyPresent, CodeNotPresent
from locutus.model.enumerations import *
from locutus.model.exceptions import *
from enum import StrEnum  # Adds 3.11 requirement or 3.6+ with StrEnum library
from datetime import datetime
from locutus.api import generate_paired_string
import time

from locutus.model.user_input import UserInput
from sessions import SessionManager

import pdb


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
        CreateTable = "Create Table"
        RemoveTable = "Remove Table"
        AddVariables = "Add Variables"
        AddTerm = "Add Term"
        RemoveTerm = "Remove Term"
        EditTerm = "Edit Term"
        AddMapping = "Add Mapping"
        SoftDeleteMapping = "Soft Delete Mapping"
        SoftDeleteAllMappings = "Soft Delete All Mappings"
        EditMapping = "Edit Mapping"
        ApprovalRequested = "Approval Requested"
        Approved = "Approved"
        ApprovalDenied = "Approval Denied"
        ReplacePrefTerm = "Add/Replace Preferred Terminology"
        AddMappingQuality = "Add Mapping Quality"

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

        for codingmapping in mapping["codes"]:
            codes.append(CodingMapping(**codingmapping))

        return codes

    def add_code(self, code, display, description=None, editor=None):
        for cc in self.codes:
            if cc.code == code:
                raise CodeAlreadyPresent(code, self.id, cc)
        new_coding = Coding(
            code=code, display=display, system=self.url, description=description
        )
        self.codes.append(new_coding)
        self.save()

        if editor:
            # This adds provenance to the Terminology/Table itself
            self.add_provenance(
                Terminology.ChangeType.AddTerm,
                editor=editor,
                target="self",
                new_value=code,
            )
            # This adds provenance to the code itself
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
        old_values = []
        new_values = []

        for code in self.codes:
            if code.code == original_code:

                # It's not unreasonable we have only been asked to update the
                # display, so no need to wastefully change all of the details
                # about the code when the end result is the same
                if original_code != new_code:
                    old_values.append(f"code: {original_code}")
                    new_values.append(f"code: {new_code}")
                    code.code = new_code

                    # Since we found a matching code, we'll pull the mappings and
                    # save those under the new code after deleting the old ones.
                    mappings = self.mappings(original_code)
                    if original_code in mappings and mappings[original_code] != []:
                        self.set_mapping(new_code, mappings[original_code], editor=editor)
                        self.delete_mappings(code=original_code, editor=editor)

                if new_display is not None and code.display != new_display:
                    old_values.append(f"display: {code.display}")
                    new_values.append(f"display: {new_display}")
                    code.display = new_display

                if new_description is not None and code.description != new_description:
                    old_values.append(f"description: {code.description}")
                    new_values.append(f"description: {new_description}")
                    code.description = new_description

                old_values = ",".join(old_values)
                new_values = ",".join(new_values)

                self.save()
                if new_values:
                    self.add_provenance(
                        change_type=Terminology.ChangeType.EditTerm,
                        target=original_code,
                        old_value=old_values,
                        new_value=new_values,
                        editor=editor,
                    )
                    self.add_provenance(
                        change_type=Terminology.ChangeType.EditTerm,
                        target="self",
                        old_value=old_values,
                        new_value=new_values,
                        editor=editor,
                    )
                    if original_code != new_code:
                        term_doc = persistence().collection(self.resource_type).document(self.id).collection(
                        "provenance"
                         )
                        prov = term_doc.document(original_code).get().to_dict()
                        prov["target"] = new_code
                        term_doc.document(new_code).set(prov)
                        term_doc.document(original_code).delete()
                    return True
        return False

    def has_code(self, code):
        """Check if a code exists in the terminology.
        
        If the terminology has the code already this will return True
        """

        return any(entry.code == code for entry in self.codes)

    def delete_mappings(self, editor, code=None):
        """
        Soft deletes mappings from a terminology document setting the mapping 
        valid field to false.

        Args:
            editor (str): The ID of the user performing the deletion.
            code (str, optional): The specific mapping code to delete. 

        """
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
                # Iterate over the codes in the mapping and toggle 'valid' to False
                for coding in mapping["codes"]:
                    coding["valid"] = False

                # Save the updated mapping with the 'valid' field set to False
                tmref.set(mapping)

                self.add_provenance(
                    change_type=Terminology.ChangeType.SoftDeleteMapping,
                    target=code,
                    old_value=mapping,
                    editor=editor,
                )
            else:
                print(
                    f"Soft deleting mappings for code, {code}, from Terminology, {self.name} but there were no mappings."
                )
        else:
            mapref = (
                persistence()
                .collection("Terminology")
                .document(self.id)
                .collection("mappings")
            )

            for mapping_doc in mapref.stream():
                mapping = mapping_doc.to_dict()
                for coding in mapping["codes"]:
                    if "valid" in coding:
                        coding["valid"] = False

                # Save the updated mapping
                mapref.document(mapping["code"]).set(mapping)

            self.add_provenance(
                change_type=Terminology.ChangeType.SoftDeleteAllMappings,
                target="self",
                old_value="valid=True",
                new_value="valid=False",
                editor=editor,
            )

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
        for mapping in codings:
            coding_dict = mapping.to_dict()

            # Validation of mapping_relationship

            ftd_terminology = FTDConceptMapTerminology()  
            ftd_terminology.validate_codes_against(coding_dict["mapping_relationship"], additional_enums=[""])

            # Add 'valid' explicitly to the mapping document
            coding_dict['valid'] = True

            doc["codes"].append(coding_dict)
            new_mappings.append(coding_dict["code"])

            for coding_obj in self.codes:
                if coding_obj.code == mapping.code:
                    coding_obj.valid = True

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
            new_value=",".join(new_mappings),
            editor=editor,
        )

        tmref.document(code).set(doc)

    def get_preference(self, code=None):
        pref = {}
        term_pref_id = "self"  # Identifier for terminology preference

        try:
            # If no code is provided, retrieve the terminology preference directly
            if code is None:
                terminology_pref = (
                    persistence()
                    .collection(self.resource_type)
                    .document(self.id)
                    .collection('onto_api_preference')
                    .document(term_pref_id)
                    .get()
                )

                if terminology_pref.exists:
                    pref[term_pref_id] = terminology_pref.to_dict() or {}
                else:
                    # Return an empty object if terminology preference doesn't exist
                    pref[term_pref_id] = {}

            # If a specific code is provided, get the preference
            else:
                prv = (
                    persistence()
                    .collection(self.resource_type)
                    .document(self.id)
                    .collection('onto_api_preference')
                    .document(code)
                    .get()
                )

                if prv.exists:
                    pref[code] = prv.to_dict() or {}
                else:
                    # Fall back to terminology preference if no specific code preference is found
                    pref = self.get_preference()

        except Exception as e:
            print(f"An error occurred while retrieving preferences: {str(e)}")
            raise

        return pref

    def add_or_update_pref(self, api_preference, code=None):
        if code is None:
            code = "self"

        try:
            # get current preferences, default to empty dict
            cur_pref = self.get_preference(code=code).get(code, {})

            # Add or update the preferences for the given API
            cur_pref["api_preference"] = api_preference

            # Save the updated preferences back to the Firestore sub-collection
            persistence().collection(self.resource_type).document(self.id) \
                .collection("onto_api_preference").document(code).set(cur_pref)

        except Exception as e:
            print(f"An error occurred while updating preferences: {e}")
            raise

    def remove_pref(self, code=None):
        if code is None:
            code = "self"

        try:
            # Define the collection reference
            collection_ref = persistence().collection(self.resource_type) \
                .document(self.id).collection("onto_api_preference")

            doc_ref = collection_ref.document(code)
            doc_snapshot = doc_ref.get()

            if doc_snapshot.exists:
                # Delete the document if it exists
                doc_ref.delete()
                message = f"Successfully deleted preferences for code '{code}'."
            else:
                message = f"No preferences found to delete for code '{code}'."

        except Exception as e:
            message = f"An error occurred while deleting preferences for code '{code}': {e}"
            raise

        print(message)

        return message

    def get_preferred_terminology(self):
        """
        Retrieves all references from the 'preferred_terminology' sub-collection

        Returns:
            list: 'references" - An array of `Terminology` reference dictionaries
        
        Example output:
        {
            "references": [
                {
                    "reference": "Terminology/tm--example1"
                },
                {
                    "reference": "Terminology/tm--example2"
                }
            ]
        } 
        """
        try:
            doc_ref = persistence().collection(self.resource_type).document(self.id) \
                .collection("preferred_terminology").document("self")

            doc_snapshot = doc_ref.get()
            if doc_snapshot.exists:
                preferred_terms = doc_snapshot.to_dict().get('references', [])
                return {"references": preferred_terms}
            else:
                # Return an empty list for references if no preferred terminology exists
                return {"references": []}

        except Exception as e:
            print(f"An error occurred while retrieving preferred terminology: {e}")
            raise

    def replace_preferred_terminology(self, editor, preferred_terminology):
        """
        Creates or replaces a document in the 'preferred_terminology' sub-collection

        Args:
            preferred_terminology (list): A dictionary representing the preferred terminology to be added.

        JSON body with two additions example:
        [
            {
                "preferred_terminology": "tm--example1"
            },
            {
                "preferred_terminology": "tm--example2"
            }
        ]
        """
        try:
            # Reference to the sub-collection document named "self"
            doc_ref = persistence().collection(self.resource_type).document(self.id) \
                .collection("preferred_terminology").document("self")

            # Create a list of references based on the provided preferred terminologies
            references = [{"reference": f"Terminology/{item['preferred_terminology']}"} for item in preferred_terminology]

            # Update the document with new combined data
            doc_ref.set({"references": references})

            self.add_provenance(
            Terminology.ChangeType.ReplacePrefTerm,
            target="self",
            new_value=references,
            editor=editor,
            )

        except Exception as e:
            print(f"An error occurred while adding preferred terminology: {e}")
            raise

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

class CodingMapping(Coding):
    """
    Inherits Terminonlogy.Coding. Adds mapping specific attributes.
    Note: Placed here to avoid circular imports. Move only with refactor.
    """

    def __init__(
        self,
        code,
        display=None,
        system=None,
        description="",
        valid=None,
        mapping_relationship=None,
        user_input=None,
    ):
        super().__init__(code, display, system, description)
        self.valid = valid
        self.mapping_relationship = mapping_relationship
        self.user_input = user_input

    class _Schema(Schema):
        code = fields.Str(
            required=True, error_messages={"required": "Codings *must* have a code "}
        )
        display = fields.Str()
        system = fields.URL()
        description = fields.Str()
        valid = fields.Bool()
        mapping_relationship = fields.Str()
        user_input = fields.Dict(keys=fields.Str(), values=fields.Raw())

        @post_load
        def build_coding_mapping(self, data, **kwargs):
            return CodingMapping(**data)

    def to_dict(self):
        """Inherits Terminonlogy.Coding. Adds mapping specific attributes."""
        obj = super().to_dict()

        # Marks the mapping valid if the attribute does not exist in the database
        if self.valid is not None:
            obj["valid"] = self.valid
        else:
            self.valid = True

        # Returns the mapping_relationship as "" if the attribute does not exist in database
        if self.mapping_relationship is not None:
            obj["mapping_relationship"] = self.mapping_relationship
        else:
            obj["mapping_relationship"] = ""

        # Returns the user_input for a mapping if requested
        if self.user_input is not None:
            obj["user_input"] = self.user_input

        return obj


class MappingUserInputModel:
    def generate_mapping_user_input(id, code, mapped_code, user_id):
        """Mappings may have user_input data stored seperate from the mapping itself.
        This function collects and formats the user_input data for a given mapping,
        then creates the user_input object to be included in a CodingMapping.
        """

        document_id = generate_paired_string(code, mapped_code)
        doc_ref = (
            persistence()
            .collection("Terminology")
            .document(id)
            .collection("user_input")
            .document(document_id)
        )

        comments_count = MappingUserInputModel.get_mapping_conversations_counts(doc_ref)
        votes_count = MappingUserInputModel.get_mapping_votes_counts(doc_ref)
        users_vote = MappingUserInputModel.get_users_mapping_vote(doc_ref, user_id)

        return {
            "comments_count": comments_count,
            "votes_count": votes_count,
            "users_vote": users_vote,
        }

    def get_mapping_conversations_counts(doc_ref):
        """Counts the number of mapping_conversation records for a given mapping"""
        document = doc_ref.get()
        if document.exists:
            data = document.to_dict()
            conversations = data.get("mapping_conversations", [])
            return len(conversations)
        return 0

    def get_mapping_votes_counts(doc_ref):
        """Counts up and down votes for a given mapping"""
        document = doc_ref.get()
        if document.exists:
            data = document.to_dict()
            mapping_votes = data.get("mapping_votes", {})
            return {
                "up": sum(
                    1 for vote in mapping_votes.values() if vote.get("vote") == "up"
                ),
                "down": sum(
                    1 for vote in mapping_votes.values() if vote.get("vote") == "down"
                ),
            }
        return {"up": 0, "down": 0}

    def get_users_mapping_vote(doc_ref, user_id):
        """Retrieves the current user's vote for a given mapping. If the user_id
        is not found(no vote exists for the user, or user_id is unknown/None) an
        empty string is returned."""
        document = doc_ref.get()
        if document.exists:
            data = document.to_dict()
            mapping_votes = data.get("mapping_votes", {})
            user_vote = mapping_votes.get(user_id, {}).get("vote")
            return user_vote if user_vote else ""
        return ""
