from locutus import persistence
from flask import session
from flask_session import Session
from locutus import logger, get_code_index


class APIError(Exception):
    """
    Base class for all API exceptions.
    """
    def __init__(self, message, details=None, status_code=400):
        self.message = message
        self.details = details or {}
        self.status_code = status_code
        super().__init__(self.message)

    def to_dict(self):
        return {
            "error": self.__class__.__name__,
            "message": self.message
        }

class CodeAlreadyPresent(APIError):
    def __init__(self, code, terminology_id, existing_coding):
        self.code = code
        self.existing_coding = existing_coding
        self.terminology_id = terminology_id
        message = f"The code({self.code}) is already present in the terminology({terminology_id}). The existing display is ({self.existing_coding.display})."
        logger.error(message)
        super().__init__(message, status_code=400)


class CodeNotPresent(APIError):
    def __init__(self, code, terminology_id):
        self.code = code
        self.terminology_id = terminology_id
        code_index = get_code_index(code)
        # More info on code format(code vs code_index) can be found in get_code_index
        message = f"The code {self.code}, or possibly:{code_index}, is not present in the terminology({self.terminology_id})."
        logger.error(message)
        super().__init__(message, status_code=404)

class InvalidEnumValueError(APIError):
    """
    Raised when a value is not in the allowed set of enum values.
    """
    def __init__(self, value, valid_values):
        self.value = value
        self.valid_values = valid_values
        message = f"Value({self.value}) is not valid. The value should be one of:({self.valid_values})"
        logger.error(message)
        super().__init__(message, status_code=400)

class LackingUserID(APIError):
    """
    Raised when neither an editor(body) nor user_id(session) is supplied.
    """
    def __init__(self, editor):
        self.editor = editor
        message = f"This action requires an editor or session! Current editor or user_id: ({self.editor})"
        logger.error(message)
        super().__init__(message, status_code=400)

class LackingRequiredParameter(APIError):
    """
    Raised when a required parameter is missing.
    """
    def __init__(self, param):
        self.param = param
        message = f"This action requires the parameter: '{self.param}'"
        logger.error(message)
        super().__init__(message, status_code=400)