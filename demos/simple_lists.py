#!/usr/bin/env python


"""Action 1 as Python:

    {'value': u'Hello Mike', 'tags': [u'Erlang', u'Mike Williams']}

Action 2 as JSON:

    {"value": "Hello Joe", "tags": ["Erlang", "Joe Armstrong"]}

Single task as Python:

    {'action': {'value': u'Hello Mike', 'tags': [u'Erlang', u'Mike Williams']}, 'created_date': datetime.datetime(2011, 12, 10, 22, 16, 22, 273267)}

Single task as JSON:

    {"action": {"value": "Hello Mike", "tags": ["Erlang", "Mike Williams"]}, "created_date": "2011-12-10T22:16:22.273267"}

Tasklist as Python:

    {'updated_date': datetime.datetime(2011, 12, 10, 22, 16, 22, 273521), 'num_completed': 0, 'actions': ['value': u'Hello Mike', 'tags': [u'Erlang', u'Mike Williams']}, {'value': u'Hello Joe', 'tags': [u'Erlang', u'Joe Armstrong']}], 'created_date': datetime.datetime(2011, 12, 10, 22, 16, 22, 273558)}

Tasklist as JSON:

    {"updated_date": "2011-12-10T22:16:22.273521", "num_completed": 0, "actions": [{"value": "Hello Mike", "tags": ["Erlang", "Mike Williams"]}, {"value": "Hello Joe", "tags": ["Erlang", "Joe Armstrong"]}], "created_date": "2011-12-10T22:16:22.273558"}
"""


import datetime

from schematics.models import Model
from schematics.serialize import to_json, to_python
from schematics.types import (StringType,
                              DateTimeType,
                              IntType)
from schematics.types.compound import (ModelType,
                                       ListType)


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

print 'Action 1 as Python:\n\n    %s\n' % (to_python(a1))
print 'Action 2 as JSON:\n\n    %s\n' % (to_json(a2))


###
### SingleTask
###

st = SingleTask()
st.action = a1

print 'Single task as Python:\n\n    %s\n' % (to_python(st))
print 'Single task as JSON:\n\n    %s\n' % (to_json(st))


###
### TaskList
###

tl = TaskList()
tl.actions = [a1, a2]

print 'Tasklist as Python:\n\n    %s\n' % (to_python(tl))
print 'Tasklist as JSON:\n\n    %s\n' % (to_json(tl))

