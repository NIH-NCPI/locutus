"""
Classes define user input such as comments/notes, and up/down votes.

Current Use:
 * Terminology Mappings (Terminology sub-collection user_input)
    - Mapping conversations: user comments regarding a single mapping
    - Mapping votes: users up/down vote regarding a single mapping

"""
from marshmallow import Schema, fields, post_load

from locutus.model.sessions import SessionManager
class UserInput:
    class MappingConversations:
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

        def __init__(self, mapping_conversations):
            self.mapping_conversations = mapping_conversations

        def build_mapping_conversation(self, note):
            """
            Structures conversation response body to format expected by the 
            update function.

            Args:
                note (str): The note content (e.g., a comment from the user).

            """
            # Get the user_id and date using session manager methods
            user_id = SessionManager.create_session_user_id()
            if 'error' in user_id:
                raise ValueError("User not logged in")

            date = SessionManager.create_current_datetime()

            return {
                "user_id": user_id,
                "note": note,
                "date": date
            }

        class _Schema(Schema):
            """Schema for serializing/deserializing multiple mapping conversations."""
            mapping_conversations = fields.List(fields.Dict(keys=fields.Str(),
                                                             values=fields.Str()))

            @post_load
            def build_mapping_conversations(self, data, **kwargs):
                """Transforms deserialized data into a UserInput.MappingConversations instance."""
                return UserInput.MappingConversations(data['mapping_conversations'])
            
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
        

    class MappingVotes:
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
        def __init__(self, mapping_votes):
            self.mapping_votes = mapping_votes

        def build_mapping_vote(self, vote):
            """
            Structures vote response body to format expected by the update function.

            Args:
                vote (str): The vote value (e.g., 'up' or 'down').
            """
            # Get the user_id and date using session manager methods
            user_id = SessionManager.create_session_user_id()
            if 'error' in user_id:
                raise ValueError("User not logged in")

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
                return UserInput.MappingVotes(data['mapping_votes'])
            
        def to_dict(self):
            """Converts the list of mapping votes to a dictionary format."""
            return {"mapping_votes": self.mapping_votes}
