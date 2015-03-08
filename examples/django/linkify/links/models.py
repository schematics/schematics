# -*- coding: utf-8 -*-

from django.db import models


class Tag(models.Model):
    title = models.CharField(max_length=50)

    def to_dict(self):
        return {'id': self.id, 'title': self.title}


class Link(models.Model):
    title = models.CharField(max_length=255)
    url = models.URLField()
    tags = models.ManyToManyField(Tag)

    def to_dict(self):
        return {'id': self.id, 'title': self.title,
                'url': self.url, 'tags': [tag.to_dict()
                                          for tag in self.tags.all()]}

    def attach_tags(self, tags):
        for tag in tags:
            self.tags.add(tag)

    def update(self, **kwargs):
        """Update the particular fields rather than all fields.

        This works from Django 1.7+.
        """
        for field, value in kwargs.items():
            setattr(self, field, value)
        self.save(update_fields=list(kwargs.keys()))
