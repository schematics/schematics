import pytest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import DataError


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


def test_simple_embedded_model_set_to_none():
    class Location(Model):
        country_code = StringType()

    class Player(Model):
        id = IntType()
        location = ModelType(Location)

    p = Player(dict(id=1))
    p.location = None

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

    with pytest.raises(DataError):
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


def test_export_loop_with_subclassed_model():
    class Asset(Model):
        file_name = StringType()

    class S3Asset(Asset):
        bucket_name = StringType()

    class Product(Model):
        title = StringType()
        asset = ModelType(Asset)

    asset = S3Asset({'bucket_name': 'assets_bucket', 'file_name': 'bar'})

    product = Product({'title': 'baz', 'asset': asset})

    primitive = product.to_primitive()
    assert 'bucket_name' in primitive['asset']

    native = product.to_native()
    assert 'bucket_name' in native['asset']


def test_mock_object():
    class User(Model):
        name = StringType(required=True)
        age = IntType(required=True)

    assert ModelType(User, required=True).mock() is not None


def test_specify_model_by_name():

    class M(Model):
        to_one = ModelType('M')
        to_many = ListType(ModelType('M'))
        matrix = ListType(ListType(ModelType('M')))

    assert M.to_one.model_class is M
    assert M.to_many.field.model_class is M
    assert M.matrix.field.field.model_class is M
