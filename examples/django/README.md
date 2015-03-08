#### Linkify

`Linkify` is small app similar to `reddit/hackernews` without comments and votes features.
App demonstrates how to use `Schematics` with `Django` to create APIs.

#### Installation

- Create a new virtualenv for `python3`.
- Then `pip install -r requirements`.
- `./manage.py runserver`.
- To run tests, `./test`

#### Endpoints

- `/links` -> List all links (`GET`).
- `/links/` -> Create a link (`POST`).
- `/links/<id>/` -> Read details of a link (`GET`).
- `/links/<id>/` -> Update a link (`PATCH`).
- `/links/<id>/` -> Delete a link (`DELETE`).

#### Examples

```python
# Create a new link
In [96]: data = {'title': 'Brubeck', 'url': 'https://github.com/j2labs/brubeck', 'tags':['Web Framework', 'Python']}

In [97]: r = requests.post('http://127.0.0.1:8000/links/', json=data)

In [98]: r.status_code
Out[98]: 201

In [99]: r.json()
Out[99]:
{'id': 1,
 'tags': [{'id': 1, 'title': 'Web Framework'}, {'id': 2, 'title': 'Python'}],
 'title': 'Brubeck',
 'url': 'https://github.com/j2labs/brubeck'}

# Read a link

In [105]: requests.get("http://localhost:8000/links/1/").json()
Out[105]:
{'id': 1,
 'tags': [{'id': 1, 'title': 'Web Framework'}, {'id': 2, 'title': 'Python'}],
 'title': 'Brubeck',
 'url': 'https://github.com/j2labs/brubeck'}

# List all links
In [106]: requests.get("http://localhost:8000/links/").json()
Out[106]:
{'items': [{'id': 1,
   'tags': [{'id': 1, 'title': 'Web Framework'}, {'id': 2, 'title': 'Python'}],
   'title': 'Brubeck',
   'url': 'https://github.com/j2labs/brubeck'}],
   'total': 1}

# Update a link
In [107]: update_data = {'title': 'Django', 'url': 'https://github.com/django/django'}

In [110]: r = requests.patch("http://localhost:8000/links/1/", json=update_data)

In [111]: r.status_code
Out[111]: 202

In [112]: r.json()
Out[112]:
{'id': 1,
 'tags': [{'id': 1, 'title': 'Web Framework'}, {'id': 2, 'title': 'Python'}],
 'title': 'Django',
 'url': 'https://github.com/django/django'}

# Delete a link
In [113]: r = requests.delete("http://localhost:8000/links/1/")

In [114]: r.status_code
Out[114]: 204
```
