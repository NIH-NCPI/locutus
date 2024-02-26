from flask_restful import Resource
from locutus import persistence
from locutus.model.terminology import Terminology as Term
from flask_cors import cross_origin
from locutus.api import default_headers
import pdb

"""
Endpoint associated with GETting all mappings for a given terminology

endpoint: ../Terminology/[terminology_id]/mapping
method: GET
response:
    terminology: Reference to the Terminology associated with the request
    codes: List of Mappings:
        code: Code from the terminology
        mappings: list of codings (code, display, system, etc)


example call:
    url: est3630:5000/api/Terminology/tm-43WDERlpYBSEAYXt9QCub/mapping/Male
    input: 
{
    "terminology": {
        "Reference": "Terminology/tm-43WDERlpYBSEAYXt9QCub"
    },
    "codes": [
        {
            "code": "Female",
            "mappings": [
                {
                    "code": "female",
                    "display": "Female",
                    "system": "http://hl7.org/fhir/administrative-gender"
                }
            ]
        },
        {
            "code": "Male",
            "mappings": [
                {
                    "code": "male",
                    "display": "Male",
                    "system": "http://hl7.org/fhir/administrative-gender"
                }
            ]
        }
    ]
}

Notes:
The terminology reference seems a bit redundant, so that may just go away. It
seemed appropriate when I was planning things out, but seeing it here makes 
it seem rather silly

"""


class TerminologyMappings(Resource):
    @classmethod
    def get_mappings(cls, id):
        pdb.set_trace()
        termref = persistence().collection("Terminology").document(id)
        term = termref.get().to_dict()

        if term is not None:
            if "resource_type" in term:
                del term["resource_type"]

            t = Term(**term)

            response = {
                "terminology": {
                    "Reference": f"Terminology/{t.id}",
                },
                "codes": [],
            }
            mappings = t.mappings()

            for code in mappings:
                mapping = {"code": code, "mappings": []}
                for coding in mappings[code]:
                    mapping["mappings"].append(coding.to_dict())

                response["codes"].append(mapping)

            return response
        return None

    @classmethod
    def get(cls, id):
        response = cls.get_mappings(id)
        if response is not None:
            return (response, 200, default_headers)
        return (None, 404, default_headers)
