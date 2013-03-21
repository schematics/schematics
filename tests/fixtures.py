import datetime
import hashlib
import json

from schematics.models import Model
from schematics.types import (BaseType,
                              UUIDType,
                              IntType,
                              BooleanType,
                              StringType,
                              FloatType,
                              DateTimeType,
                              EmailType,
                              MD5Type)
from schematics.serialize import (whitelist, blacklist, wholelist,
                                  make_safe_json)
from schematics.types.compound import ListType, ModelType


###
### Basic Class and Subclass
###

class SimpleModel(Model):
    """Simple model that has one StringType member
    """
    owner = UUIDType() # probably set required=True
    title = StringType(max_length=40)
    class Options:
        roles = {
            'owner': wholelist(),
        }
            


simple = SimpleModel(title='Misc Doc')


class SubModel(SimpleModel):
    """Subclass of `SimpleModel`. Adds `year` and limits publicly shareable
    types to only 'title' and 'year'.
    """
    year = IntType(min_value=1950, max_value=datetime.datetime.now().year)
    thoughts = StringType(max_length=255)
    class Options:
        roles = {
            'owner': wholelist(),
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


class OtherMixin(Model):
    wat = BooleanType(default=False)
    

class ThingModel(InterestMixin):
    title = StringType()
    body = StringType()

    class Options:
        roles = {
            'owner': wholelist(),
        }


thing_body = """Scenester twee mlkshk readymade butcher. Letterpress
portland +1 salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn
helvetica DIY. Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin
master cleanse.
"""

thing = ThingModel(title='Thing Model', body=thing_body, liked=True)


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
    author = ModelType(Author)
    comments = ListType(ModelType(Comment))
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
    action = ModelType(Action)
    created_date = DateTimeType(default=datetime.datetime.now)


class TaskList(Model):
    """A `TaskList` associated a creation date and updated_date with a list of
    `Action` instances.
    """
    actions = ListType(ModelType(Action))
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

class BasicUser(Model):
    
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
u.name = 'test hash'
u.set_password('whatevz')


###
### Instantiate an instance with this data
###

# user_dict
total_input = {
    'secret': 'e8b5d682452313a6142c10b045a9a135',
    'name': 'J2D2',
    'bio': 'J2D2 loves music',
    'rogue_field': 'MWAHAHA',
}


### Check all types and collect all failures
#exceptions = User.validate_class_types(total_input, validate_all=True)


###
### Type Security
###

# Add the rogue type back to `total_input`
total_input['rogue_field'] = 'MWAHAHA'

user_doc = BasicUser(**total_input)
#print 'Document as Python:\n    %s\n' % (user_doc.to_python())
safe_doc = make_safe_json(BasicUser, user_doc, 'owner')
#print 'Owner safe doc:\n    %s\n' % (safe_doc)
public_safe_doc = make_safe_json(BasicUser, user_doc, 'public')
#print 'Public safe doc:\n    %s\n' % (public_safe_doc)


### Alternate field names

class AltNames(Model):
    title = StringType(print_name='something_else')
