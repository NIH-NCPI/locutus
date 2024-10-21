"""
Classes define user input such as comments/notes, and up/down votes.

Current Use:
 * Terminology Mappings (Terminology sub-collection user_input)
    - Mapping conversations: user comments regarding a single mapping
    - Mapping votes: users up/down vote regarding a single mapping

"""
from marshmallow import Schema, fields, post_load
from locutus import persistence

from sessions import SessionManager

USER_INPUT_CHAR_LIMIT = 1000

class UserInput:
    def __init__(self, return_format, input_type):
        self.return_format = return_format
        self.input_type = input_type

    def get_input_class(self, type):
        """
        Returns the appropriate UserInput subclass for the given type.
        """
        if type == "mapping_conversations":
            return MappingConversations()
        elif type == "mapping_votes":
            return MappingVotes()
        else:
            raise ValueError("Invalid input type specified.")


    def get_user_input(self, resource_type, collection_type, id, code, type):
        """
        Retrieves user input for the identified Resource/id/collection/code/type.
        Does not filter down by editor.
        Returns only one type of user_input.

        Args:
        resource_type (str): The resource collection (e.g., "Terminology").
        collection_type (str): The subcollection (e.g., "user_input")
        id (str): The document ID.
        code (str): The target document (mapping) identifier.

        Returns:
            dict: Serialized user input data based on the type specified.
        
        Example output for TerminologyUserInput type mapping_votes
        {
            "Terminology": "tm--2VjOxekLP8m28EPRqk95",
            "code": "TEST_0001",
            "user_id": [
                {
                    "user_id": user
                    "up": "date"
                },
            ]
        }
        """
        try:
            doc_ref = persistence().collection(resource_type).document(id) \
                .collection(collection_type).document(code)

            doc_snapshot = doc_ref.get()

            if doc_snapshot.exists:
                existing_data = doc_snapshot.to_dict()
            else:
                return {resource_type: id,
                        "code": code,
                        "message": "No user input for this mapping."}

            # Use the type to instantiate the corresponding UserInput subclass
            user_input_instance = self.get_input_class(type)
            
            # Retrieve the specific input data using the type
            input_data = existing_data.get(type)

            # If input_data is not found, return the appropriate default format
            if input_data is None:
                input_data = user_input_instance.return_format if user_input_instance.return_format != list else []

            # Serialize the data using the appropriate schema
            schema = user_input_instance._Schema()
            serialized_data = schema.dump({type: input_data})

            # Return the extracted and serialized data in a standardized format
            return {
                resource_type: id,
                "code": code,
                type: serialized_data[type]
            }
        
        except Exception as e:
            return (f"An error occurred while retrieving user input for {id} {resource_type} - {code}: {e}"), 500

    def create_or_replace_user_input(self, resource_type, collection_type, id, code, type, body):
        """
        Creates or replaces a document in the 'user_input' sub-collection data
        for a user.
        """
        # Prep the data
        try:
            editor = body.get('editor') if 'editor' in body else None

            # Instantiate the appropriate UserInput subclass
            user_input_instance = self.get_input_class(type)

            # Build and format user_input as necessary
            user_input = user_input_instance.build_user_input(
                body.get(user_input_instance.input_type),
                editor=editor
            )

            formatted_user_input = user_input_instance.format_for_storage(user_input)

        except Exception as e:
            return (f"ERROR: while creating the user_input from body: {e}"), 500

        # Validate
        try:
            user_input_instance.validate_input(user_input)
        except ValueError as e:
            return {"message": str(e)}, 400
        
        # Prep any existing data
        try:
            doc_ref = persistence().collection(resource_type).document(id) \
                .collection(collection_type).document(code)

            # Fetch existing data for the document if it exists
            doc_snapshot = doc_ref.get()
            existing_data = doc_snapshot.to_dict() if doc_snapshot.exists else {}

             # Initialize type structure using return_format if it doesn't exist
            if type not in existing_data:
                existing_data[type] = self.return_format() \
                                      if callable(self.return_format) \
                                      else self.return_format

            # Get user_id to identify existing data for the user.
            try:
                user_id = SessionManager.create_user_id(editor=editor)
            except ValueError as e:
                print(f"An error occurred while getting the user_id. {e}")

        except Exception as e:
            return (f"An error occured during update setup {e}"), 500
        
        # Update or append the user input based on type. Updates existing_data.
        try:
            self.update_or_append_input(
                existing_data[type],
                user_id,
                formatted_user_input,
                user_input_instance.return_format
            )
        except Exception as e:
            return (f"An error occurred while appending data. {e}"), 500
        
        # Update the Firestore document with the new data.
        try:
            doc_ref.set(existing_data)
            return existing_data

        except Exception as e:
            return (f"An error occurred while updating firestore {id} \
                    {resource_type} - {code}: {e}"), 500


    def update_or_append_input(self, existing_data, user_id, new_record, return_format):
        """
        Update existing input or append new user input.

        Args:
            existing_data (dict or list): The data to be updated (could be a dict or list).
            user_id (str): The user ID for the entry.
            new_record (dict or list): The user_input formatted as defined by it's class.
            return_format (type): The format in which input data is stored (list or dict).
        """
        if return_format == dict:
            
            # Insert new record or update existing entry based on user_id.
            existing_data.update(new_record)
            
        elif return_format == list:
            # Get the users existing entry
            existing_entry = next((entry for entry in existing_data if entry.get('user_id') == user_id), None)
    
            if existing_entry:
                # Update the existing entry.
                existing_entry.update(new_record.get(user_id))
            else:
                # Append a new input if no matching entry is found.
                existing_data.append(new_record[user_id])

