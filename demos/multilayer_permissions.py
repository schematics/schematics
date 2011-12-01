#!/usr/bin/env python

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

import datetime
from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (StringField,
                               EmailField,
                               ListField,
                               BooleanField,
                               DateTimeField,
                               EmbeddedDocumentField)


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
    post_date = DateTimeField(default=datetime.datetime.now)
    comments = ListField(EmbeddedDocumentField(Comment))
    deleted = BooleanField()   
    

author = Author(name='james', username='j2d2', email='jdennis@gmail.com',
                a_setting=True, is_active=True)

#print 'AUTHOR ]%s' % ('-' * 40)
#print '- as python:  ', author.to_python(), '\n'
#print '- json owner: ', Author.make_json_ownersafe(author), '\n'
#print '- json public:', Author.make_json_publicsafe(author), '\n'

comment1 = Comment(text='This post was awesome!', username='bro',
                   email='bru@dudegang.com')

#print 'COMMENT 1 ]%s' % ('-' * 40)
#print '- as python:  ', comment1.to_python(), '\n'
#print '- json owner: ', Comment.make_json_ownersafe(comment1), '\n'
#print '- json public:', Comment.make_json_publicsafe(comment1), '\n'

comment2 = Comment(text='This post is ridiculous', username='barbie',
                   email='barbie@dudegang.com')
#print 'COMMENT 2 ]%s' % ('-' * 40)
#print '- as python:  ', comment2.to_python(), '\n'
#print '- json owner: ', Comment.make_json_ownersafe(comment2), '\n'
#print '- json public:', Comment.make_json_publicsafe(comment2), '\n'

content = """Retro single-origin coffee chambray stumptown, scenester VHS
bicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free
trust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed
"""

blogpost = BlogPost(title='Hipster Hodgepodge', author=author, content=content,
                    comments=[comment1, comment2], deleted=False)
print 'BLOG POST ]%s' % ('-' * 40)
print '- as python:  ', blogpost.to_python(), '\n'
print '- owner: ', BlogPost.make_ownersafe(blogpost), '\n'
print '- public:', BlogPost.make_publicsafe(blogpost), '\n'

print '- owner: ', BlogPost.make_json_ownersafe(blogpost), '\n'
print '- public:', BlogPost.make_json_publicsafe(blogpost), '\n'
