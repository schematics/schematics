# -*- coding: utf-8 -*-

import json
from django.test import TestCase, Client


class TestCreateLink(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

    def test_create_with_bad_data(self):
        data = {'name': 'Django', 'url': 'https://github.com/django/django',
                'tags': ['Web Framework', 'Python']}
        resp = self.client.post('/links/', content_type='application/json',
                                data=json.dumps(data))

        assert resp.status_code == 400

    def test_create(self):
        data = {'title': 'Django', 'url': 'https://github.com/django/django',
                'tags': ['Web Framework', 'Python']}
        resp = self.client.post('/links/', content_type='application/json',
                                data=json.dumps(data))
        obj = json.loads(resp.content.decode())

        assert resp.status_code == 201
        assert obj['id']

        assert len(obj['tags']) == 2
        assert obj['title'] == data['title']
        assert obj['url'] == data['url']


class TestUpdateLink(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        data = {'title': 'Django', 'url': 'https://github.com/django/django',
                'tags': ['Web Framework', 'Python']}
        resp = self.client.post('/links/', content_type='application/json',
                                data=json.dumps(data))
        self.link = json.loads(resp.content.decode())

    def test_update(self):
        data = {'title': 'Flask', 'url': 'https://github.com/mitsuhiko/flask'}
        pk = self.link['id']

        resp = self.client.patch('/links/{}/'.format(pk),
                                 content_type='application/json',
                                 data=json.dumps(data))

        obj = json.loads(resp.content.decode())

        assert resp.status_code == 202
        assert obj['title'] == data['title']
        assert obj['url'] == data['url']

    def test_update_with_bad_params(self):
        data = {'name': 'Flask'}

        pk = self.link['id']

        resp = self.client.patch('/links/{}/'.format(pk),
                                 content_type='application/json',
                                 data=json.dumps(data))

        assert resp.status_code == 400


class TestListLink(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        data = {'title': 'Django', 'url': 'https://github.com/django/django',
                'tags': ['Web Framework', 'Python']}
        resp = self.client.post('/links/', content_type='application/json',
                                data=json.dumps(data))
        self.link = json.loads(resp.content.decode())

    def test_list(self):
        resp = self.client.get('/links/')
        obj = json.loads(resp.content.decode())

        assert resp.status_code == 200
        assert int(obj['total']) == 1
        for item in obj['items']:
            assert item['id']
            assert item['title']
            assert item['url']

            for tag in item['tags']:
                assert tag['id']
                assert tag['title']


class TestReadLink(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        self.data = {'title': 'Django',
                     'url': 'https://github.com/django/django',
                     'tags': ['Web Framework', 'Python']}
        resp = self.client.post('/links/', content_type='application/json',
                                data=json.dumps(self.data))
        self.link = json.loads(resp.content.decode())

    def test_read(self):
        resp = self.client.get('/links/{}/'.format(self.link['id']))
        obj = json.loads(resp.content.decode())

        assert obj['id'] == 1
        assert obj['title'] == self.data['title']
        assert obj['url'] == self.data['url']

        for tag in obj['tags']:
                assert tag['id']
                assert tag['title'] in self.data['tags']

    def test_missing(self):
        resp = self.client.get('/links/23/')

        assert resp.status_code == 404


class TestDeleteLink(TestCase):
    def setUp(self):
        super().setUp()
        self.client = Client()

        self.data = {'title': 'Django',
                     'url': 'https://github.com/django/django',
                     'tags': ['Web Framework', 'Python']}
        resp = self.client.post('/links/', content_type='application/json',
                                data=json.dumps(self.data))
        self.link = json.loads(resp.content.decode())

    def test_delete(self):
        resp = self.client.delete('/links/{}/'.format(self.link['id']))

        assert resp.status_code == 204

        resp = self.client.get('/links/{}/'.format(self.link['id']))
        assert resp.status_code == 404