class MappingConversations(UserInput):
    """Represents a user's comments or notes for multiple mappings. Used
        to serialize and deserialize data.
    
    Attributes:
        mapping_conversations (list): A list of dictionaries representing 
            the users input as well as metadata.

    Data Expectations:
        "mapping_conversations": {
            "date": "Sep 25, 2024, 08:47:33.396 AM",
            "user_id": "users id",
            "note": "note here"
        }
    """
    def __init__(self):
        super().__init__(return_format=list,input_type="note")

    def build_user_input(self, note, editor=None):
        """
        Structures conversation response body to format expected by the 
        update function.

        Args:
            note (str): The note content (e.g., a comment from the user).
            editor (str, optional): The editor's user ID, if provided.

        """
        try: 
            user_id = SessionManager.create_user_id(editor=editor)

        except ValueError as e:
            print(f"Error: {e}")

        date = SessionManager.create_current_datetime()

        return {
            "user_id": user_id,
            "note": note,
            "date": date
        }
    
    def validate_input(self, user_input):
        note = user_input.get('note')
        if not note or len(note) > USER_INPUT_CHAR_LIMIT:
            raise ValueError(f"'note' must be provided and cannot exceed {USER_INPUT_CHAR_LIMIT} characters.")
        else:
            pass

    def format_for_storage(self, user_input):
        return {
            user_input["user_id"]: {
                "note": user_input["note"],
                "date": user_input["date"]
            }
        }

    class _Schema(Schema):
        """Schema for serializing/deserializing multiple mapping conversations."""
        mapping_conversations = fields.List(fields.Dict(keys=fields.Str(),
                                                            values=fields.Str()))

        @post_load
        def build_mapping_conversations(self, data, **kwargs):
            """Transforms deserialized data into a MappingConversations instance."""
            return MappingConversations(data['mapping_conversations'])
        
    def to_dict(self):
        """Converts the list of mapping conversations to a dictionary format.
        If the datetime cannot be converted to a datetime. The process should fail.
        
        """
        return {
            "mapping_conversations": [
                {
                    "user_id": conv["user_id"],
                    "date": conv["date"],
                    "note": conv["note"]
                } for conv in self.mapping_conversations
            ]
        }
    

class MappingVotes(UserInput):
    """
    Represents multiple user votes.

    Example:
        mapping_votes {
        "user_id": {
            "vote": "up",
            "date": date
        }
    }

    """
    def __init__(self):
        super().__init__(return_format=dict,input_type="vote")

    def build_user_input(self, vote, editor=None):
        """
        Structures vote response body to format expected by the update function.

        Args:
            vote (str): The vote value (e.g., 'up' or 'down').
        """
        try:
            user_id = SessionManager.create_user_id(editor=editor)
        except ValueError as e:
            print(f"Error: {e}")

        date = SessionManager.create_current_datetime()
        
        return {
                "user_id": user_id,
                "vote": vote,
                "date": date
            }

    def _build_mapping_votes(self, mapping_votes):
        """Transforms the input list of votes into the desired dictionary structure.

        Args:
            mapping_votes (list): A list of dictionaries with user_id, vote, and date.
        
        Returns:
            dict: A dictionary with user_id as keys and their vote and date as values.
        """

        return {vote["user_id"]: {"vote": vote["vote"],
                                    "date": vote["date"]} for vote in mapping_votes
    }

    def validate_input(self, user_input):
        vote = user_input.get('vote')
        if not vote or vote not in ['up', 'down']:
            raise ValueError("'vote' must be provided and set to 'up' or 'down'.")
        else: 
            pass

    def format_for_storage(self, user_input):
        return {
            user_input["user_id"]: {
                "vote": user_input["vote"],
                "date": user_input["date"]
            }
        }

    class _Schema(Schema):
        """
        Marshmallow schema for serializing and deserializing mapping votes.
        """        
        mapping_votes = fields.Dict(
            keys=fields.Str(),
            values=fields.Dict(keys=fields.Str(), values=fields.Str())
        )
        @post_load
        def build_mapping_votes(self, data, **kwargs):
            """
            Transform the loaded data into the desired structure.
            Args:
                data (dict): The deserialized data.
            Returns:
                dict: A dictionary representation of the mapping votes.
            """
            return MappingVotes(data['mapping_votes'])
        
    def to_dict(self):
        """Converts the list of mapping votes to a dictionary format."""
        return {"mapping_votes": self.mapping_votes}
