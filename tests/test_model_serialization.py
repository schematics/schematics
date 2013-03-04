#!/usr/bin/env python


"""Comment
"""


import unittest
import json
import datetime
import copy

from schematics.base import json
from schematics.models import Model
from schematics.serialize import to_jsonschema, from_jsonschema

import fixtures
from fixtures import SimpleModel


class FixtureMixin():
    """This class provides the commonly used calls, assuming they're applied
    to multiple different structures. It is intended for use with
    `unittest.TestCase` as the provided functions adhere to `test_*` naming for
    test methods.

    You will need to define:

        `self.klass`: a DictShield document class
        
        `self.jsonschema`: the JSON schema you expect the class to turn into
                           from klass.to_jsonschema()
    """
    def test_class_to_jsonschema(self):
        """Tests whether or not the test jsonschema matches what the test class
        returns for `to_jsonschema()`.
        """
        self.assertDictContainsSubset(self.jsonschema, json.loads(to_jsonschema(self.klass)))

    def test_class_from_jsonschema(self):
        """Tests loading the jsonschema into a Document instance and
        serializing back out to jsonschema via a comparison to the jsonschema
        provided by the test.
        """
        if issubclass(self.klass, SimpleModel):
            there = from_jsonschema(self.jsonschema, self.klass)
            andbackagain = to_jsonschema(there)
            jsonschema = json.loads(andbackagain)
            self.assertDictContainsSubset(self.jsonschema, jsonschema)
                              

class TestSimpleModel(unittest.TestCase, FixtureMixin):
    klass = fixtures.SimpleModel
    jsonschema = {
        u'title' : u'SimpleModel',
        u'type'  : u'object',
        u'properties': {
            u'owner' : {
                u'type' : u'string',
                u'title': u'owner',
            },
            u'title' : {
                u'type' : u'string',
                u'title': u'title',
                u'maxLength': 40,
            }
        }
    }


class TestSubModel(unittest.TestCase, FixtureMixin):
    klass = fixtures.SubModel
    jsonschema = {
        u'title' : u'SubModel',
        u'type'  : u'object',
        u'properties' : {
            u'thoughts' : {
                u'maxLength': 255,
                u'type'     : u'string',
                u'title'    : u'thoughts'
            },
            u'year' : {
                u'maximum': datetime.datetime.now().year,
                u'minimum': 1950,
                u'title'  : u'year',
                u'type'   : u'number'
            },
            u'owner' : {
                u'type' : u'string',
                u'title': u'owner',
            },
            u'title' : {
                u'type' : u'string',
                u'title': u'title',
                u'maxLength': 40,
            }
        }
    }



class TestAuthor(unittest.TestCase, FixtureMixin):
    klass = fixtures.Author
    jsonschema = {
        u'title' : u'Author',
        u'type'  : u'object',
        u'properties' : {
            u'name' : {
                u'title' : u'name',
                u'type'  : u'string' },
            u'username' : {
                u'title' : u'username',
                u'type'  : u'string' },
            u'a_setting': {
                u'type': u'boolean',
                u'title': u'a_setting'},
            u'is_active': {
                u'type': u'boolean',
                u'title': u'is_active'},
            u'email': {
                u'format': u'email',
                u'type': u'string',
                u'title': u'email'},
            }}


class TestComment(unittest.TestCase, FixtureMixin):
    klass = fixtures.Comment
    jsonschema = {
        u'title' : u'Comment',
        u'type'  : u'object',
        u'properties' : {
            u'text' : {
                u'title' : u'text',
                u'type'  : u'string' },
            u'username' : {
                u'title' : u'username',
                u'type'  : u'string' },
            u'email': {
                u'format': u'email',
                u'type': u'string',
                u'title': u'email'},
            }
        }


