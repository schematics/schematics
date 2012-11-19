#!/usr/bin/env python

"""
"""

import datetime
from schematics.models import Model
from schematics.serialize import (to_python, to_json,
                                  make_safe_python, make_safe_json,
                                  wholelist, blacklist, whitelist)
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
        roles = {
            'owner': blacklist('is_active'),
            'public': whitelist('username', 'name'),
        }


class Comment(Model):
    text = StringType()
    username = StringType()
    email = EmailType()   
    class Options:
        roles = {
            'owner': wholelist(),
            'public': whitelist('username', 'text'),
        }


class BlogPost(Model):
    title = StringType()    
    content = StringType()
    author = ModelType(Author)
    post_date = DateTimeType(default=datetime.datetime.now)
    comments = ListType(ModelType(Comment))
    deleted = BooleanType()   
    class Options:
        roles = {
            'owner': blacklist('personal_thoughts'),
            'public': whitelist('author', 'content', 'comments'),
        }
    

author = Author(name='james', username='j2d2', email='jdennis@gmail.com',
                a_setting=True, is_active=True)

print 'AUTHOR ]%s' % ('-' * 40)
print '- as python:  ', to_python(author), '\n'
print '- json owner: ', make_safe_json(Author, author, 'owner'), '\n'
print '- json public:', make_safe_json(Author, author, 'public'), '\n'

comment1 = Comment(text='This post was awesome!', username='bro',
                   email='bru@dudegang.com')

print 'COMMENT 1 ]%s' % ('-' * 40)
print '- as python:  ', to_python(comment1), '\n'
print '- json owner: ', make_safe_json(Comment, comment1, 'owner'), '\n'
print '- json public:', make_safe_json(Comment, comment1, 'public'), '\n'

comment2 = Comment(text='This post is ridiculous', username='barbie',
                   email='barbie@dudegang.com')
print 'COMMENT 2 ]%s' % ('-' * 40)
print '- as python:  ', to_python(comment2), '\n'
print '- json owner: ', make_safe_json(Comment, comment2, 'owner'), '\n'
print '- json public:', make_safe_json(Comment, comment2, 'public'), '\n'

content = """Retro single-origin coffee chambray stumptown, scenester VHS
bicycle rights 8-bit keytar aesthetic cosby sweater photo booth. Gluten-free
trust fund keffiyeh dreamcatcher skateboard, williamsburg yr salvia tattooed
"""

blogpost = BlogPost(title='Hipster Hodgepodge', author=author, content=content,
                    comments=[comment1, comment2], deleted=False)
print 'BLOG POST ]%s' % ('-' * 40)
print '- as python:  ', to_python(blogpost), '\n'
print '- owner: ', make_safe_json(BlogPost, blogpost, 'owner'), '\n'
print '- public:', make_safe_json(BlogPost, blogpost, 'public'), '\n'

print '- owner: ', make_safe_json(BlogPost, blogpost, 'owner'), '\n'
print '- public:', make_safe_json(BlogPost, blogpost, 'public'), '\n'
