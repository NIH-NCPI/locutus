from . import Serializable
from marshmallow import Schema, fields, post_load
from locutus import persistence


"""
The reference just represents a placeholder for an entity from another table
"""


class Reference(Serializable):
    """A FHIR-like reference entity-for our needs, the reference should be to
    a local url."""

    def __init__(self, reference=None, instance=None):
        if type(reference) is not str:
            print(f"What sort of reference is this?\n{reference}")

        self.reference = reference

        # Dumb, super short lived cache. If this object is expected to live
        # beyond a short block, clients should take care to clear the cached
        # instance to avoid working off of a stale data object
        self._reference = instance

    class _Schema(Schema):
        reference = fields.Str()
        resource_type = fields.Str()

        @post_load
        def build_reference(self, data, **kwargs):
            return Reference(**data)

    def reset_cache(self, instance=None):
        """I imagine this would normally be default, but if you happen to know
        that your version is current, you can use this function to update
        the cached reference."""
        self._reference = instance

    def dereference(self):
        """Pulls actual representation down and returns it. Reference object
        does cache this locally, but that shouldn't be trusted for more
        than a single block."""
        if self._reference is None:
            resource_type, id = self.reference.split("/")
            resource_raw = (
                persistence().collection(resource_type).document(id).get().to_dict()
            )
            self._reference = Serializable.build_object(resource_raw)

        return self._reference

    def reference_id(self):
        return self.reference.split("/")[-1]
