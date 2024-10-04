from flask_restful import Resource
from flask import request
from locutus.model.terminology import Terminology as Term
from locutus.api import default_headers
from locutus.model.sessions import SessionManager

import pdb


class TerminologyUserInput(Resource, Term):
    """
    Resource for handling user input related to terminology mappings.

    This class provides methods to retrieve and update user inputs for
    terminology, including mapping conversations and votes. 

    Attributes:
        resource_type (str): The type of resource, default is "Terminology".
        collection_type (str): The sub-collection for user input, default is "user_input".
    """
    def __init__(self, resource_type= "Terminology", collection_type="user_input"):
        self.resource_type = resource_type
        self.collection_type = collection_type
    
    def get(self, id, code, type):
            """
            Retrieves user input for the identified Resource/id/collection/code/type.
            Does not filter down by editor.
            Returns only one type of user_input.

            Args:
                id (str): Defines the terminology of interest
                code (str): Defines the target document(mapping)
                type (str): The type of input to retrieve
                    (e.g., "mapping_conversations" or "mapping_votes").

            Example output for TerminologyUserInput type mapping_votes
            {
                "Terminology": "tm--2VjOxekLP8m28EPRqk95",
                "code": "TEST_0001",
                "mapping_votes": [
                    {
                        "user2": "up"
                    },
                    {
                        "user3": "down"
                    }
                ]
            }
            """

            t = Term.get(id)

            user_input = t.get_user_input(self.resource_type, self.collection_type,
                                           id, code, type)
            
            return (user_input, 200, default_headers)
            
    def put(self, id, code, type):
        """
        Update the user input 

        This method updates the user input for a specific mapping based on 
        the provided user data. 

        Args:
            id (str): Defines the terminology of interest.
            code (str): Defines the target document (mapping).
            type (str): The type of input to update (e.g., "mapping_votes").

        Request Body:
        {
            "note": "I dont like this mapping"
        }
        """
        body = request.get_json()
        t = Term.get(id)

        user_input = body

        # Validate input based on type
        if type == 'mapping_votes':
            vote = user_input.get('vote')
            if not vote or vote not in ['up', 'down']:
                return {"message": "'vote' must be provided set to 'up' or 'down'."}, 400

        elif type == 'mapping_conversations':
            note = user_input.get('note')
            if not note or len(note) > 500:
                return {"message": f"'note' must be provided and cannot exceed 500 characters."}, 400

        # Add additional data (user ID and date) to the input
        user_obj = SessionManager.create_session_user_object()
        if 'error' in user_obj:
            return {"message": "User not logged in"}, 401

       # Update the user input with user_id and date
        user_input.update(user_obj)
        user_input.update(SessionManager.create_date_object())

        # create input for the user or replace existing input
        t.create_or_replace_user_input(self.resource_type,
                                       self.collection_type,
                                       id,
                                       code,
                                       type,
                                       user_input)

        response = {
            "message": f"The {type} was updated for {id}-{code}"
        }
        return (response, 200, default_headers)
        