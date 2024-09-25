from flask_restful import Resource
from flask import request
from locutus.model.terminology import Terminology as Term
from locutus.api import default_headers

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
        the provided user data. It checks if the user is allowed to update 
        the input based on their role (editor/admin) and the defined rules.

        Args:
            id (str): Defines the terminology of interest.
            code (str): Defines the target document (mapping).
            type (str): The type of input to update (e.g., "mapping_votes").

        Request Body:
            {
                "editor": "ex_user",
                "mapping_votes": {
                    "ex_user": "updated up"
                },
                "update_allowed": "False",
                "is_admin": "True"
            }
        
        Notes: 
            update_allowed(Optional, default=True): Denotes whether previous 
              user input should be editable.
            is_admin(Optional, default=False): Denotes the requester is the
              an admin and is able to edit a user's data.
        """
        body = request.get_json()
        t = Term.get(id)

        if 'editor' not in body:
            return {"message": "editor is required"}

        editor = body.get("editor")  
        user_input = body.get(type)

        if 'update_allowed' in body:
             update_allowed = body.get('update_allowed').lower() == 'true'
        else:
             update_allowed = True

        if 'is_admin' in body:
             is_admin = body.get('is_admin').lower() == 'true'
        else:
             is_admin = False

        # Validate 'mapping_votes' values
        if type == 'mapping_votes':
            for user, vote in user_input.items():
                if vote.lower() not in ['up', 'down']:
                    return {"message": f"Invalid vote value '{vote}' for user \
                             {user}. Must be 'up' or 'down'."}, 400

        # create input for the user or replace existing input
        t.create_or_replace_user_input(self.resource_type,
                                       self.collection_type,
                                       id,
                                       code,
                                       type,
                                       editor,
                                       user_input,
                                       update_allowed,
                                       is_admin)

        response = {
            "user_id": editor,
            "message": f"{editor}s {type} were updated for {id}-{code}"
        }
        return (response, 200, default_headers)
        