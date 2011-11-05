import unittest
import json
import datetime
import copy
from fixtures import demos

class TestMedia(unittest.TestCase):
    
    def test_media_instance_to_json(self):
        
        obj_from_json = json.loads(demos.m.to_json())
        self.assertEquals(36, len(obj_from_json.pop('_id')))
        self.assertEquals({
                u'_cls'  : u'Media',
                u'_types': [u'Media'],
                u'title' : u'Misc Media'
                }, obj_from_json)
        
        
    def test_media_class_to_jsonschema(self):
        self.assertEquals({
                'title' : 'Media',
                'type'  : 'object',
                'properties': {
                    'id' : { 'type' : 'string' },
                    'owner' : {
                        'type' : 'string',
                        'title': 'owner'
                        },
                    'title' : {
                        'type' : 'string',
                        'title': 'title',
                        'maxLength': 40
                        }
                    }}, json.loads(demos.Media.to_jsonschema())
                          )

class TestMovie(unittest.TestCase):
    
    def test_movie_instance_to_json(self):
        obj_from_json = json.loads(demos.mv.to_json())
        
        self.assertEquals(36, len(obj_from_json.pop('_id')))
        self.assertEquals({
                u'_cls'  : u'Media.Movie',
                u'_types': [u'Media', u'Media.Movie'],
                u'title' : u'Total Recall',
                u'year'  : 1990,
                u'personal_thoughts' : u'I wish I had three hands...'
                }, obj_from_json)
        
    def test_movie_class_to_jsonschema(self):
        self.assertEquals({
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
                        'type'   : 'integer' }}},
                          json.loads(demos.Movie.to_jsonschema()))

class TestProduct(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_product_instance_to_json(self):
        pass
    
    PRODUCT_SCHEMA = {
        'type' : 'object',
        'title': 'Product',
        'properties': {
            'sku'     : {
                'type'     : 'integer',
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
                'type' : 'integer',
                'title': 'num_in_stock' }}}

    def test_product_class_to_jsonschema(self):
        self.assertEquals(self.PRODUCT_SCHEMA, json.loads(demos.Product.to_jsonschema()))

class TestOrder(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_order_instance_to_json(self):
        pass

    ORDER_SCHEMA = {
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
                'items' : TestProduct.PRODUCT_SCHEMA },
            'total' : {
                'type' : 'number',
                'title': 'total'}}}
    
    def test_order_class_to_jsonschema(self):
        self.assertEquals(self.ORDER_SCHEMA, json.loads(demos.Order.to_jsonschema()))

