import pytest 
from locutus.model.provenance import Provenance 
from locutus.model.coding import Coding
from datetime import datetime 

from time import sleep

import pdb

class TestProvenance:
    def test_term_provenance_function(self):
        prov = Provenance.terminology_provenance("tm-0000001")
        assert len(prov) == 0
        p = Provenance.add_terminology_provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.Create,
                editor="unit-test"
            )
        assert p.terminology_id == "tm-0000001"
        assert p.action == "Create Terminology"
        assert p.timestamp is not None 
        assert p.target is None

        p2 = Provenance.add_terminology_provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.AddMapping,
                new_value="hats",
                editor="unit-test"
        )
        assert p2.timestamp is not None 

        t1 = datetime.now().strftime(Provenance.PROVENANCE_TIMESTAMP_FORMAT)
        sleep(0.1)
        p3   = Provenance.add_terminology_provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.SoftDeleteMapping,
                new_value="cats",
                editor="unit-test",
                timestamp=t1
            )
        assert p3.timestamp == t1

        prov = Provenance.terminology_provenance("tm-0000001")
        assert len(prov) == 3
        assert prov[0]['action'] == p.action 
        assert prov[0]['editor'] == p.editor 
        assert prov[0]['target'] == p.target
        assert prov[1]['target'] == p3.target
        assert str(prov[2]['_id']) == p3._id 

        p.delete(hard_delete=True)
        p2.delete(hard_delete=True)
        p3.delete(hard_delete=True)
        
        prov = Provenance.terminology_provenance("tm-0000001")
        assert len(prov) == 0

    def test_provenance_instantiation(self):
        p = Provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.Create,
                editor="unit-test"
            )

        assert p.terminology_id == "tm-0000001"
        assert p.action == "Create Terminology"
        assert p.timestamp is not None 
        assert p.target is None
        p.save()

        prov = Provenance.terminology_provenance("tm-0000001")
        assert len(prov) == 1 
        assert str(prov[0]['_id']) == p._id 
        assert prov[0]['action'] == p.action 
        assert prov[0]['editor'] == p.editor 
        assert prov[0]['target'] == p.target
        p.delete(hard_delete=True)

        prov = Provenance.terminology_provenance("tm-0000001")
        assert prov == []

    def test_provenance_delete(self):
        p = Provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.Create,
                editor="unit-test"
            )

        assert p.terminology_id == "tm-0000001"
        assert p.action == "Create Terminology"
        assert p.timestamp is not None 
        assert p.target is None
        p.save()

        prov = Provenance.terminology_provenance("tm-0000001")
        assert len(prov) == 1 
        assert str(prov[0]['_id']) == p._id 
        assert prov[0]['action'] == p.action 
        assert prov[0]['editor'] == p.editor 
        assert prov[0]['target'] == p.target
        p.delete(hard_delete=False)
        prov = Provenance.terminology_provenance("tm-0000001", valid_only=False)
        assert len(prov) == 1
        assert prov[0]['action'] == p.action 
        assert prov[0]['valid'] == False 

        p.delete(hard_delete=True)
        prov = Provenance.terminology_provenance("tm-0000001")
        assert prov == []

    def test_prov_order(self):
        # Create 2 timestamps with some delay between them
        t1 = datetime.now().strftime(Provenance.PROVENANCE_TIMESTAMP_FORMAT)
        sleep(0.1)
        t2 = datetime.now().strftime(Provenance.PROVENANCE_TIMESTAMP_FORMAT)
        sleep(0.1)

        p2   = Provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.AddMapping,
                new_value="hats",
                editor="unit-test",
                timestamp=t2
            )
        p2.save()
        p3   = Provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.SoftDeleteMapping,
                new_value="cats",
                editor="unit-test"
            )
        p3.save()

        p1   = Provenance(
                terminology_id="tm-0000001",
                action=Provenance.ChangeType.Create,
                new_value="",
                editor="unit-test",
                timestamp=t1
            )
        p1.save()

        prov = Provenance.terminology_provenance("tm-0000001")
        assert len(prov) == 3
        assert str(prov[0]['_id']) == p1._id 
        assert str(prov[1]['_id']) == p2._id 
        assert str(prov[2]['_id']) == p3._id

        p1.delete(hard_delete=True)
        p2.delete(hard_delete=True)
        p3.delete(hard_delete=True)





