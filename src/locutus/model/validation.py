from locutus.model.exceptions import *


def validate_enums(codes, enums, additional_enums=None):
    """
    Validates that codes are within the provided enums or additional enums.

    :param codes: The codes to validate. Can be a dict, list, or string.
    :param enums: The valid enums. Can be a dict, list, or string.
    :param additional_enums: Additional enums to consider as valid. Should be a list or iterable.
    :raises InvalidValueError: If any code is not in the valid enums.
    """
    # Normalize enums
    if isinstance(enums, dict):
        valid_enums = enums.get("code", [])
    elif isinstance(enums, list):
        valid_enums = enums
    elif isinstance(enums, str):
        valid_enums = [enums]
    else:
        raise TypeError("Enums must be a dict, list, or string.")

    # Allow additional enums if provided
    if additional_enums:
        valid_enums += list(additional_enums)

    # Normalize codes
    if isinstance(codes, dict):  # Assuming Coding or CodingMapping object
        code_list = [entry.get("code") for entry in codes.values()]
    elif isinstance(codes, list):
        code_list = codes
    elif isinstance(codes, str):
        code_list = [codes]
    else:
        raise TypeError(f"Codes, {codes}, must be a dict, list, or string.")

    # Validate each code
    invalid_codes = [code for code in code_list if code not in valid_enums]
    if invalid_codes:
        raise InvalidValueError(invalid_codes, valid_enums)

    return True
