"""From Media class to json structure:

    {"_types": ["Media"], "_cls": "Media", "title": "Misc Media"}

From Movie class to json structure:

    {"personal_thoughts": "I wish I had three hands...", "_types": ["Media", "Media.Movie"], "title": "Total Recall", "_cls": "Media.Movie", "year": 1990}

Making mv json safe:

    {"personal_thoughts": "I wish I had three hands...", "title": "Total Recall", "year": 1990}

Making mv json public safe (only ['title', 'year'] should show):
    
    {"title": "Total Recall", "year": 1990}
"""

import datetime

from dictshield.base import ShieldException
from dictshield.document import Document, EmbeddedDocument

from dictshield.fields import (BaseField,
                               IntField,
                               BooleanField,
                               StringField,
                               FloatField,
                               DateTimeField,
                               EmailField,
                               MD5Field)

from dictshield.fields.compound import ListField, EmbeddedDocumentField
from dictshield.fields.bson import ObjectIdField
import hashlib
import json

###
### The base class
###

class Media(Document):
    """Simple document that has one StringField member
    """
    owner = ObjectIdField() # probably set required=True
    title = StringField(max_length=40)

m = Media()
m.title = 'Misc Media'
#print 'From Media class to json structure:\n\n    %s\n' % (m.to_json())

###
### Subclass `Media` to create a `Movie`
###

class Movie(Media):
    """Subclass of Foo. Adds bar and limits publicly shareable
    fields to only 'title' and 'year'.
    """
    _public_fields = ['title','year']
    year = IntField(min_value=1950, max_value=datetime.datetime.now().year)
    personal_thoughts = StringField(max_length=255)
mv = Movie()
mv.title = 'Total Recall'
mv.year = 1990
mv.personal_thoughts = 'I wish I had three hands...' # (.Y.Y.)
#print 'From Movie class to json structure:\n\n    %s\n' % (mv.to_json())

###
### Scrubbing functions
###

ownersafe_json = Movie.make_json_ownersafe(mv)
ownersafe_str = 'Making mv json safe:\n\n    %s\n'
#print ownersafe_str % (ownersafe_json)

publicsafe_json = Movie.make_json_publicsafe(mv)
publicsafe_str = 'Making mv json public safe (only %s should show):\n\n    %s\n'
#print  publicsafe_str % (Movie._public_fields, publicsafe_json)

"""PYTHON:
    {
      'username': u'ben',
      '_types': ['User', 'User.Customer'],
      'first_name': u'Ben',
      'last_name': u'G',
      'date_made': datetime.datetime(2011, 8, 7, 4, 21, 22, 783762),
      'orders': [<Order: Order object>],
      '_cls': 'User.Customer',
      'email': u'ben@ben.com'
    } 

JSON:
    {
      "username": "ben",
      "_types": ["User", "User.Customer"],
      "first_name": "Ben",
      "last_name": "G",
      "date_made": "2011-08-07T04:21:22.783762",
      "orders": [
        {
          "_types": ["Order"],
          "line_items": [
            {
              "sku": 1,
              "_types": ["Product"],
              "description": "A Japanese laquered bowl",
              "title": "Japanese Bowl",
              "price": 3.99,
              "num_in_stock": 3,
              "_cls": "Product"
            }, {
              "sku": 2,
              "_types": ["Product"],
              "description": "An African laquered bowl",
              "title": "African Bowl",
              "price": 3.99,
              "num_in_stock": 4,
              "_cls": "Product"
            }
          ],
          "total": 7.98,
          "date_made": "2011-08-07T04:21:22.783271",
          "_cls": "Order"
        }
      ],
      "_cls": "User.Customer",
      "email": "ben@ben.com"
    } 

Serializing to JSON and reloading...
    
PYTHON:
    {
      'username': u'ben',
      '_types': ['User', 'User.Customer'],
      'first_name': u'Ben',
      'last_name': u'G',
      'date_made': datetime.datetime(2011, 8, 7, 4, 21, 22, 783762),
      'orders': [<Order: Order object>],
      '_cls': 'User.Customer',
      'email': u'ben@ben.com'
    }
    
JSON:
    {
      "username": "ben",
      "_types": ["User", "User.Customer"],
      "first_name": "Ben",
      "last_name": "G",
      "date_made": "2011-08-07T04:21:22.783762",
      "orders": [
        {
          "_types": ["Order"],
          "line_items": [
            {
              "sku": 1,
              "_types": ["Product"],
              "description": "A Japanese laquered bowl",
              "title": "Japanese Bowl",
              "price": 3.99,
              "num_in_stock": 3,
              "_cls": "Product"
            }, {
              "sku": 2,
              "_types": ["Product"],
              "description": "An African laquered bowl",
              "title": "African Bowl",
              "price": 3.99,
              "num_in_stock": 4,
              "_cls": "Product"
            }
          ],
          "total": 7.98,
          "date_made": "2011-08-07T04:21:22.783271",
          "_cls":
          "Order"
        }
      ],
      "_cls": "User.Customer",
      "email": "ben@ben.com"
    } 
"""