class TestUser(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_user_instance_to_json(self):
        pass

    USER_SCHEMA = {
        'type'   : 'object',
        'title'  : 'User',
        'properties': {
            'id'       : { 'type' : 'string' },
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

    def test_user_class_to_jsonschema(self):
        self.assertEquals(self.USER_SCHEMA, json.loads(demos.User.to_jsonschema()))

class TestCustomer(unittest.TestCase):
    
    CUSTOMER_SCHEMA = copy.copy(TestUser.USER_SCHEMA)
    CUSTOMER_PROPERTIES = copy.copy(TestUser.USER_SCHEMA['properties'])
    CUSTOMER_PROPERTIES.update({
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
                        'items'    : TestOrder.ORDER_SCHEMA }})
    CUSTOMER_SCHEMA.update({
            'title'      : 'Customer',
            'properties' : CUSTOMER_PROPERTIES })

    @unittest.skip('Tests for instance not yet written.')
    def test_customer_instance_to_json(self):
        pass

    def test_customer_class_to_jsonschema(self):
        self.assertEquals(self.CUSTOMER_SCHEMA, json.loads(demos.Customer.to_jsonschema()))

class TestSomeDoc(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_somedoc_instance_to_json(self):
        pass
    
    SOME_DOC_SCHEMA = {
        'type'   : 'object',
        'title'  : 'SomeDoc',
        'properties': {
            'id' : { 'type' : 'string' },
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

    def test_somedoc_class_to_jsonschema(self):
        self.assertEquals(self.SOME_DOC_SCHEMA, json.loads(demos.SomeDoc.to_jsonschema()))

class TestAuthor(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_author_instance_to_json(self):
        pass
    
    AUTHOR_SCHEMA = {
        'title' : 'Author',
        'type'  : 'object',
        'properties' : {
            'name' : {
                'title' : 'name',
                'type'  : 'string' },
            'username' : {
                'title' : 'username',
                'type'  : 'string' }}}

    def test_author_class_to_jsonschema(self):
        self.assertEquals(self.AUTHOR_SCHEMA, json.loads(demos.Author.to_jsonschema()))

class TestComment(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_comment_instance_to_json(self):
        pass
    
    # only public fields should appear in the schema.
    COMMENT_SCHEMA = {
        'title' : 'Comment',
        'type'  : 'object',
        'properties' : {
            'text' : {
                'title' : 'text',
                'type'  : 'string' },
            'username' : {
                'title' : 'username',
                'type'  : 'string' }}}

    def test_comment_class_to_jsonschema(self):
        self.assertEquals(self.COMMENT_SCHEMA, json.loads(demos.Comment.to_jsonschema()))

class TestBlogPost(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_blog_post_instance_to_json(self):
        pass
    
    # only public fields should appear in the schema.
    BLOG_POST_SCHEMA = {
        'title' : 'BlogPost',
        'type'  : 'object',
        'properties' : {
            'author' : TestAuthor.AUTHOR_SCHEMA,
            'comments' : {
                'title' : 'comments',
                'type'  : 'array',
                'items' : TestComment.COMMENT_SCHEMA },
            'content' : {
                'title' : 'content',
                'type'  : 'string' }}}
    
    def test_blog_post_class_to_jsonschema(self):
        self.assertEquals(self.BLOG_POST_SCHEMA, json.loads(demos.BlogPost.to_jsonschema()))

class TestAction(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_action_instance_to_json(self):
        pass
    
    ACTION_SCHEMA = {
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
                'items'  : { 'type' : 'string' }}}}
    
    def test_action_class_to_jsonschema(self):
        self.assertEquals(self.ACTION_SCHEMA, json.loads(demos.Action.to_jsonschema()))

class TestSingleTask(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_single_task_instance_to_json(self):
        pass
    
    SINGLE_TASK_SCHEMA = {
        'title' : 'SingleTask',
        'type'  : 'object',
        'properties' : {
            'id' : { 'type' : 'string' },
            'action'       : TestAction.ACTION_SCHEMA,
            'created_date' : {
                'type'   : 'string',
                'format' : 'date-time',
                'title'  : 'created_date' }}}
    
    def test_single_task_class_to_jsonschema(self):
        self.assertEquals(self.SINGLE_TASK_SCHEMA, json.loads(demos.SingleTask.to_jsonschema()))

class TestTaskList(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_task_list_instance_to_json(self):
        pass
    
    TASK_LIST_SCHEMA = {
        'title' : 'TaskList',
        'type'  : 'object',
        'properties' : {
            'id' : { 'type' : 'string' },
            'actions' : {
                'type'   : 'array',
                'title'  : 'actions',
                'items'  : TestAction.ACTION_SCHEMA },
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
                'type'   : 'integer',
                'title'  : 'num_completed',
                'default': 0 }}}
    
    def test_task_list_class_to_jsonschema(self):
        self.assertEquals(self.TASK_LIST_SCHEMA, json.loads(demos.TaskList.to_jsonschema()))

class TestBasicUser(unittest.TestCase):
    @unittest.skip('Tests for instance not yet written.')
    def test_basic_user_instance_to_json(self):
        pass
    
    # only public fields should appear in schema
    BASIC_USER_SCHEMA = {
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
    
    def test_basic_user_class_to_jsonschema(self):
        self.assertEquals(self.BASIC_USER_SCHEMA, json.loads(demos.BasicUser.to_jsonschema()))

if __name__ == '__main__':
    unittest.main()

