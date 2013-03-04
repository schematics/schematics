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
        self.assertEquals(self.jsonschema, json.loads(to_jsonschema(self.klass)))

    def test_class_from_jsonschema(self):
        """Tests loading the jsonschema into a Document instance and
        serializing back out to jsonschema via a comparison to the jsonschema
        provided by the test.
        """
        if issubclass(self.klass, SimpleModel):
            there = from_jsonschema(self.jsonschema, self.klass)
            andbackagain = to_jsonschema(there)
            jsonschema = json.loads(andbackagain)
            self.assertEquals(self.jsonschema, jsonschema)
                              

class TestSimpleModel(unittest.TestCase, FixtureMixin):
    klass = fixtures.SimpleModel
    jsonschema = {
        'title' : 'SimpleModel',
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
                'maxLength': 40 }}}


class TestSubModel(unittest.TestCase, FixtureMixin):
    klass = fixtures.SubModel
    jsonschema = {
        'title' : 'SubModel',
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



class TestAuthor(unittest.TestCase, FixtureMixin):
    klass = fixtures.Author
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
    klass = fixtures.Comment
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
    klass = fixtures.BlogPost
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
    klass = fixtures.Action
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
    klass = fixtures.SingleTask
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
    klass = fixtures.TaskList
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
    klass = fixtures.BasicUser
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