###
### Store models
###

class Product(EmbeddedDocument):
    sku = IntField(min_value=1, max_value=9999, required=True)
    title = StringField(max_length = 30, required=True)
    description = StringField()
    price = FloatField(required=True)
    num_in_stock = IntField()

class Order(EmbeddedDocument):
    date_made = DateTimeField(required=True)
    date_changed = DateTimeField()
    line_items = ListField(EmbeddedDocumentField(Product))
    total = FloatField()


###
### User models
###

class User(Document):
    username = StringField(min_length=2, max_length=20, required=True)
    email = EmailField(max_length=30, required=True)

class Customer(User):
    date_made = DateTimeField(required=True)
    first_name = StringField(max_length=20, required=True)
    last_name = StringField(max_length=30, required=True)
    orders = ListField(EmbeddedDocumentField(Order))


###
### Product instances
###

product_a = Product(sku=1,
                    title="Japanese Bowl",
                    description="A Japanese laquered bowl",
                    price=3.99,
                    num_in_stock=3)

product_b = Product(sku=2,
                    title="African Bowl",
                    description="An African laquered bowl",
                    price=3.99,
                    num_in_stock=4)


###
### Order instance
###

order = Order(date_made=datetime.datetime.utcnow(),
              line_items=[product_a,product_b])
order.total=(product_a.price + product_b.price)


###
### Customer instance
###

customer = Customer(username="ben",
                    email="ben@ben.com",
                    first_name="Ben",
                    last_name="G",
                    date_made=datetime.datetime.utcnow(),                    
                    orders=[order])

###
### Serialization
###

### Serialize to Python
#print 'PYTHON:\n', customer.to_python(), '\n'

### Serialize to JSON
#print 'JSON:\n', customer.to_json(), '\n'

### Serialize data to JSON and load back into Python dictionary.
#print 'Serializing to JSON and reloading...\n'
json_data = customer.to_json()
customer_dict = json.loads(json_data)

### Instantiate customer instance from pythonified JSON data
loaded_customer = Customer(**customer_dict)

### Reserialize to Python
#print 'PYTHON:\n', loaded_customer.to_python(), '\n'

### Reserialize to JSON
#print 'JSON:\n', loaded_customer.to_json(), '\n'

"""This thing to notice in this example is that the class hierarchy is not
influenced by subclassing EmbeddedDocuments with meta['mixin'] = True. This
can be useful if you know you're going to use something of an EmbeddedDocument
in the top level document structure

{
    "_cls": "SomeDoc", 
    "_types": [
        "SomeDoc"
    ], 
    "archived": false, 
    "body": "Scenester twee mlkshk readymade butcher. Letterpress portland +1\nsalvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.\nSartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.\n", 
    "deleted": false, 
    "liked": true, 
    "title": "Some Document"
}
"""



