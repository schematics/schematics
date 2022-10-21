安装
=====
==========
pip install schemv
==========

描述
=======
schematics 不支持数据类型强校验,在原有包基础上修改加入数据类型强校验,
性能远超cerberus校验框架


例子
=======

This is a simple Model. 

.. code:: python

  >>> from schemv.models import Model
    >>> from schemv.types import StringType, URLType
    >>> class Person(Model):
    ...     name = StringType(required=True)
    ...     website = URLType()
    ...
    >>> person = Person({'name': u'Joe Strummer',
    ...                  'website': 'http://soundcloud.com/joestrummer'})
    >>> person.name
    u'Joe Strummer'

  Serializing the data to JSON.
  >>> from schemv.types import StringType, URLType
  >>> class Person(Model):
  ...     name = StringType(required=True)
  ...     website = URLType()
  ...
  >>> person = Person({'name': u'Joe Strummer',
  ...                  'website': 'http://soundcloud.com/joestrummer'})
  >>> person.name
  u'Joe Strummer'

Serializing the data to JSON.

.. code:: python

  >>> import json
  >>> json.dumps(person.to_primitive())
  {"name": "Joe Strummer", "website": "http://soundcloud.com/joestrummer"}

Let's try validating without a name value, since it's required.

.. code:: python

  >>> person = Person()
  >>> person.website = 'http://www.amontobin.com/'
  >>> person.validate()
  Traceback (most recent call last):
    File "<stdin>", line 1, in <module>
    File "schematics/models.py", line 231, in validate
      raise DataError(e.messages)
  schemv.exceptions.DataError: {'name': ['This field is required.']}

Add the field and validation passes.

.. code:: python

  >>> person = Person()
  >>> person.name = 'Amon Tobin'
  >>> person.website = 'http://www.amontobin.com/'
  >>> person.validate()
  >>>