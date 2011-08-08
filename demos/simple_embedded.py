#!/usr/bin/env python

"""We first see an `Action` model, which is just a way to associate some value
with a list of tags.

A `SingleTask` instance associates an `Action` instance with a creation date.

A `TaskList` associates a list of `Action` instances with a creation date but
also adds an updated date and a count of how many tasks are completed.  This
model is hypothetical, but it assumes the tasks are done synchronously so then
`num_completed` would be an offset from the start of the task list.

The output looks like below.  I have formatted it for clarity.

ACTION: # As Python, then JSON

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

import datetime

from dictshield.document import EmbeddedDocument, Document
from dictshield.fields import (StringField,
                               EmbeddedDocumentField,
                               ListField,
                               DateTimeField,
                               IntField)


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

print 'ACTION:\n'
print '    ', a1.to_python()
print '    ', a2.to_json()


###
### SimpleTask
###

st = SingleTask()
st.action = a1

print '\nSINGLETASK:\n'
print '    ', st.to_python()
print '    ', st.to_json()


###
### TaskList
###

tl = TaskList()
tl.actions = [a1, a2]

print '\nTASKLIST:\n'
print '    ', tl.to_python()
print '    ', tl.to_json()

