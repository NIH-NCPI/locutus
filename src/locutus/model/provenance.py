from enum import StrEnum
from datetime import datetime
from marshmallow import Schema, fields, post_load
from .simple import Simple 
from locutus.model.reference import Reference
import locutus
import pdb


class DictOrStringField(fields.Field):
    def _serialize(self, value, attr, obj, **kwargs):
        if value is None:
            return ""
        if isinstance(value, dict):
            # Serialize dictionary as needed
            return value
        elif isinstance(value, str):
            # Serialize string as needed
            return value
        else:
            raise TypeError("Field must be a dictionary or a string.")

    def _deserialize(self, value, attr, data, **kwargs):
        if isinstance(value, dict):
            # Deserialize dictionary as needed
            return value
        elif isinstance(value, str):
            # Deserialize string as needed
            return value
        else:
            raise TypeError("Field must be a dictionary or a string.")

class Provenance(Simple):
    PROVENANCE_TIMESTAMP_FORMAT = "%Y-%m-%d %I:%M:%S.%f%p"

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
        RemovePrefTerm = "Remove Preffered Terminology"
        AddMappingQuality = "Add Mapping Quality"

    def __init__(
        self, 
        terminology_id, 
        _id=None, 
        id=None,
        action=None,
        editor=None,
        new_value=None,
        old_value=None,
        target=None,
        timestamp=None,
        valid=True
    ):
        super().__init__(
            _id=_id, 
            id=id,
            collection_type="Provenance",
            resource_type="Provenance"
        )
        self.terminology_id = terminology_id 
        self.action = action 
        self.editor = editor 
        self.new_value = new_value 
        self.old_value = old_value 
        self.target = target 
        self.timestamp = timestamp 
        self.valid = valid

        if timestamp is None:
            self.timestamp = datetime.now().strftime(Provenance.PROVENANCE_TIMESTAMP_FORMAT)
    
    @classmethod 
    def add_terminology_provenance(cls, 
                                   terminology_id, 
                                   action,
                                   editor,
                                   old_value=None,
                                   new_value=None,
                                   timestamp=None):
        p = cls(terminology_id=terminology_id, 
                action=action, 
                target=None,
                editor=editor,
                old_value=old_value,
                new_value=new_value,
                timestamp=timestamp,
                valid=True)
        p.save()
        return p

    @classmethod 
    def exists_in_db(cls, 
                    terminology_id,
                    target=None,
                    return_instance=True):
        # This doesn't conform to the always overwrite concept
        return None

    @classmethod
    def terminology_provenance(cls, 
                               terminology_id,
                               valid_only=True):
        params = {
            "terminology_id": terminology_id,
            "target":  None,
            }
        if valid_only:
            params['valid'] = True
        return cls.find(params=params , 
            return_instance=False, sorting="timestamp")

    @classmethod
    def index_list(cls):
        "For codings, we must have either a terminology or system and the code"
        return [
            [("terminology_id", 1), ("target", 1), ("timestamp", 1), ("valid", 1)],
            [("terminology_id", 1), ("timestamp", 1), ("valid", 1)],
        ]

    @classmethod 
    def add_mapping_provenance(cls, 
                               terminology_id, 
                               target_coding,
                               action,
                               editor,
                               old_value=None,
                               new_value=None,
                               timestamp=None):
        p = cls(terminology_id=terminology_id, 
                action=action, 
                target=target_coding,
                editor=editor,
                old_value=old_value,
                new_value=new_value,
                timestamp=timestamp,
                valid=True)
        p.save()
        return p

    @classmethod 
    def mapping_provenance(cls, 
                           terminology_id,
                           target_coding,
                           valid_only=True,
                           return_instance=False):
        params = {
            "terminology_id": terminology_id,
            "target":  target_coding,
            }

        if valid_only:
            params['valid'] = True

        return cls.find(params=params , 
            return_instance=return_instance, sorting="timestamp")

    class _Schema(Schema):
        id = fields.Str()
        terminology_id = fields.Str(required=True)
        action = fields.Str(required=True)
        editor = fields.Str(required=True)
        new_value = fields.Str()
        old_value = DictOrStringField() 
        timestamp = fields.Str()
        # timestamp = fields.DateTime(format=PROVENANCE_TIMESTAMP_FORMAT)
        valid = fields.Bool()

        target = fields.Str()

        @post_load 
        def build_provenance(self, data, **kwargs):
            return Provenance(**data)


    def delete(self, hard_delete=True):
        if not hard_delete:
            self.valid = False 
            self.save()
            t = self.dump()
        else:
            dref = locutus.persistence().collection(self.__class__.__name__).document(self._id)
            t = dref.get().to_dict()

            time_of_delete = dref.delete()
        return t
    
