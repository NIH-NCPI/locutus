import pytest

from locutus.model.study import Study


@pytest.fixture
def basic_study():
    study = Study(
        name="FTD Study 01",
        url="http://ftd.unit.tests/locutus/",
        title="Simple Study Test Fixture",
        description="Simple Test Study",
    )
    study.save()
    yield study
    # study.global_id().delete()
    study.delete(hard_delete=True)


def test_study_basics(basic_study):
    study = Study.get(basic_study.id)
    assert study.id == basic_study.id
    assert study.name == basic_study.name
    assert study.description == basic_study.description
