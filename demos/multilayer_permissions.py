#!/usr/bin/env python

"""AUTHOR ]----------------------------------------
- as python:   {'username': u'j2d2', '_types': ['Author'], 'name': u'james', 'a_setting': True, 'is_active': True, '_cls': 'Author', 'email': u'jdennis@gmail.com'} 

- json owner:  {"username": "j2d2", "a_setting": true, "name": "james", "email": "jdennis@gmail.com"} 

- json public: {"username": "j2d2", "name": "james"} 

COMMENT 1 ]----------------------------------------
- as python:   {'username': u'bro', 'text': u'This post was awesome!', '_types': ['Comment'], 'email': u'bru@dudegang.com', '_cls': 'Comment'} 

- json owner:  {"username": "bro", "text": "This post was awesome!", "email": "bru@dudegang.com"} 

- json public: {"username": "bro", "text": "This post was awesome!"} 

COMMENT 2 ]----------------------------------------
- as python:   {'username': u'barbie', 'text': u'This post is ridiculous', '_types': ['Comment'], 'email': u'barbie@dudegang.com', '_cls': 'Comment'} 

- json owner:  {"username": "barbie", "text": "This post is ridiculous", "email": "barbie@dudegang.com"} 

- json public: {"username": "barbie", "text": "This post is ridiculous"} 

BLOG POST ]----------------------------------------
- as python:   {'_types': ['BlogPost'], 'post_date': datetime.datetime(2011, 12, 10, 22, 12, 2, 383543), 'author': {'username': u'j2d2', '_types': ['Author'], 'name': u'james', 'a_setting': True, 'is_active': True, '_cls': 'Author', 'email': u'jdennis@gmail.com'}, 'deleted': False, 'title': u'Hipster Hodgepodge', 'comments': [{'username': u'bro', 'text': u'This post was awesome!', '_types': ['Comment'], 'email': u'bru@dudegang.com', '_cls': 'Comment'}, {'username': u'barbie', 'text': u'This post is ridiculous', '_types': ['Comment'], 'email': u'barbie@dudegang.com', '_cls': 'Comment'}], 'content': u'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n', '_cls': 'BlogPost'} 

- owner:  {'post_date': datetime.datetime(2011, 12, 10, 22, 12, 2, 383543), 'author': {'username': 'j2d2', 'a_setting': True, 'name': 'james', 'email': 'jdennis@gmail.com'}, 'deleted': False, 'title': 'Hipster Hodgepodge', 'comments': [{'username': 'bro', 'text': 'This post was awesome!', 'email': 'bru@dudegang.com'}, {'username': 'barbie', 'text': 'This post is ridiculous', 'email': 'barbie@dudegang.com'}], 'content': 'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n'} 

- public: {'author': {'username': 'j2d2', 'name': 'james'}, 'comments': [{'username': 'bro', 'text': 'This post was awesome!'}, {'username': 'barbie', 'text': 'This post is ridiculous'}], 'content': 'Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n'} 

- owner:  {"post_date": "2011-12-10T22:12:02.383543", "author": {"username": "j2d2", "a_setting": true, "name": "james", "email": "jdennis@gmail.com"}, "deleted": false, "title": "Hipster Hodgepodge", "comments": [{"username": "bro", "text": "This post was awesome!", "email": "bru@dudegang.com"}, {"username": "barbie", "text": "This post is ridiculous", "email": "barbie@dudegang.com"}], "content": "Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n"} 

- public: {"author": {"username": "j2d2", "name": "james"}, "comments": [{"username": "bro", "text": "This post was awesome!"}, {"username": "barbie", "text": "This post is ridiculous"}], "content": "Retro single-origin coffee chambray stumptown, scenester VHS\nbicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free\ntrust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed\n"} 
"""

import datetime
from schematics.models import Model
from schematics.filters import (make_ownersafe, make_publicsafe,
                                make_json_ownersafe, make_json_publicsafe)
from schematics.types import (StringType,
                              EmailType,
                              BooleanType,
                              DateTimeType)
from schematics.types.compound import (ListType,
                                       ModelType)


class Author(Model):
    name = StringType()
    username = StringType()
    email = EmailType()
    a_setting = BooleanType()
    is_active = BooleanType()
    class Options:
        private_fields=['is_active']
        public_fields=['username', 'name']


class Comment(Model):
    text = StringType()
    username = StringType()
    email = EmailType()   
    class Options:
        public_fields=['username', 'text']


class BlogPost(Model):
    title = StringType()    
    content = StringType()
    author = ModelType(Author)
    post_date = DateTimeType(default=datetime.datetime.now)
    comments = ListType(ModelType(Comment))
    deleted = BooleanType()   
    class Options:
        private_fields=['personal_thoughts']
        public_fields=['author', 'content', 'comments']
    

author = Author(name='james', username='j2d2', email='jdennis@gmail.com',
                a_setting=True, is_active=True)

print 'AUTHOR ]%s' % ('-' * 40)
print '- as python:  ', author.to_python(), '\n'
print '- json owner: ', make_json_ownersafe(Author, author), '\n'
print '- json public:', make_json_publicsafe(Author, author), '\n'

comment1 = Comment(text='This post was awesome!', username='bro',
                   email='bru@dudegang.com')

print 'COMMENT 1 ]%s' % ('-' * 40)
print '- as python:  ', comment1.to_python(), '\n'
print '- json owner: ', make_json_ownersafe(Comment, comment1), '\n'
print '- json public:', make_json_publicsafe(Comment, comment1), '\n'

comment2 = Comment(text='This post is ridiculous', username='barbie',
                   email='barbie@dudegang.com')
print 'COMMENT 2 ]%s' % ('-' * 40)
print '- as python:  ', comment2.to_python(), '\n'
print '- json owner: ', make_json_ownersafe(Comment, comment2), '\n'
print '- json public:', make_json_publicsafe(Comment, comment2), '\n'

content = """Retro single-origin coffee chambray stumptown, scenester VHS
bicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free
trust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed
"""

blogpost = BlogPost(title='Hipster Hodgepodge', author=author, content=content,
                    comments=[comment1, comment2], deleted=False)
print 'BLOG POST ]%s' % ('-' * 40)
print '- as python:  ', blogpost.to_python(), '\n'
print '- owner: ', make_ownersafe(BlogPost, blogpost), '\n'
print '- public:', make_publicsafe(BlogPost, blogpost), '\n'

print '- owner: ', make_json_ownersafe(BlogPost, blogpost), '\n'
print '- public:', make_json_publicsafe(BlogPost, blogpost), '\n'
