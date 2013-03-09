#!/usr/bin/env python


import uuid
from schematics.models import Model
from schematics.types import UUIDType, StringType
from schematics.serialize import to_python, make_safe_python, blacklist, whitelist


class Media(Model):
    id = UUIDType(print_name='_id')
    owner = UUIDType()
    title = StringType(max_length=40)
    class Options:
        roles = {
            'meow': blacklist('owner'),
            'woof': whitelist('id'),
        }


m = Media()
m.id = uuid.uuid4()
m.owner = uuid.uuid4()
m.title = 'word'

# {'owner': None, '_id': UUID('5e3634f5-d37a-4cc8-b16a-cb23b04a7553'), 'title': u'word'}
print to_python(m)

# {'_id': UUID('5e3634f5-d37a-4cc8-b16a-cb23b04a7553'), 'title': u'word'}
print make_safe_python(Media, m, 'meow')

# {'_id': UUID('5e3634f5-d37a-4cc8-b16a-cb23b04a7553')}
print make_safe_python(Media, m, 'woof')
