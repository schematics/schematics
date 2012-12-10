#!/usr/bin/env python


import unittest
import json
import datetime
import copy

from schematics.models import Model
from schematics.serialize import (to_python, to_json, make_safe_python,
                                  make_safe_json)

import fixtures
from fixtures import Model


class ModelSerializer:
    ### Subclass overrides these
    klass = None 
    description = dict()
    owner_safe = dict()
    public_safe = dict()
    
    def setUp(self):
        self.instance = self.klass(**self.description)
        self.as_python = to_python(self.instance)
        self.as_json = to_json(self.instance, sort_keys=True)
        self.json_owner_safe = json.dumps(self.owner_safe, sort_keys=True)
        self.json_public_safe = json.dumps(self.public_safe, sort_keys=True)

    def test_instance_to_python(self):
        self.assertEquals(self.as_python, self.description)

    def test_instance_to_json(self):
        self.assertEquals(self.as_json, json.dumps(self.description,
                                                   sort_keys=True))

    def test_owner_safe(self):
        owner_safe = make_safe_python(self.klass, self.instance, 'owner')
        self.assertEqual(self.owner_safe, owner_safe)

    def test_json_owner_safe(self):
        json_owner_safe = make_safe_json(self.klass, self.instance, 'owner',
                                         sort_keys=True)
        self.assertEqual(self.json_owner_safe, json_owner_safe)

    def test_public_safe(self):
        public_safe = make_safe_python(self.klass, self.instance, 'public')
        self.assertEqual(self.public_safe, public_safe)

    def test_json_public_safe(self):
        json_public_safe = make_safe_json(self.klass, self.instance, 'public',
                                          sort_keys=True)
        self.assertEqual(self.json_public_safe, json_public_safe)


class TestSimpleModel(ModelSerializer, unittest.TestCase):
    klass = fixtures.SimpleModel
    
    description = {
        'title' : u'Misc Doc',
    }
    
    owner_safe = {
        'title': u'Misc Doc',
    }
    
    public_safe = {}


class TestSubModel(ModelSerializer, unittest.TestCase):
    klass = fixtures.SubModel
    
    description = {
        'title': u'Total Recall',
        'year': 1990,
        'thoughts': u'I wish I had three hands...',
    }
    
    owner_safe = {
        'title': u'Total Recall',
        'year': 1990,
        'thoughts': u'I wish I had three hands...',
    }
    
    public_safe = {
        'title': u'Total Recall',
        'year': 1990,
    }


class TestThingModel(ModelSerializer, unittest.TestCase):
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
        description = {'something_else': 'whatever'}
        self.instance = self.klass(**description)

    def test_serialize_print_names(self):
        x = to_python(self.instance)
        self.assertEqual(x['something_else'], 'whatever')
        self.assertEqual(self.instance.title, 'whatever')
