

"""These are tests that attempt to convert the DictShield classes and
instances from fixtures/demos.py to and from JSON.

Instances are created through a DictShield class and compared to JSON,
testing the .to_json(self) instance method.

Classes are converted into JSON schema, testing the .to_jsonschema(cls)
DictShield class method.  Classes are also built from JSON schema, and then
converted back into JSON schema to test Document.from_jsonschema().
"""

import unittest
import json
import datetime
import copy
from dictshield.base import json
from dictshield.document import Document
from fixtures import demos
from fixtures.demos import Document

def skipIfUndefined(attribute, message):
    """This decorator will skip `testFunc' with `msg' if `attribute' is
    not defined in the test class in which the decorator is used.

    Example:
    @skipIfUndefined('foo', 'Your foo is weak!')
    def myTest(self):
      assertEquals('bar', self.foo)
    """
    def wrapper(testFunc):
        def wrapped(self):
            if hasattr(self, attribute):
                return testFunc(self)
            else:
                @unittest.skip(message)
                def skipped(self):
                    pass
                return skipped(self)

        return wrapped
    return wrapper

class FixtureMixin():
    """Make sure to mix this in to a class that is descended from
    unittest.TestCase .  You will need to define:

    self.instance   : a DictShield document instance
    self.klass      : a DictShield document class
    self.json       : the JSON you expect the instance to turn into from
                      instance.to_json()
    self.jsonschema : the JSON schema you expect the class to turn into
                      from klass.to_jsonschema()

    Tests will be skipped otherwise.
    """

    @skipIfUndefined('json', 'Instance JSON not provided.')
    def test_instance_to_json(self):
        obj_from_json = json.loads(self.instance.to_json())
        self.assertEquals(36, len(obj_from_json.pop('_id')))
        self.assertEquals(self.json, obj_from_json)

    @skipIfUndefined('jsonschema', 'JSON schema not provided.')
    def test_class_to_jsonschema(self):
        self.assertEquals(self.jsonschema, json.loads(self.klass.to_jsonschema()))

    @skipIfUndefined('jsonschema', 'JSON schema not provided.')
    def test_class_from_jsonschema(self):
        if issubclass(self.klass, Document) and not self.klass._public_fields:
            self.assertEquals(self.jsonschema, json.loads(Document.from_jsonschema(self.jsonschema).to_jsonschema()))


class TestMedia(unittest.TestCase, FixtureMixin):
    instance = demos.m
    klass = demos.Media
    json = {
        u'_cls'  : u'Media',
        u'_types': [u'Media'],
        u'title' : u'Misc Media'
        }
    jsonschema = {
        'title' : 'Media',
        'type'  : 'object',
        'properties': {
            '_id' : { 'type' : 'string' },
            'owner' : {
                'type' : 'string',
                'title': 'owner'
                },
            'title' : {
                'type' : 'string',
                'title': 'title',
                'maxLength': 40
                }
            }}

class TestMovie(unittest.TestCase, FixtureMixin):
    instance = demos.mv
    klass = demos.Movie
    json = { u'_cls'  : u'Media.Movie',
             u'_types': [u'Media', u'Media.Movie'],
             u'title' : u'Total Recall',
             u'year'  : 1990,
             u'personal_thoughts' : u'I wish I had three hands...' }
    jsonschema = {
        'title' : 'Movie',
        'type'  : 'object',
        'properties' : {
            'title' : {
                'maxLength': 40,
                'type'     : 'string',
                'title'    : 'title' },
            'year' : {
                'maximum': datetime.datetime.now().year,
                'minimum': 1950,
                'title'  : 'year',
                'type'   : 'number' }}}

class TestProduct(unittest.TestCase, FixtureMixin):
    klass = demos.Product
    jsonschema = {
        'type' : 'object',
        'title': 'Product',
        'properties': {
            'sku'     : {
                'type'     : 'number',
                'title'    : 'sku',
                'required' : True,
                'minimum'  : 1,
                'maximum'  : 9999 },
            'title'   : {
                'type'     : 'string',
                'title'    : 'title',
                'required' : True,
                'maxLength': 30 },
            'description' : {
                'type' : 'string',
                'title': 'description' },
            'price' : {
                'type'     : 'number',
                'title'    : 'price',
                'required' : True },
            'num_in_stock' : {
                'type' : 'number',
                'title': 'num_in_stock' }}}

class TestOrder(unittest.TestCase, FixtureMixin):
    klass = demos.Order
    jsonschema = {
        'type' : 'object',
        'title': 'Order',
        'properties': {
            'date_made': {
                'title'   : 'date_made',
                'type'    : 'string',
                'format'  : 'date-time',
                'required': True },
            'date_changed' : {
                'title'   : 'date_changed',
                'type'    : 'string',
                'format'  : 'date-time' },
            'line_items' : {
                'type'  : 'array',
                'title' : 'line_items',
                'items' : [TestProduct.jsonschema]},
            'total' : {
                'type' : 'number',
                'title': 'total'}}}

