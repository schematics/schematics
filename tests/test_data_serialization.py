import json
import unittest

from . import fixtures


def pj(j):
    return json.dumps(j, indent=2, sort_keys=True)


class ModelSerializer:
    ### Subclass overrides these
    klass = None
    description = dict()
    owner_safe = dict()
    public_safe = dict()

    def setUp(self):
        self.instance = self.klass(self.description)
        self.as_dict = self.instance.serialize()
        self.dict_owner_safe = self.owner_safe
        self.dict_public_safe = self.public_safe

    def test_instance_to_primitive(self):
        self.assertEquals(self.as_dict, self.description)

    def test_dict_owner_safe(self):
        dict_owner_safe = self.instance.serialize(role="owner")
        # print pj(self.dict_owner_safe)
        # print pj(dict_owner_safe)
        self.assertEqual(self.dict_owner_safe, dict_owner_safe)

    def test_dict_public_safe(self):
        dict_public_safe = self.instance.serialize(role="public")
        self.assertEqual(self.dict_public_safe, dict_public_safe)


class OnwerOnlyModelSerializer(ModelSerializer):

    def test_dict_public_safe(self):
        self.assertRaises(Exception, lambda: self.instance.serialize(role="public"))


class TestSimpleModel(OnwerOnlyModelSerializer, unittest.TestCase):
    klass = fixtures.SimpleModel

    description = {
        'title': u'Misc Doc',
        'owner': None,
    }

    owner_safe = {
        'title': u'Misc Doc',
        'owner': None,
    }

    public_safe = {}


class TestSubModel(ModelSerializer, unittest.TestCase):
    klass = fixtures.SubModel

    description = {
        'title': u'Total Recall',
        'year': 1990,
        'thoughts': u'I wish I had three hands...',
        'owner': None,
    }

    owner_safe = {
        'title': u'Total Recall',
        'year': 1990,
        'thoughts': u'I wish I had three hands...',
        'owner': None,
    }

    public_safe = {
        'title': u'Total Recall',
        'year': 1990,
    }


class TestThingModel(OnwerOnlyModelSerializer, unittest.TestCase):
    klass = fixtures.ThingModel

    description = {
        'title': u'Thing Model',
        'body': u'Scenester twee mlkshk readymade butcher. Letterpress\nportland +1 salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn\nhelvetica DIY. Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin\nmaster cleanse.\n',
        'liked': True,
        'archived': False,
        'deleted': False,
    }

    owner_safe = {
        'title': u'Thing Model',
        'body': u'Scenester twee mlkshk readymade butcher. Letterpress\nportland +1 salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn\nhelvetica DIY. Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin\nmaster cleanse.\n',
        'liked': True,
        'archived': False,
        'deleted': False,
    }

    public_safe = {}


class TestEmbeddedDocs(ModelSerializer, unittest.TestCase):
    klass = fixtures.BlogPost

    description = {
        'title': u'Hipster Hodgepodge',
        'content': u'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n',
        'author': {
            'username': u'j2d2',
            'name': u'james',
            'a_setting': True,
            'is_active': True,
            'email': u'jdennis@gmail.com'
        },
        'comments': [
            {
                'username': u'bro',
                'text': u'This post was awesome!',
                'email': u'bru@dudegang.com',
            },
            {
                'username': u'barbie',
                'text': u'This post is ridiculous',
                'email': u'barbie@dudegang.com',
            }
        ],
        'deleted': False,
    }

    owner_safe = {
        'author': {
            'username': 'j2d2',
            'a_setting': True,
            'name': 'james',
            'email': 'jdennis@gmail.com'
        },
        'deleted': False,
        'title': 'Hipster Hodgepodge',
        'comments': [
            {
                'username': 'bro',
                'text': 'This post was awesome!',
                'email': 'bru@dudegang.com'
            },
            {
                'username': 'barbie',
                'text': 'This post is ridiculous',
                'email': 'barbie@dudegang.com'
            }
        ],
        'content': 'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n'
    }

    public_safe = {
        'author': {
            'name': 'james',
            'username': 'j2d2',
        },
        'comments': [
            {
                'username': 'bro',
                'text': 'This post was awesome!',
            },
            {
                'username': 'barbie',
                'text': 'This post is ridiculous',
            }
        ],
        'content': 'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n'
    }


class TestAltFieldNames(unittest.TestCase):
    klass = fixtures.AltNames

    def setUp(self):
        self.description = {'something_else': 'whatever'}
        self.instance = self.klass(self.description)

    def test_serialize_print_names(self):
        self.assertEqual(self.instance.title, 'whatever')

        self.assertEqual(self.instance.serialize(), self.description)
