#!/usr/bin/env python

"""PYTHON:
    {
      'username': u'ben',
      '_types': ['User', 'User.Customer'],
      'first_name': u'Ben',
      'last_name': u'G',
      'date_made': datetime.datetime(2011, 8, 7, 4, 21, 22, 783762),
      'orders': [<Order: Order object>],
      '_cls': 'User.Customer',
      'email': u'ben@ben.com'
    } 

JSON:
    {
      "username": "ben",
      "_types": ["User", "User.Customer"],
      "first_name": "Ben",
      "last_name": "G",
      "date_made": "2011-08-07T04:21:22.783762",
      "orders": [
        {
          "_types": ["Order"],
          "line_items": [
            {
              "sku": 1,
              "_types": ["Product"],
              "description": "A Japanese laquered bowl",
              "title": "Japanese Bowl",
              "price": 3.99,
              "num_in_stock": 3,
              "_cls": "Product"
            }, {
              "sku": 2,
              "_types": ["Product"],
              "description": "An African laquered bowl",
              "title": "African Bowl",
              "price": 3.99,
              "num_in_stock": 4,
              "_cls": "Product"
            }
          ],
          "total": 7.98,
          "date_made": "2011-08-07T04:21:22.783271",
          "_cls": "Order"
        }
      ],
      "_cls": "User.Customer",
      "email": "ben@ben.com"
    } 

Serializing to JSON and reloading...
    
PYTHON:
    {
      'username': u'ben',
      '_types': ['User', 'User.Customer'],
      'first_name': u'Ben',
      'last_name': u'G',
      'date_made': datetime.datetime(2011, 8, 7, 4, 21, 22, 783762),
      'orders': [<Order: Order object>],
      '_cls': 'User.Customer',
      'email': u'ben@ben.com'
    }
    
JSON:
    {
      "username": "ben",
      "_types": ["User", "User.Customer"],
      "first_name": "Ben",
      "last_name": "G",
      "date_made": "2011-08-07T04:21:22.783762",
      "orders": [
        {
          "_types": ["Order"],
          "line_items": [
            {
              "sku": 1,
              "_types": ["Product"],
              "description": "A Japanese laquered bowl",
              "title": "Japanese Bowl",
              "price": 3.99,
              "num_in_stock": 3,
              "_cls": "Product"
            }, {
              "sku": 2,
              "_types": ["Product"],
              "description": "An African laquered bowl",
              "title": "African Bowl",
              "price": 3.99,
              "num_in_stock": 4,
              "_cls": "Product"
            }
          ],
          "total": 7.98,
          "date_made": "2011-08-07T04:21:22.783271",
          "_cls":
          "Order"
        }
      ],
      "_cls": "User.Customer",
      "email": "ben@ben.com"
    } 
"""

from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import (IntField,
                               StringField,
                               FloatField,
                               DateTimeField,
                               EmailField)
from dictshield.fields.compound import (ListField,
                                        EmbeddedDocumentField)
import datetime
import json


###
### Store models
###

class Product(EmbeddedDocument):
    sku = IntField(min_value=1, max_value=9999, required=True)
    title = StringField(max_length = 30, required=True)
    description = StringField()
    price = FloatField(required=True)
    num_in_stock = IntField()

class Order(EmbeddedDocument):
    date_made = DateTimeField(required=True)
    date_changed = DateTimeField()
    line_items = ListField(EmbeddedDocumentField(Product))
    total = FloatField()


###
### User models
###

class User(Document):
    username = StringField(min_length=2, max_length=20, required=True)
    email = EmailField(max_length=30, required=True)

class Customer(User):
    date_made = DateTimeField(required=True)
    first_name = StringField(max_length=20, required=True)
    last_name = StringField(max_length=30, required=True)
    orders = ListField(EmbeddedDocumentField(Order))


###
### Product instances
###

product_a = Product(sku=1,
                    title="Japanese Bowl",
                    description="A Japanese laquered bowl",
                    price=3.99,
                    num_in_stock=3)

product_b = Product(sku=2,
                    title="African Bowl",
                    description="An African laquered bowl",
                    price=3.99,
                    num_in_stock=4)


###
### Order instance
###

order = Order(date_made=datetime.datetime.utcnow(),
              line_items=[product_a,product_b])
order.total=(product_a.price + product_b.price)


###
### Customer instance
###

customer = Customer(username="ben",
                    email="ben@ben.com",
                    first_name="Ben",
                    last_name="G",
                    date_made=datetime.datetime.utcnow(),                    
                    orders=[order])

###
### Serialization
###

### Serialize to Python
print 'PYTHON:\n', customer.to_python(), '\n'

### Serialize to JSON
print 'JSON:\n', customer.to_json(), '\n'

### Serialize data to JSON and load back into Python dictionary.
print 'Serializing to JSON and reloading...\n'
json_data = customer.to_json()
customer_dict = json.loads(json_data)

### Instantiate customer instance from pythonified JSON data
loaded_customer = Customer(**customer_dict)

### Reserialize to Python
print 'PYTHON:\n', loaded_customer.to_python(), '\n'

### Reserialize to JSON
print 'JSON:\n', loaded_customer.to_json(), '\n'
