import datetime

from dictshield.base import ShieldException
from schematics.models import Model

from schematics.types import (BaseType,
                              IntType,
                              BooleanType,
                              StringType,
                              FloatType,
                              DateTimeType,
                              EmailType,
                              MD5Type)

from schematics.validation import whitelist

from schematics.types.compound import ListType, EmbeddedDocumentType
from schematics.types.mongo import ObjectIdType
import hashlib
import json


###
### Basic Class and Subclass
###

class SimpleModel(Model):
    """Simple model that has one StringType member
    """
    owner = ObjectIdType() # probably set required=True
    title = StringType(max_length=40)


simple = SimpleModel(title='Misc Doc')


class SubModel(SimpleModel):
    """Subclass of `SimpleModel`. Adds `year` and limits publicly shareable
    types to only 'title' and 'year'.
    """
    year = IntType(min_value=1950, max_value=datetime.datetime.now().year)
    thoughts = StringType(max_length=255)
    class Options:
        roles = {
            'public': whitelist('title','year'),
        }


sub = SubModel(title='Total Recall', year=1990,
               thoughts='I wish I had three hands...')


###
### Mixin Concept
###

class InterestMixin(Model):
    liked = BooleanType(default=False)
    archived = BooleanType(default=False)
    deleted = BooleanType(default=False)


class ThingModel(Model, InterestMixin):
    title = StringType()
    body = StringType()


thing_body = """Scenester twee mlkshk readymade butcher. Letterpress
portland +1 salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn
helvetica DIY. Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin
master cleanse.
"""

thing = ThingModel(title='Mixed Document', body=thing_body, liked=True)


###
### Embedded Docs, each with Permissions config
###

class Author(Model):
    name = StringType()
    username = StringType()
    email = EmailType()
    a_setting = BooleanType()
    is_active = BooleanType()
    class Options:
        roles = {
            'owner': blacklist('is_active'),
            'public': whitelist('username', 'name'),
        }


author = Author(name='james', username='j2d2', email='jdennis@gmail.com',
                a_setting=True, is_active=True)


class Comment(Model):
    text = StringType()
    username = StringType()
    email = EmailType()   
    class Options:
        roles = {
            'owner': wholelist(),
            'public': whitelist('username', 'text'),
        }


comment1 = Comment(text='This post was awesome!', username='bro',
                   email='bru@dudegang.com')

comment2 = Comment(text='This post is ridiculous', username='barbie',
                   email='barbie@dudegang.com')


class BlogPost(Model):
    title = StringType()    
    content = StringType()
    author = EmbeddedDocumentType(Author)
    comments = ListType(EmbeddedDocumentType(Comment))
    deleted = BooleanType()   
    class Options:
        roles = {
            'owner': blacklist('personal_thoughts'),
            'public': whitelist('author', 'content', 'comments'),
        }
    

content = """Retro single-origin coffee chambray stumptown, scenester VHS
bicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free
trust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed
"""

blogpost = BlogPost(title='Hipster Hodgepodge', author=author, content=content,
                    comments=[comment1, comment2], deleted=False)


###
### Models
###

class Action(Model):
    """An `Action` associates an action name with a list of tags.
    """
    value = StringType(required=True, max_length=256)
    tags = ListType(StringType())


class SingleTask(Model):
    """A `SingleTask` associates a creation date with an `Action` instance.
    """
    action = EmbeddedDocumentType(Action)
    created_date = DateTimeType(default=datetime.datetime.now)


class TaskList(Model):
    """A `TaskList` associated a creation date and updated_date with a list of
    `Action` instances.
    """
    actions = ListType(EmbeddedDocumentType(Action))
    created_date = DateTimeType(default=datetime.datetime.now)
    updated_date = DateTimeType(default=datetime.datetime.now)
    num_completed = IntType(default=0)


###
### Actions
###

a1 = Action(value='Hello Mike', tags=['Erlang', 'Mike Williams'])
a2 = Action(value='Hello Joe', tags=['Erlang', 'Joe Armstrong'])


###
### SingleTask
###

st = SingleTask()
st.action = a1


###
### TaskList
###

tl = TaskList()
tl.actions = [a1, a2]


###
### Basic User model
###

class BasicUser(Document):
    
    secret = MD5Type()
    name = StringType(required=True, max_length=50)
    bio = StringType(max_length=100)

    class Options:
        roles = {
            'public': whitelist('name', 'bio'),
        }
        
    def set_password(self, plaintext):
        hash_string = hashlib.md5(plaintext).hexdigest()
        self.secret = hash_string


### Create instance with bogus password
u = BasicUser()
u.secret = 'whatevz'
u.name = 'test hash'

### Set the password *correctly* using our `set_password` function
u.set_password('whatevz')

###
### Instantiate an instance with this data
###
 
total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_field': 'MWAHAHA',
}


### Check all types and collect all failures
exceptions = .validate_class_types(total_input, validate_all=True)


###
### Type Security
###

# Add the rogue type back to `total_input`
total_input['rogue_field'] = 'MWAHAHA'

user_doc = BasicUser(**total_input)
#print 'Document as Python:\n    %s\n' % (user_doc.to_python())
safe_doc = BasicUser.make_json_ownersafe(user_doc)
#print 'Owner safe doc:\n    %s\n' % (safe_doc)
public_safe_doc = BasicUser.make_json_publicsafe(user_doc)
#print 'Public safe doc:\n    %s\n' % (public_safe_doc)

