#!/usr/bin/env python

from dictshield.document import Document, EmbeddedDocument
from dictshield.fields import *
import datetime
import json

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

class User(Document):
    username = StringField(min_length=2, max_length=20, required=True)
    email = EmailField(max_length=30, required=True)

class Customer(User):
    date_made = DateTimeField(required=True)
    first_name = StringField(max_length=20, required=True)
    last_name = StringField(max_length=30, required=True)
    orders = ListField(EmbeddedDocumentField(Order))

product = Product(sku=1,
                  title="Japanese Bowl",
                  description="A Japanese laquered bowl",
                  price=3.99,
                  num_in_stock=3)

order = Order(date_made=datetime.datetime.utcnow(),
              line_items=[product,product],
              total=7.98)

customer = Customer(username="ben",
                    email="ben@ben.com",
                    first_name="Ben",
                    last_name="G",
                    date_made=datetime.datetime.utcnow(),                    
                    orders=[order])


print 'PYTHON:\n', customer.to_python(), '\n'
print 'JSON:\n', customer.to_json(), '\n'

print 'Serializing to JSON and reloading...\n'
json_data = customer.to_json()
customer_dict = json.loads(json_data)


loaded_customer = Customer(**customer_dict)
print 'PYTHON:\n', loaded_customer.to_python(), '\n'
print 'JSON:\n', loaded_customer.to_json(), '\n'
