"""
Classes define user input such as comments/notes, and up/down votes.

Current Use:
 * Terminology Mappings (Terminology sub-collection user_input)
    - Mapping conversations: user comments regarding a single mapping
    - Mapping votes: users up/down vote regarding a single mapping

"""
from marshmallow import Schema, fields, post_load
# from locutus import persistence, FTD_PLACEHOLDERS, normalize_ftd_placeholders
import locutus
from locutus.api import generate_mapping_index, get_editor
from locutus.sessions import SessionManager
from locutus.model.exceptions import *

from .simple import Simple
USER_INPUT_CHAR_LIMIT = 1000

import pdb

class UserInput:
    def __init__(self, return_format, input_type, update_policy):
        self.return_format = return_format
        self.input_type = input_type
        self.update_policy = update_policy

    @classmethod 
    def get_input_class(cls, type):
        """
        Returns the appropriate UserInput subclass for the given type.
        """
        if type == "mapping_conversations":
            return MappingConversation
        elif type == "mapping_votes":
            return MappingVote
        else:
            raise ValueError("Invalid input type specified.")

    @classmethod 
    def get_user_input(cls, resource_type, collection_type, id, code, mapped_code, type):
        """
        Retrieves user input for the identified Resource/id/collection/code/type.
        Does not filter down by editor.
        Returns only one type of user_input.

        Args:
        resource_type (str): The resource collection (e.g., "Terminology").
        collection_type (str): The subcollection (e.g., "user_input")
        id (str): The document ID.
        code (str): The target document (mapping) identifier.
        mapped_code (str): Defines the code being mapped to the target.

        Returns:
            dict: Serialized user input data based on the type specified.
        
        Example output for TerminologyUserInput type mapping_votes
        {
            "Terminology": "tm--2VjOxekLP8m28EPRqk95",
            "code": "TEST_0001",
            "mapped_code": "Study Code"
            "user_id": [
                {
                    "user_id": user
                    "up": "date"
                },
            ]
        }
        """
        try:
            user_input_class = cls.get_input_class(type)
            existing_data = user_input_class.get(
                terminology_id=id,
                source_code=code,
                mapped_code=mapped_code,
                return_instance=False
            )
            
            if existing_data == []:
                return {resource_type: id,
                        "code": code,
                        "source_code": code,
                        "mapped_code": mapped_code,
                        "message": "No user input for this mapping."}
            existing_data['code'] = existing_data['source_code']
            return existing_data 


        except Exception as e:
            return (f"An error occurred while retrieving user input for {id} {resource_type} - {code}/{mapped_code}: {e}"), 500

    @classmethod 
    def delete_user_conversations(cls, resource_type, collection_type, id, code, mapped_code, hard_delete=False):
        user_input = MappingConversation.get(terminology_id=id,
                                    source_code=code,
                                    mapped_code=mapped_code,
                                    return_instance=True)
        user_input.delete(hard_delete=hard_delete)
    
    def exists_in_db(self, 
                    return_instance=True):

        item = self.__class__.get(terminology_id=self.terminology_id,
                        source_code=self.source_code, 
                        mapped_code=self.mapped_code,  
                        return_instance=return_instance)

        if item == []:
            return None

        if len(item) == 1:
            return item[0]
        return item

    @classmethod 
    def get(cls, _id=None, terminology_id=None, source_code=None, mapped_code=None, return_instance=True):
        if _id is not None:
            return cls.find({"_id": _id}, return_instance=return_instance)

        if (not isinstance(terminology_id, str) or not terminology_id.strip()):
            raise ValueError("Terminology ID is required to get a coding without an _id.")
        
        params = {
            "terminology_id": terminology_id
        }

        if source_code is not None:
            params['source_code'] = source_code 
        if mapped_code is not None:
            params['mapped_code'] = mapped_code 

        conversations = cls.find(params, return_instance=return_instance)

        if len(conversations) == 1:
            return conversations[0]
        
        return conversations

    @classmethod 
    def delete_user_votes(cls, resource_type, collection_type, id, code, mapped_code, hard_delete=False):
        user_input = MappingVote.get(terminology_id=id,
                                    source_code=code,
                                    mapped_code=mapped_code,
                                    return_instance=True)
        user_input.delete(hard_delete=hard_delete)

    @classmethod
    def create_or_replace_user_input(cls, resource_type, collection_type, id, code, mapped_code, type, input_value, editor):
        """
        Creates or replaces a document in the 'user_input' sub-collection data
        for a user.
        """
        # Prep the data
        try:
            document_id = generate_mapping_index(code, mapped_code)
            editor = get_editor(body={}, editor=editor)
            if editor is None:
                raise LackingUserID(editor)

            # Instantiate the appropriate UserInput subclass
            input_class = cls.get_input_class(type)
            user_input_instance = input_class(terminology_id=id, 
                                                        source_code=code,
                                                        mapped_code=mapped_code)

            # Build and format user_input as necessary
            input_data = user_input_instance.add_input(input_value, editor=editor)

            user_input_instance.save()

            content = user_input_instance.dump()
            # For the time being, we will reuse the old name for source_code to avoid breaking FE
            content['code'] = content['source_code']
            return content

        except Exception as e:
            return (f"An error occurred while updating firestore {id} \
                    {resource_type} - {document_id}: {e}"), 500

    @classmethod
    def update_or_append_input(cls, existing_data, user_id, new_record, return_format):
        """
        For user_input types that allow only one record per user(update_policy=update),
        update existing user_input or append user_input if the user has no existing data.

        Args:
            existing_data (dict or list): The data to be updated (could be a dict or list).
            user_id (str): The user ID for the entry.
            new_record (dict or list): The user_input formatted as defined by it's class.
            return_format (type): The format in which input data is stored (list or dict).
        """
        if return_format == dict:

            # Insert new record or update existing entry based on user_id.
            existing_data[user_id] = new_record[user_id]

        elif return_format == list:

            if isinstance(existing_data, list):
                # Check if the user_id already exists in the list
                existing_entry = next((entry for entry in existing_data if entry.get('user_id') == user_id), None)

                if existing_entry:
                    # Update the existing entry
                    existing_entry.update(new_record[0])
                else:
                    # Append a new entry.
                    existing_data.insert(0, new_record[0])
                print(f"Updated mapping conversations: {existing_data}")
            else:
                raise ValueError("The existing data should be of return_format type 'list'.")


