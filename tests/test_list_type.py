import pytest

from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.types.compound import ModelType, ListType
from schematics.exceptions import ValidationError, StopValidation


def test_list_field():
    class User(Model):
        ids = ListType(StringType, required=True)

    c = User({
        "ids": []
    })

    c.validate({'ids': []})

    assert c.ids == []


def test_list_with_default_type():
    class CategoryStatsInfo(Model):
        slug = StringType()

    class PlayerInfo(Model):
        categories = ListType(ModelType(CategoryStatsInfo))

    math_stats = CategoryStatsInfo(dict(slug="math"))
    twilight_stats = CategoryStatsInfo(dict(slug="twilight"))
    info = PlayerInfo({
        "categories": [{"slug": "math"}, {"slug": "twilight"}]
    })

    assert info.categories == [math_stats, twilight_stats]

    d = info.serialize()
    assert d == {
        "categories": [{"slug": "math"}, {"slug": "twilight"}],
    }


def test_set_default():
    class CategoryStatsInfo(Model):
        slug = StringType()

    class PlayerInfo(Model):
        categories = ListType(ModelType(CategoryStatsInfo),
                              default=lambda: [],
                              serialize_when_none=True)

    info = PlayerInfo()
    assert info.categories == []

    d = info.serialize()
    assert d == {
        "categories": [],
    }


def test_list_defaults_to_none():
    class PlayerInfo(Model):
        following = ListType(StringType)

    info = PlayerInfo()

    assert info.following is None

    assert info.serialize() == {
        "following": None,
    }


def test_list_default_to_none_embedded_model():
    class QuestionResource(Model):
        url = StringType()

    class QuestionResources(Model):
        pictures = ListType(ModelType(QuestionResource))

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
            {
                "id": "2",
                "resources": {
                    "pictures": [],
                }
            },
            {
                "id": "3",
                "resources": {
                    "pictures": [{
                        "url": "http://www.mbl.is/djok",
                    }]
                }
            },
        ]
    })

    assert question_pack.questions[0].resources is None
    assert question_pack.questions[1].resources["pictures"] == []

    resource = QuestionResource({"url": "http://www.mbl.is/djok"})
    assert question_pack.questions[2].resources["pictures"][0] == resource


def test_validation_with_size_limits():
    class User(Model):
        name = StringType()

    class Card(Model):
        users = ListType(ModelType(User), min_size=1, max_size=2, required=True)

    with pytest.raises(ValidationError) as exception:
        c = Card({"users": None})
        c.validate()

    assert exception.value.messages['users'] == [u'This field is required.']

    with pytest.raises(ValidationError) as exception:
        c = Card({"users": []})
        c.validate()

    assert exception.value.messages['users'] == [u'Please provide at least 1 item.']

    with pytest.raises(ValidationError) as exception:
        c = Card({"users": [User(), User(), User()]})
        c.validate()

    assert exception.value.messages['users'] == [u'Please provide no more than 2 items.']


def test_list_field_required():
    class User(Model):
        ids = ListType(StringType(required=True))

    c = User({
        "ids": []
    })

    c.ids = [1]
    c.validate()

    c.ids = [None]
    with pytest.raises(ValidationError):
        c.validate()


def test_list_field_convert():
    class User(Model):
        ids = ListType(IntType)

    c = User({'ids': ["1", "2"]})

    assert c.ids == [1, 2]


def test_list_model_field():
    class User(Model):
        name = StringType()

    class Card(Model):
        users = ListType(ModelType(User), min_size=1, required=True)

    data = {'users': [{'name': u'Doggy'}]}
    c = Card(data)

    c.users = None
    with pytest.raises(ValidationError) as exception:
        c.validate()

    errors = exception.value.messages
    assert errors['users'] == [u'This field is required.']


def test_list_model_field_exception_with_full_message():
    class User(Model):
        name = StringType(max_length=1)

    class Group(Model):
        users = ListType(ModelType(User))

    g = Group({'users': [{'name': "ToLongName"}]})

    with pytest.raises(ValidationError) as exception:
        g.validate()
    assert exception.value.messages == {'users': [{'name': ['String value is too long.']}]}


def test_stop_validation():
    def raiser(x):
        raise StopValidation({'something': 'bad'})

    lst = ListType(StringType(), validators=[raiser])

    with pytest.raises(ValidationError) as exc:
        lst.validate('foo@bar.com')

    assert exc.value.messages == {'something': 'bad'}


def test_compound_fields():
    comments = ListType(ListType, compound_field=StringType)

    assert isinstance(comments.field, ListType)
