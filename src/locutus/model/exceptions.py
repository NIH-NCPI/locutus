from locutus import persistence


class CodeAlreadyPresent(Exception):
    def __init__(self, code, terminology_id, existing_coding):
        self.code = code
        self.existing_coding = existing_coding
        self.terminology_id = terminology_id

        super().__init__(self.message())

    def message(self):
        return f"The code, {self.code}, is already present in the terminology, {self.terminology_id}. It's current display is '{self.existing_coding.display}"

class CodeNotPresent(Exception):
    def __init__(self, code, terminology_id):
        self.code = code
        self.terminology_id = terminology_id

        super().__init__(self.message())

    def message(self):
        return f"The code, {self.code}, is not present in the terminology, {self.terminology_id}."
    
class InvalidEnumValueError(ValueError):
    """
    Raised when a value is not in the allowed set of enum values.
    """
    def __init__(self, value, valid_values):
        message = f"Value '{value}' is not valid. Expected one of: {valid_values}."
        super().__init__(message)

class LackingUserID(ValueError):
    """
    Raised when neither an editor(body) nor user_id(session) is supplied.
    """
    def __init__(self, editor):
        message = f"This action requires an editor! Editor={editor}"
        super().__init__(message)