class InterestMixin(EmbeddedDocument):
    liked = BooleanField(default=False)
    archived = BooleanField(default=False)
    deleted = BooleanField(default=False)
    meta = {
        'mixin': True,
    }


class SomeDoc(Document, InterestMixin):
    title = StringField()
    body = StringField()


sd = SomeDoc()
sd.title = 'Some Document'
sd.body = """Scenester twee mlkshk readymade butcher. Letterpress portland +1
salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn helvetica DIY.
Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin master cleanse.
"""

sd.liked = True

#print sd.to_json()

"""AUTHOR:
- as python:   {'username': u'j2d2', '_types': ['Author'], 'name': u'james', 'a_setting': True, 'is_active': True, '_cls': 'Author', 'email': u'jdennis@gmail.com'} 

- json owner:  {"username": "j2d2", "name": "james", "a_setting": true, "email": "jdennis@gmail.com"} 

- json public: {"username": "j2d2", "name": "james"} 

COMMENT 1:
- as python:   {'username': u'bro', 'text': u'This post was awesome!', '_types': ['Comment'], 'email': u'bru@dudegang.com', '_cls': 'Comment'} 

- json owner:  {"username": "bro", "text": "This post was awesome!", "email": "bru@dudegang.com"} 

- json public: {"username": "bro", "text": "This post was awesome!"} 

COMMENT 2:
- as python:   {'username': u'barbie', 'text': u'This post is ridiculous', '_types': ['Comment'], 'email': u'barbie@dudegang.com', '_cls': 'Comment'} 

- json owner:  {"username": "barbie", "text": "This post is ridiculous", "email": "barbie@dudegang.com"} 

- json public: {"username": "barbie", "text": "This post is ridiculous"} 

BLOG POST:
- as python:   {'_types': ['BlogPost'], 'author': <Author: Author object>, 'deleted': False, 'title': u'Hipster Hodgepodge', 'comments': [<Comment: Comment object>, <Comment: Comment object>], 'content': u'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n', '_cls': 'BlogPost'} 

- json owner:  {"author": {"username": "j2d2", "name": "james", "a_setting": true, "email": "jdennis@gmail.com"}, "deleted": false, "title": "Hipster Hodgepodge", "comments": [{"username": "bro", "text": "This post was awesome!", "email": "bru@dudegang.com"}, {"username": "barbie", "text": "This post is ridiculous", "email": "barbie@dudegang.com"}], "content": "Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n"} 

- json public: {"author": {"username": "j2d2", "name": "james"}, "comments": [{"username": "bro", "text": "This post was awesome!"}, {"username": "barbie", "text": "This post is ridiculous"}], "content": "Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n"} 
"""



class Author(EmbeddedDocument):
    _private_fields=['is_active']
    _public_fields=['username', 'name']
    name = StringField()
    username = StringField()
    email = EmailField()
    a_setting = BooleanField()
    is_active = BooleanField()


class Comment(EmbeddedDocument):
    _public_fields=['username', 'text']
    text = StringField()
    username = StringField()
    email = EmailField()   


class BlogPost(Document):
    _private_fields=['personal_thoughts']
    _public_fields=['author', 'content', 'comments']
    title = StringField()    
    content = StringField()
    author = EmbeddedDocumentField(Author)
    comments = ListField(EmbeddedDocumentField(Comment))
    deleted = BooleanField()   
    

author = Author(name='james', username='j2d2', email='jdennis@gmail.com',
                a_setting=True, is_active=True)
# print 'AUTHOR:'
# print '- as python:  ', author.to_python(), '\n'
# print '- json owner: ', Author.make_json_ownersafe(author), '\n'
# print '- json public:', Author.make_json_publicsafe(author), '\n'

comment1 = Comment(text='This post was awesome!', username='bro',
                   email='bru@dudegang.com')
# print 'COMMENT 1:'
# print '- as python:  ', comment1.to_python(), '\n'
# print '- json owner: ', Comment.make_json_ownersafe(comment1), '\n'
# print '- json public:', Comment.make_json_publicsafe(comment1), '\n'

