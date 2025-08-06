from enum import StrEnum
from datetime import datetime
from marshmallow import Schema, fields, post_load
from . import Simple 
from locutus.model.reference import Reference
from locutus import persistence 

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
        timestamp=None
    ):
        super().__init__(
            _id=_id, 
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

        if timestamp is None:
            self.timestamp = datetime.now().strftime(Provenance.PROVENANCE_TIMESTAMP_FORMAT)
        
    @classmethod
    def terminology_provenance(cls, 
                               terminology_id):
        return cls.find(params = {
            "terminology_id": terminology_id,
            "target":  None
        }, sorting="timestamp")
    
    class _Schema(Schema):
        id = fields.Str()
        terminology_id = fields.Str(required=True)
        action = fields.Str(required=True)
        editor = fields.Str(required=True)
        new_value = fields.Str()
        old_value = fields.Str() 
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
        else:
            dref = persistence().collection(self.__class__.__name__).document(self._id)
            t = dref.get().to_dict()

            time_of_delete = dref.delete()
        return t