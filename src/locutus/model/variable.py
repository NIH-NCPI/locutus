from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus.model.terminology import Terminology
from locutus.model.reference import Reference
from locutus import persistence
from locutus.model.terminology import Terminology as Term
from locutus import clean_varname, strip_none

"""
A Variable lives inside a table and doesn't exist as a unit on its own, thus
it has no id property. 

Name:
The name property is whatever the column name is defined to be. For now, 
we are assuming this can be whatever the researcher has chosen and can
contain spaces, capitals etc. 

Description:
This is the descriptive text that often appears inside the data-dictionary 
and can be long enough to convey whatever is needed for a person using the
data must know in order to properly use it. 

Data Type:
This enumeration is necessary in order for the system to properly identify
the type of variable that is being represented/validated/etc. 

"""

from enum import Enum
import typing
from datetime import datetime
from marshmallow.exceptions import ValidationError
from copy import deepcopy

import pdb


class InvalidVariableDefinition(Exception):
    def __init__(self, varname, var_data):
        self.var_name = varname
        self.variable = var_data
        super().__init__(self.message())

    def message(self):
        return f"An issue was found with the variable, {self.var_name}"


class Variable:
    _schema = None
    # Register each of our data_types with their corresponding class for
    # deserialization
    _factory_workers = {}

    class DataType(Enum):
        STRING = 1
        INTEGER = 2  # We'll assume an integer field can have units
        QUANTITY = 3
        DATE = 4
        DATETIME = 5
        BOOLEAN = 6
        ENUMERATION = 7

    def __init__(self, code="", name="", description=""):
        """Default variable type is a basic string"""
        # super().__init__(self, "Variable", self.__class__.__name__)
        self.name = strip_none(name)
        self.code = strip_none(code)
        self.description = strip_none(description)
        self.data_type = None

        if self.code == "" and self.name != "":
            self.code = clean_varname(self.name)

    class _Schema(Schema):
        @post_load
        def build_variable(self, data, **kwargs):
            args = deepcopy(data)
            del args["data_type"]
            return Variable(**args)

    def _validator(self):
        return fields.Str

    def dump(self):
        # pdb.set_trace()
        return self.__class__._get_schema().dump(self)

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls._factory_workers[cls.data_type.name.lower()] = cls

    @classmethod
    def deserialize(cls, data):
        # Find the appropriate class based on data_type and use that do de-
        # serialize the data
        # print(cls._factory_workers)
        vardata = deepcopy(data)
        del vardata["data_type"]
        try:
            return cls._factory_workers[data["data_type"].lower()](**vardata)
        except:
            print(data)
            print("ERROR: An issue was encountered with the following data")
            raise InvalidVariableDefinition(data["name"], data)

    @classmethod
    def _get_schema(cls):
        # pdb.set_trace()
        if cls._schema is None:
            cls._schema = cls._Schema()
            cls._schema._parent = cls
        return cls._schema


class StringVariable(Variable):
    data_type = Variable.DataType.STRING

    def __init__(self, code="", name="", description=None):
        super().__init__(code=code, name=name, description=description)
        self.data_type = Variable.DataType.STRING
        data_type = fields.Enum(Variable.DataType)

    class _Schema(Schema):
        name = fields.Str(required=True)
        code = fields.Str()
        description = fields.Str()
        data_type = fields.Enum(Variable.DataType)


class EnumerationVariable(Variable):
    data_type = Variable.DataType.ENUMERATION

    def __init__(self, code="", name="", description=None, enumerations=None):
        super().__init__(code=code, name=name, description=description)
        self.data_type = Variable.DataType.ENUMERATION
        self.enumerations = Reference(reference=enumerations["reference"])

    def get_mappings(self):
        t = self.get_terminology()
        mappings = t.mappings()

        return mappings

    def get_terminology(self):

        terminology = (
            persistence()
            .collection("Terminology")
            .document(self.enumerations.reference_id())
            .get()
            .to_dict()
        )

        t = Term(**terminology)

        return t

    class _Schema(Schema):
        name = fields.Str(required=True)
        description = fields.Str()
        data_type = fields.Enum(Variable.DataType)
        enumerations = fields.Nested(Reference._Schema)