comment2 = Comment(text='This post is ridiculous', username='barbie',
                   email='barbie@dudegang.com')
# print 'COMMENT 2:'
# print '- as python:  ', comment2.to_python(), '\n'
# print '- json owner: ', Comment.make_json_ownersafe(comment2), '\n'
# print '- json public:', Comment.make_json_publicsafe(comment2), '\n'

content = """Retro single-origin coffee chambray stumptown, scenester VHS
bicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free
trust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed
"""

blogpost = BlogPost(title='Hipster Hodgepodge', author=author, content=content,
                    comments=[comment1, comment2], deleted=False)
# print 'BLOG POST:'
# print '- as python:  ', blogpost.to_python(), '\n'
# print '- json owner: ', BlogPost.make_json_ownersafe(blogpost), '\n'
# print '- json public:', BlogPost.make_json_publicsafe(blogpost), '\n'

"""ACTION: # As Python, then JSON

     {
       '_types': ['Action'],
       '_cls': 'Action',
       'value': u'Hello Mike',
       'tags': [u'Erlang', u'Mike Williams']
     }
     {
       "_types": ["Action"],
       "_cls": "Action",
       "value": "Hello Joe",
       "tags": ["Erlang", "Joe Armstrong"]
     }

SINGLETASK: # As Python, then JSON

     {
       'action': <Action: Action object>,
       '_types': ['SingleTask'],
       '_cls': 'SingleTask',
       'created_date': datetime.datetime(2011, 8, 7, 1, 41, 46, 363909)
     }
     {
       "action": {
         "_types": ["Action"],
         "_cls": "Action",
         "value": "Hello Mike",
         "tags": ["Erlang", "Mike Williams"]
       },
       "_types": ["SingleTask"],
       "_cls": "SingleTask",
       "created_date": "2011-08-07T01:41:46.363909"
     }

TASKLIST: # As Python, then JSON

     {
       'updated_date': datetime.datetime(2011, 8, 7, 1, 41, 46, 364019),
       '_types': ['TaskList'],
       'num_completed': 0,
       'actions': [<Action: Action object>, <Action: Action object>],
       '_cls': 'TaskList',
       'created_date': datetime.datetime(2011, 8, 7, 1, 41, 46, 364031)
     }
     {
       "updated_date": "2011-08-07T01:41:46.364019",
       "_types": ["TaskList"],
       "num_completed": 0,
       "actions": [
         {
           "_types": ["Action"],
           "_cls": "Action",
           "value": "Hello Mike",
           "tags": ["Erlang", "Mike Williams"]
         }, {
           "_types": ["Action"],
           "_cls": "Action",
           "value": "Hello Joe",
           "tags": ["Erlang", "Joe Armstrong"]
         }
       ],
       "_cls": "TaskList",
       "created_date": "2011-08-07T01:41:46.364031"
     }
"""



###
### Models
###

class Action(EmbeddedDocument):
    """An `Action` associates an action name with a list of tags.
    """
    value = StringField(required=True, max_length=256)
    tags = ListField(StringField())


class SingleTask(Document):
    """A `SingleTask` associates a creation date with an `Action` instance.
    """
    action = EmbeddedDocumentField(Action)
    created_date = DateTimeField(default=datetime.datetime.now)


class TaskList(Document):
    """A `TaskList` associated a creation date and updated_date with a list of
    `Action` instances.
    """
    actions = ListField(EmbeddedDocumentField(Action))
    created_date = DateTimeField(default=datetime.datetime.now)
    updated_date = DateTimeField(default=datetime.datetime.now)
    num_completed = IntField(default=0)


###
### Actions
###

a1 = Action(value='Hello Mike', tags=['Erlang', 'Mike Williams'])
a2 = Action(value='Hello Joe', tags=['Erlang', 'Joe Armstrong'])

# print 'ACTION:\n'
# print '    ', a1.to_python()
# print '    ', a2.to_json()


###
### SingleTask
###

st = SingleTask()
st.action = a1

