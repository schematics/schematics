#!/usr/bin/env python


"""Customer as Python:

    {'username': u'ben', '_types': ['User', 'User.Customer'], 'first_name': u'Ben', 'last_name': u'G', 'date_made': datetime.datetime(2011, 12, 11, 3, 4, 27, 107500), 'orders': [{'_types': ['Order'], 'line_items': [{'sku': 1, '_types': ['Product'], 'description': u'A Japanese laquered bowl', 'title': u'Japanese Bowl', 'price': 3.99, 'num_in_stock': 3, '_cls': 'Product'}, {'sku': 2, '_types': ['Product'], 'description': u'An African laquered bowl', 'title': u'African Bowl', 'price': 3.99, 'num_in_stock': 4, '_cls': 'Product'}], 'total': 7.98, 'date_made': datetime.datetime(2011, 12, 11, 3, 4, 27, 107004), '_cls': 'Order'}], '_cls': 'User.Customer', 'email': u'ben@ben.com'}

Customer as JSON:

    {"username": "ben", "_types": ["User", "User.Customer"], "first_name": "Ben", "last_name": "G", "date_made": "2011-12-11T03:04:27.107500", "orders": [{"_types": ["Order"], "line_items": [{"sku": 1, "_types": ["Product"], "description": "A Japanese laquered bowl", "title": "Japanese Bowl", "price": 3.99, "num_in_stock": 3, "_cls": "Product"}, {"sku": 2, "_types": ["Product"], "description": "An African laquered bowl", "title": "African Bowl", "price": 3.99, "num_in_stock": 4, "_cls": "Product"}], "total": 7.98, "date_made": "2011-12-11T03:04:27.107004", "_cls": "Order"}], "_cls": "User.Customer", "email": "ben@ben.com"}

Serializing model to JSON and loading into new instance...

Customer as Python:

    {'username': u'ben', '_types': ['User', 'User.Customer'], 'first_name': u'Ben', 'last_name': u'G', 'date_made': datetime.datetime(2011, 12, 11, 3, 4, 27, 107500), 'orders': [{'_types': ['Order'], 'line_items': [{'sku': 1, '_types': ['Product'], 'description': u'A Japanese laquered bowl', 'title': u'Japanese Bowl', 'price': 3.99, 'num_in_stock': 3, '_cls': 'Product'}, {'sku': 2, '_types': ['Product'], 'description': u'An African laquered bowl', 'title': u'African Bowl', 'price': 3.99, 'num_in_stock': 4, '_cls': 'Product'}], 'total': 7.98, 'date_made': datetime.datetime(2011, 12, 11, 3, 4, 27, 107004), '_cls': 'Order'}], '_cls': 'User.Customer', 'email': u'ben@ben.com'}

Customer as JSON:

    {"username": "ben", "_types": ["User", "User.Customer"], "first_name": "Ben", "last_name": "G", "date_made": "2011-12-11T03:04:27.107500", "orders": [{"_types": ["Order"], "line_items": [{"sku": 1, "_types": ["Product"], "description": "A Japanese laquered bowl", "title": "Japanese Bowl", "price": 3.99, "num_in_stock": 3, "_cls": "Product"}, {"sku": 2, "_types": ["Product"], "description": "An African laquered bowl", "title": "African Bowl", "price": 3.99, "num_in_stock": 4, "_cls": "Product"}], "total": 7.98, "date_made": "2011-12-11T03:04:27.107004", "_cls": "Order"}], "_cls": "User.Customer", "email": "ben@ben.com"}
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
print 'Customer as Python:\n\n    %s\n' % (customer.to_python())

### Serialize to JSON
print 'Customer as JSON:\n\n    %s\n' % (customer.to_json())

### Serialize data to JSON and load back into Python dictionary.
print 'Serializing model to JSON and loading into new instance...\n'
json_data = customer.to_json()
customer_dict = json.loads(json_data)

### Instantiate customer instance from pythonified JSON data
loaded_customer = Customer(**customer_dict)

### Reserialize to Python
print 'Customer as Python:\n\n    %s\n' % (loaded_customer.to_python())

### Reserialize to JSON
print 'Customer as JSON:\n\n    %s\n' % (loaded_customer.to_json())