class BooleanVariable(Variable):
    data_type = Variable.DataType.BOOLEAN

    def __init__(self, name="", description=None):
        super().__init__(name, description)
        self.data_type = Variable.DataType.BOOLEAN

    class _Schema(Schema):
        name = fields.Str(required=True)
        code = fields.Str()
        description = fields.Str()
        data_type = fields.Enum(Variable.DataType)


class DateVariable(Variable):
    data_type = Variable.DataType.DATE

    def __init__(
        self, code="", name="", description=None, date=None, format="YYYY-MM-DD"
    ):
        super().__init__(code=code, name=name, description=description)
        self.data_type = Variable.DataType.DATE
        self.date = datetime.strptime(date, format)
        self.format = format

    class _Schema(Schema):
        name = fields.Str(required=True)
        code = fields.Str()
        description = fields.Str()
        data_type = fields.Enum(Variable.DataType)
        date = fields.Date()
        format = fields.Str()


class DateTimeVariable(Variable):
    data_type = Variable.DataType.DATETIME

    def __init__(
        self,
        code="",
        name="",
        description="",
        datetime=None,
        format="YYYY-MM-DD %H:%M:%S",
    ):
        super().__init__(code=code, name=name, description=description)
        self.data_type = Variable.DataType.DATETIME
        self.datetime = strptime(datetime, format)
        self.format = format

    class _Schema(Schema):
        code = fields.Str()
        name = fields.Str(required=True)
        description = fields.Str()
        data_type = fields.Enum(Variable.DataType)
        datetime = fields.DateTime()
        format = fields.Str()


class QuantityVariable(Variable):
    data_type = Variable.DataType.QUANTITY

    def __init__(
        self, code="", name="", description="", min=None, max=None, units=None
    ):
        super().__init__(code=code, name=name, description=description)
        self.units = units
        self.data_type = Variable.DataType.QUANTITY

        self.min = min
        self.max = max

    class _Schema(Schema):
        code = fields.Str()
        name = fields.Str(required=True)
        description = fields.Str()
        data_type = fields.Enum(Variable.DataType)
        min = fields.Float()
        max = fields.Float()
        units = fields.Str()


class IntegerVariable(Variable):
    data_type = Variable.DataType.INTEGER
    _validation_helper = fields.Number()

    def __init__(
        self, code="", name="", description=None, min=None, max=None, units=None
    ):
        super().__init__(code=code, name=name, description=description)
        self.min = min
        self.max = max
        self.units = units
        self.data_type = Variable.DataType.INTEGER

    class _Schema(Schema):
        name = fields.Str(required=True)
        code = fields.Str()
        description = fields.Str()
        min = fields.Integer()
        max = fields.Integer()
        data_type = fields.Enum(Variable.DataType)
        units = fields.Str()

        @post_load
        def build_intvar(self, data, **kwargs):
            return IntegerVariable(**data)

    def _validator(self):
        return IntegerVariable

    def _serialize(self, value, attr, obj, **kwargs):
        return IntegerVariable._validation_helper._serialize(value, attr, obj, **kwargs)

    def _deserialize(self, value, attr, data, **kwargs) -> typing.Any:
        if not isinstance(value, (int)):
            raise ValidationError(f"Integer expected, but, {value}, was found.")

        if self.min is not None:
            if value < self.min:
                return ValidationError(
                    f"Integer value, {value}, is lower than the specified minimum, {self.min}."
                )

        if self.max is not None:
            if value > self.max:
                return ValidationError(
                    f"Integer value, {value}, is larger than the specified maximum, {self.max}."
                )
        return IntegerVariable._validation_helper._validated(value)
