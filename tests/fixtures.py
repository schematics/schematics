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
from dictshield.fields.mongo import ObjectIdField
import hashlib
import json

###
### Basic Class and Subclass
###

class SimpleDoc(Document):
    """Simple document that has one StringField member
    """
    owner = ObjectIdField() # probably set required=True
    title = StringField(max_length=40)


simple_doc = SimpleDoc(title='Misc Doc')


class SubDoc(SimpleDoc):
    """Subclass of `SimpleDoc`. Adds `year` and limits publicly shareable
    fields to only 'title' and 'year'.
    """
    _public_fields = ['title','year']
    year = IntField(min_value=1950, max_value=datetime.datetime.now().year)
    thoughts = StringField(max_length=255)


sub_doc = SubDoc(title='Total Recall',
                 year=1990,
                 thoughts='I wish I had three hands...')

###
### Mixin Docs
###

class InterestMixin(EmbeddedDocument):
    liked = BooleanField(default=False)
    archived = BooleanField(default=False)
    deleted = BooleanField(default=False)
    class Meta:
        mixin = True


class MixedDoc(Document, InterestMixin):
    title = StringField()
    body = StringField()


mixed_doc = MixedDoc()
mixed_doc.title = 'Mixed Document'
mixed_doc.body = """Scenester twee mlkshk readymade butcher. Letterpress
portland +1 salvia, vinyl trust fund butcher gentrify farm-to-table brooklyn
helvetica DIY. Sartorial homo 3 wolf moon, banh mi blog retro mlkshk Austin
master cleanse.
"""
mixed_doc.liked = True


###
### Embedded Docs, each with Permissions config
###

class Author(EmbeddedDocument):
    _private_fields=['is_active']
    _public_fields=['username', 'name']
    name = StringField()
    username = StringField()
    email = EmailField()
    a_setting = BooleanField()
    is_active = BooleanField()


author = Author(name='james', username='j2d2', email='jdennis@gmail.com',
                a_setting=True, is_active=True)


class Comment(EmbeddedDocument):
    _public_fields=['username', 'text']
    text = StringField()
    username = StringField()
    email = EmailField()   


comment1 = Comment(text='This post was awesome!', username='bro',
                   email='bru@dudegang.com')

comment2 = Comment(text='This post is ridiculous', username='barbie',
                   email='barbie@dudegang.com')


class BlogPost(Document):
    _private_fields=['personal_thoughts']
    _public_fields=['author', 'content', 'comments']
    title = StringField()    
    content = StringField()
    author = EmbeddedDocumentField(Author)
    comments = ListField(EmbeddedDocumentField(Comment))
    deleted = BooleanField()   
    

content = """Retro single-origin coffee chambray stumptown, scenester VHS
bicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free
trust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed
"""
blogpost = BlogPost(title='Hipster Hodgepodge', author=author, content=content,
                    comments=[comment1, comment2], deleted=False)


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
    _public_fields = ['name', 'bio']
    
    secret = MD5Field()
    name = StringField(required=True, max_length=50)
    bio = StringField(max_length=100)

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


### Check all fields and collect all failures
exceptions = BasicUser.validate_class_fields(total_input, validate_all=True)


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

