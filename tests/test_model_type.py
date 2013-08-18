import pytest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import ValidationError


def test_simple_embedded_models():
    class Location(Model):
        country_code = StringType()

    class Player(Model):
        id = IntType()
        location = ModelType(Location)

    p = Player(dict(id=1, location={"country_code": "US"}))

    assert p.id == 1
    assert p.location.country_code == "US"

    p.location = Location({"country_code": "IS"})

    assert isinstance(p.location, Location)
    assert p.location.country_code == "IS"


def test_simple_embedded_models_is_none():
    class Location(Model):
        country_code = StringType()

    class Player(Model):
        id = IntType()
        location = ModelType(Location)

    p = Player(dict(id=1))

    assert p.id == 1
    assert p.location is None


def test_simple_embedded_model_is_none_within_listtype():
    class QuestionResources(Model):
        type = StringType()

    class Question(Model):
        id = StringType()
        resources = ModelType(QuestionResources)

    class QuestionPack(Model):
        id = StringType()
        questions = ListType(ModelType(Question))

    question_pack = QuestionPack({
        "id": "1",
        "questions": [
            {
                "id": "1",
            },
        ]
    })

    assert question_pack.questions[0].resources is None


def test_raises_validation_error_on_init_with_partial_submodel():
    class User(Model):
        name = StringType(required=True)
        age = IntType(required=True)

    class Card(Model):
        user = ModelType(User)

    u = User({'name': 'Arthur'})
    c = Card({'user': u})

    with pytest.raises(ValidationError):
        c.validate()


def test_model_type():
    class User(Model):
        name = StringType()

    class Card(Model):
        user = ModelType(User)

    c = Card({"user": {'name': u'Doggy'}})
    assert isinstance(c.user, User)
    assert c.user.name == "Doggy"


def test_equality_with_embedded_models():
    class Location(Model):
        country_code = StringType()

    class Player(Model):
        id = IntType()
        location = ModelType(Location)

    p1 = Player(dict(id=1, location={"country_code": "US"}))
    p2 = Player(dict(id=1, location={"country_code": "US"}))

    assert id(p1.location) != id(p2.location)
    assert p1.location == p2.location

    assert p1 == p2


def test_default_value_when_embedded_model():
    class Question(Model):
        question_id = StringType(required=True)

        type = StringType(default="text")

    class QuestionPack(Model):

        question = ModelType(Question)

    pack = QuestionPack({
        "question": {
            "question_id": 1
        }
    })

    assert pack.question.question_id == "1"
    assert pack.question.type == "text"
