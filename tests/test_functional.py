from schematics.models import Model
from schematics.types import IntType, StringType
from schematics.validate import validate
from schematics.exceptions import ValidationError


def test_validate_simple_dict():
    class Player(Model):
        id = IntType()

    validate(Player, {'id': 4})


def test_validate_keep_context_data():
    class Player(Model):
        id = IntType()
        name = StringType()

    p1 = Player({'id': 4})
    data = validate(Player, {'name': 'Arthur'}, context=p1._data)

    assert data == {'id': 4, 'name': 'Arthur'}
    assert data != p1._data


def test_validate_override_context_data():
    class Player(Model):
        id = IntType()

    p1 = Player({'id': 4})
    data = validate(Player, {'id': 3}, context=p1._data)

    assert data == {'id': 3}


def test_validate_ignore_extra_context_data():
    class Player(Model):
        id = IntType()

    data = validate(Player, {'id': 4}, context={'name': 'Arthur'})

    assert data == {'id': 4, 'name': 'Arthur'}


def test_validate_strict_with_context_data():
    class Player(Model):
        id = IntType()

    try:
        validate(Player, {'id': 4}, strict=True, context={'name': 'Arthur'})
    except ValidationError as e:
        assert 'name' in e.messages


def test_validate_partial_with_context_data():
    class Player(Model):
        id = IntType()
        name = StringType(required=True)

    data = validate(Player, {'id': 4}, partial=False, context={'name': 'Arthur'})

    assert data == {'id': 4, 'name': 'Arthur'}


def test_validate_with_instance_level_validators():
    class Player(Model):
        id = IntType()

        def validate_id(self, context, value):
            if p1._initial['id'] != value:
                p1._data['id'] = p1._initial['id']
                raise ValidationError('Cannot change id')

    p1 = Player({'id': 4})
    p1.id = 3

    try:
        validate(Player, p1)
    except ValidationError as e:
        assert 'id' in e.messages
        assert 'Cannot change id' in e.messages['id']
        assert p1.id == 4
