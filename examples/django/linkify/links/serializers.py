# -*- coding: utf-8 -*-

from schematics.models import Model
from schematics.types import StringType, URLType, IntType
from schematics.types.compound import ListType, ModelType


class TagSerializer(Model):
    id = IntType(required=False)
    title = StringType()


class LinkSerializerMixin(Model):
    """ Base Mixin for CRUD operation"""
    title = StringType(max_length=255, min_length=5, required=True)
    url = URLType(required=True)


class LinkCreateSerializer(LinkSerializerMixin):
    """ Serializer used during POST"""
    tags = ListType(field=StringType, max_size=3, required=False)


class LinkUpdateSerializer(LinkSerializerMixin):
    """ Serializer used during PATCH"""


class LinkReadSerializer(LinkSerializerMixin):
    """ Serializer used during GET and after successful link creation"""
    id = IntType(required=False)
    tags = ListType(ModelType(TagSerializer))
