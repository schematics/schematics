#!/usr/bin/env python

import json
from dictshield.document import Document

__all__ = ['JsonschemableMixin', 'JsonschemableDocument']

class JsonschemableMixin:
    """A `JsonschemableMixin' adds a class method `.to_jsonschema' to generate
    a JSON schema from a Dictshield document.
    """
    
    @classmethod
    def to_jsonschema(cls):
        """Generate a JSON schema from a Dictshield document.
        """
        
        return 'I AM A JSON SCHEMA'

class JsonschemableDocument(Document, JsonschemableMixin):
    pass