# print '\nSINGLETASK:\n'
# print '    ', st.to_python()
# print '    ', st.to_json()


###
### TaskList
###

tl = TaskList()
tl.actions = [a1, a2]

# print '\nTASKLIST:\n'
# print '    ', tl.to_python()
# print '    ', tl.to_json()


"""Attempting validation on:
    
    {"_types": ["User"], "secret": "whatevz", "name": "test hash", "_cls": "User"}

ShieldException caught: MD5 value is wrong length - secret:whatevz

Adjusted invalid data and trying again on:

    {"_types": ["User"], "secret": "34165b7d7c2d95bbecd41c05c19379c4", "name": "test hash", "_cls": "User"}

Validation passed

Attempting validation on:

    {'rogue_field': 'MWAHAHA', 'bio': 'J2D2 loves music', 'secret': 'e8b5d682452313a6142c10b045a9a135', 'name': 'J2D2'}

Validation passed
After validation:

    {'bio': 'J2D2 loves music', 'secret': 'e8b5d682452313a6142c10b045a9a135', 'name': 'J2D2'}

Validation passed

Document as Python:
    {'_types': ['User'], 'bio': u'J2D2 loves music', 'secret': 'e8b5d682452313a6142c10b045a9a135', 'name': u'J2D2', '_cls': 'User'}

Owner safe doc:
    {"bio": "J2D2 loves music", "secret": "e8b5d682452313a6142c10b045a9a135", "name": "J2D2"}

Public safe doc:
    {"bio": "J2D2 loves music", "name": "J2D2"}
"""


###
### Basic User model
###

class BasicUser(Document):
    _public_fields = ['name', 'bio']
    
    secret = MD5Field()
    name = StringField(required=True, max_length=50)
    bio = StringField(max_length=100)

    def set_password(self, plaintext):
        hash_string = hashlib.md5(plaintext).hexdigest()
        self.secret = hash_string


###
### Manually create an instance
###

### Create instance with bogus password
u = BasicUser()
u.secret = 'whatevz'
u.name = 'test hash'

### Validation will fail because u.secret does not contain an MD5 hash
#print 'Attempting validation on:\n\n    %s\n' % (u.to_json())
# try:
#     u.validate()
#     print 'Validation passed\n'
# except ShieldException, se:
#     print 'ShieldException caught: %s\n' % (se)
    

### Set the password *correctly* using our `set_password` function
u.set_password('whatevz')
#print 'Adjusted invalid data and trying again on:\n\n    %s\n' % (u.to_json())
# try:
#     u.validate()
#     print 'Validation passed\n'
# except ShieldException, se:
#     print 'ShieldException caught: %s (This section wont actually run)\n' % (se)


###
### Instantiate an instance with this data
###
 
total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_field': 'MWAHAHA',
}

### Checking for any failure. Exception thrown on first failure.
#print 'Attempting validation on:\n\n    %s\n' % (total_input)
# try:
#     BasicUser.validate_class_fields(total_input)
#     print 'Validation passed'
# except ShieldException, se:
#     print('ShieldException caught: %s' % (se))
# print 'After validation:\n\n    %s\n' % (total_input)


### Check all fields and collect all failures
exceptions = BasicUser.validate_class_fields(total_input, validate_all=True)

# if len(exceptions) == 0:
#     print 'Validation passed\n'
# else:
#     print '%s exceptions found\n\n    %s\n' % (len(exceptions),
#                                                [str(e) for e in exceptions])


###
### Field Security
###

# Add the rogue field back to `total_input`
total_input['rogue_field'] = 'MWAHAHA'

user_doc = BasicUser(**total_input)
#print 'Document as Python:\n    %s\n' % (user_doc.to_python())
safe_doc = BasicUser.make_json_ownersafe(user_doc)
#print 'Owner safe doc:\n    %s\n' % (safe_doc)
public_safe_doc = BasicUser.make_json_publicsafe(user_doc)
#print 'Public safe doc:\n    %s\n' % (public_safe_doc)