class MappingConversation(Simple, UserInput):
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
    def __init__(self,
                terminology_id,
                source_code,
                mapped_code,
                id=None,
                _id=None,
                mapping_conversations=None):
        if mapping_conversations is None:
            mapping_conversations = []
        self.terminology_id=terminology_id 
        self.source_code=source_code 
        self.mapped_code=mapped_code 


        prev = self.exists_in_db(return_instance=False)
        if prev is not None:
            _id = prev['_id']

            if id is None:
                id = prev['id']
            if mapping_conversations == []:
                mapping_conversations = prev['mapping_conversations']

        Simple.__init__(self, id=id,
                        _id=_id, 
                        collection_type="mapping_conversations",
                        resource_type="MappingConversation")

        UserInput.__init__(self, return_format=list, input_type="note", update_policy="append")


        self.mapping_conversations = mapping_conversations


    def add_input(self, input, editor=None):
        import pdb 
        pdb.set_trace()
        input_data=self.build_user_input(input, editor)
        self.mapping_conversations.append(input_data)

    def get_input(self):
        return self.mapping_conversations

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


        if type(note) is dict:
            note = note['note']

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
        return [{
            "user_id": user_input["user_id"],
            "note": user_input["note"],
            "date": user_input["date"]
        }]

    class _Schema(Schema):
        """Schema for serializing/deserializing multiple mapping conversations."""
        id = fields.Str()
        source_code = fields.Str()
        mapped_code = fields.Str()
        terminology_id = fields.Str()

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


class MappingVote(Simple, UserInput):
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
    def __init__(self,
                terminology_id,
                source_code,
                mapped_code,
                id=None,
                _id=None,
                mapping_votes=None):

        if mapping_votes is None:
            mapping_votes = {}
        self.terminology_id=terminology_id 
        self.source_code=source_code 
        self.mapped_code=mapped_code 

        prev = self.exists_in_db(return_instance=False)

        if prev is not None:
            _id = prev['_id']

            if id is None:
                id = prev['id']
            if mapping_votes == {}:
                mapping_votes = prev['mapping_votes']

        Simple.__init__(self, id=id,
                        _id=_id, 
                        collection_type="mapping_votes",
                        resource_type="MappingVote")


        UserInput.__init__(self, return_format=list, input_type="note", update_policy="append")
        self.mapping_votes = mapping_votes

    def build_user_input(self, user_input, editor=None):
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
        vote = user_input  

        if type(vote) is dict:
            vote = vote['vote']
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

    def add_input(self, input, editor=None):
        input_data=self.build_user_input(input, editor)
        self.mapping_votes[input_data['user_id']] = {
                "vote": input_data["vote"],
                "date": input_data["date"]
            }

    def get_input(self):
        return self.mapping_votes

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

        id = fields.Str()
        source_code = fields.Str()
        mapped_code = fields.Str()
        terminology_id = fields.Str()
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