class TestBlogPost(unittest.TestCase, FixtureMixin):
    klass = fixtures.BlogPost
    jsonschema = {
        u'title' : u'BlogPost',
        u'type' : u'object',
        u'properties' : {
            u'deleted': {
                u'type': u'boolean',
                u'title': u'deleted'},
            u'content': {
                u'type': u'string',
                u'title': u'content'},
            u'title': {
                u'type': u'string',
                u'title': u'title'},
            u'comments': {
                u'items': [{
                    u'type': u'object',
                    u'properties': {
                        u'username': {
                            u'type': u'string',
                            u'title': u'username'},
                        u'text': {
                            u'type': u'string',
                            u'title': u'text'},
                        u'email': {
                            u'format': u'email',
                            u'type': u'string',
                            u'title': u'email'}
                        },
                    u'title': u'Comment'}],
                u'type': u'array',
                u'title': u'comments'},
            u'author': {
                u'type': u'object',
                u'properties': {
                    u'username': {
                        u'type': u'string',
                        u'title': u'username'},
                    u'a_setting': {
                        u'type': u'boolean',
                        u'title': u'a_setting'},
                    u'is_active': {
                        u'type': u'boolean',
                        u'title': u'is_active'},
                    u'name': {
                        u'type': u'string',
                        u'title': u'name'},
                    u'email': {
                        u'format': u'email',
                        u'type': u'string',
                        u'title': u'email'},
                    },
                u'title': u'Author'
            }
        }
    }


class TestAction(unittest.TestCase, FixtureMixin):
    klass = fixtures.Action
    jsonschema = {
        u'title' : u'Action',
        u'type'  : u'object',
        u'properties' : {
            u'value' : {
                u'title'    : u'value',
                u'required' : True,
                u'maxLength': 256,
                u'type'     : u'string' },
            u'tags' : {
                u'title'  : u'tags',
                u'type'   : u'array',
                u'items'  : [{ u'type' : u'string' }]}}}


class TestSingleTask(unittest.TestCase, FixtureMixin):
    klass = fixtures.SingleTask
    jsonschema = {
        u'title' : u'SingleTask',
        u'type'  : u'object',
        u'properties' : {
            u'action': {
                u'type': u'object',
                u'properties': {
                    u'value': {
                        u'maxLength': 256,
                        u'required': True,
                        u'type': u'string',
                        u'title': u'value'},
                    u'tags': {
                        u'items': [{u'type': u'string'}],
                        u'type': u'array',
                        u'title': u'tags'}
                },
                u'title': u'Action',
            },
            u'created_date': {
                u'type'   : u'string',
                u'format' : u'date-time',
                u'title'  : u'created_date'
            }
        }
    }


class TestTaskList(unittest.TestCase, FixtureMixin):
    klass = fixtures.TaskList
    jsonschema = {
        u'title' : 'TaskList',
        u'type'  : 'object',
        u'properties' : {
            u'actions' : {
                u'type'   : u'array',
                u'title'  : u'actions',
                u'items'  : [TestAction.jsonschema ]},
            u'created_date' : {
                u'title'  : u'created_date',
                u'type'   : u'string',
                u'format' : u'date-time'
            },
            u'updated_date' : {
                u'title'  : u'updated_date',
                u'type'   : u'string',
                u'format' : u'date-time'
            },
            u'num_completed' : {
                u'type'   : u'number',
                u'title'  : u'num_completed',
                u'default': 0,
            }
        }
    }


class TestBasicUser(unittest.TestCase, FixtureMixin):
    klass = fixtures.BasicUser
    jsonschema = {
        u'title' : u'BasicUser',
        u'type'  : u'object',
        u'properties' : {
            u'name' : {
                u'type'     : u'string',
                u'title'    : u'name',
                u'maxLength': 50,
                u'required' : True },
            u'bio'  : {
                u'type'     : u'string',
                u'title'    : u'bio',
                u'maxLength': 100 },
            u'secret': {
                u'minLength': 32,
                u'maxLength': 32,
                u'type': u'any',
                u'title': u'secret'},
            }}


if __name__ == '__main__':
    unittest.main()
