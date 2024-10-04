"""
Classes define user input such as comments/notes, and up/down votes.

Current Use:
 * Terminology Mappings (Terminology sub-collection user_input)
    - Mapping conversations: user comments regarding a single mapping
    - Mapping votes: users up/down vote regarding a single mapping

"""

from marshmallow import Schema, fields, post_load

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

        Attributes:
            mapping_votes (list): A list of dictionaries representing 
                the users input as well as metadata.

        Data Expectations:
            "mapping_votes": {
                "date": "Sep 25, 2024, 08:47:33.396 AM",
                "user_id": "users id",
                "vote": "up"
            }
        """
        def __init__(self, mapping_votes):
            self.mapping_votes = mapping_votes

        class _Schema(Schema):
            """
            Marshmallow schema for serializing and deserializing mapping votes.
            """        
            mapping_votes = fields.List(fields.Dict(keys=fields.Str(),
                                                     values=fields.Str()))

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
            return {
                "mapping_votes": [
                    {
                        "user_id": conv["user_id"],
                        "date": conv["date"],
                        "vote": conv["vote"]
                    } for conv in self.mapping_votes
                ]
            }