class TestUser(unittest.TestCase, FixtureMixin):
    klass = demos.User
    jsonschema = {
        'type'   : 'object',
        'title'  : 'User',
        'properties': {
            '_id'       : {'type' : 'string', },
            'username' : {
                'type'      : 'string',
                'title'     : 'username',
                'minLength' : 2,
                'maxLength' : 20,
                'required'  : True },
            'email' : {
                'type'      : 'string',
                'title'     : 'email',
                'format'    : 'email',
                'maxLength' : 30,
                'required'  : True }}}

class TestCustomer(unittest.TestCase, FixtureMixin):
    klass = demos.Customer
    jsonschema = copy.copy(TestUser.jsonschema)
    customer_properties = copy.copy(TestUser.jsonschema['properties'])
    customer_properties.update({
                    'date_made' : {
                        'title'   : 'date_made',
                        'type'    : 'string',
                        'format'  : 'date-time',
                        'required': True },
                    'first_name' : {
                        'title'    : 'first_name',
                        'type'     : 'string',
                        'maxLength': 20,
                        'required' : True },
                    'last_name' : {
                        'title'    : 'last_name',
                        'type'     : 'string',
                        'maxLength': 30,
                        'required' : True },
                    'orders' : {
                        'title'    : 'orders',
                        'type'     : 'array',
                        'items'    : [TestOrder.jsonschema] }})
    jsonschema.update({
            'title'      : 'Customer',
            'properties' : customer_properties })

class TestSomeDoc(unittest.TestCase, FixtureMixin):
    klass = demos.SomeDoc
    jsonschema = {
        'type'   : 'object',
        'title'  : 'SomeDoc',
        'properties': {
            '_id' : { 'type' : 'string' },
            'liked' : {
                'title'  : 'liked',
                'type'   : 'boolean',
                'default': False },
            'archived' : {
                'title'  : 'archived',
                'type'   : 'boolean',
                'default': False },
            'deleted' : {
                'title'  : 'deleted',
                'type'   : 'boolean',
                'default': False },
            'title' : {
                'title'  : 'title',
                'type'   : 'string' },
            'body'  : {
                'title'  : 'body',
                'type'   : 'string' }}}

class TestAuthor(unittest.TestCase, FixtureMixin):
    klass = demos.Author
    jsonschema = {
        'title' : 'Author',
        'type'  : 'object',
        'properties' : {
            'name' : {
                'title' : 'name',
                'type'  : 'string' },
            'username' : {
                'title' : 'username',
                'type'  : 'string' }}}

class TestComment(unittest.TestCase, FixtureMixin):
    klass = demos.Comment
    jsonschema = {
        'title' : 'Comment',
        'type'  : 'object',
        'properties' : {
            'text' : {
                'title' : 'text',
                'type'  : 'string' },
            'username' : {
                'title' : 'username',
                'type'  : 'string' }}}

class TestBlogPost(unittest.TestCase, FixtureMixin):
    klass = demos.BlogPost
    jsonschema = {
        'title' : 'BlogPost',
        'type'  : 'object',
        'properties' : {
            'author' : TestAuthor.jsonschema,
            'comments' : {
                'title' : 'comments',
                'type'  : 'array',
                'items' : [TestComment.jsonschema] },
            'content' : {
                'title' : 'content',
                'type'  : 'string' }}}

class TestAction(unittest.TestCase, FixtureMixin):
    klass = demos.Action
    jsonschema = {
        'title' : 'Action',
        'type'  : 'object',
        'properties' : {
            'value' : {
                'title'    : 'value',
                'required' : True,
                'maxLength': 256,
                'type'     : 'string' },
            'tags' : {
                'title'  : 'tags',
                'type'   : 'array',
                'items'  : [{ 'type' : 'string' }]}}}

class TestSingleTask(unittest.TestCase, FixtureMixin):
    klass = demos.SingleTask
    jsonschema = {
        'title' : 'SingleTask',
        'type'  : 'object',
        'properties' : {
            '_id' : { 'type' : 'string' },
            'action'       : TestAction.jsonschema,
            'created_date' : {
                'type'   : 'string',
                'format' : 'date-time',
                'title'  : 'created_date' }}}

class TestTaskList(unittest.TestCase, FixtureMixin):
    klass = demos.TaskList
    jsonschema = {
        'title' : 'TaskList',
        'type'  : 'object',
        'properties' : {
            '_id' : { 'type' : 'string' },
            'actions' : {
                'type'   : 'array',
                'title'  : 'actions',
                'items'  : [TestAction.jsonschema ]},
            'created_date' : {
                'title'  : 'created_date',
                'type'   : 'string',
                'format' : 'date-time' },
            #'default': datetime.datetime.now },
            'updated_date' : {
                'title'  : 'updated_date',
                'type'   : 'string',
                'format' : 'date-time' },
            # 'default': datetime.datetime.now },
            'num_completed' : {
                'type'   : 'number',
                'title'  : 'num_completed',
                'default': 0 }}}

class TestBasicUser(unittest.TestCase, FixtureMixin):
    klass = demos.BasicUser
    jsonschema = {
        'title' : 'BasicUser',
        'type'  : 'object',
        'properties' : {
            'name' : {
                'type'     : 'string',
                'title'    : 'name',
                'maxLength': 50,
                'required' : True },
            'bio'  : {
                'type'     : 'string',
                'title'    : 'bio',
                'maxLength': 100 }}} # baby bio!

if __name__ == '__main__':
    unittest.main()

