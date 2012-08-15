import copy


'''
The code in this module has been copied from Django.  See docs/LICENSE.md for
the full license attached to this code.
'''


class MultiValueDictKeyError(KeyError):
    pass


class MultiValueDict(dict):
    """
    A subclass of dictionary customized to handle multiple values for the
    same key.

    The code from this class was borrowed from the Django code base.

    >>> attrs = {'name': ['Adrian', 'Simon'], 'position': ['Developer']}
    >>> d = MultiValueDict(attrs)
    >>> d['name']
    'Simon'
    >>> d.getlist('name')
    ['Adrian', 'Simon']
    >>> d.getlist('doesnotexist')
    []
    >>> d.getlist('doesnotexist', ['Adrian', 'Simon'])
    ['Adrian', 'Simon']
    >>> d.get('lastname', 'nonexistent')
    'nonexistent'
    >>> d.setlist('lastname', ['Holovaty', 'Willison'])

    This class exists to solve the irritating problem raised by cgi.parse_qs,
    which returns a list for every key, even though most Web forms submit
    single name-value pairs.
    """
    def __init__(self, key_to_list_mapping=()):
        super(MultiValueDict, self).__init__(key_to_list_mapping)

    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__,
                             super(MultiValueDict, self).__repr__())

    def __getitem__(self, key):
        """
        Returns the last data value for this key, or [] if it's an empty list;
        raises KeyError if not found.
        """
        try:
            list_ = super(MultiValueDict, self).__getitem__(key)
        except KeyError:
            error_msg = "Key %r not found in %r" % (key, self)
            raise MultiValueDictKeyError(error_msg)
        try:
            return list_[-1]
        except IndexError:
            return []

    def __setitem__(self, key, value):
        super(MultiValueDict, self).__setitem__(key, [value])

    def __copy__(self):
        return self.__class__([
            (k, v[:])
            for k, v in self.lists()
        ])

    def __deepcopy__(self, memo=None):
        if memo is None:
            memo = {}
        result = self.__class__()
        memo[id(self)] = result
        for key, value in dict.items(self):
            dict.__setitem__(result, copy.deepcopy(key, memo),
                             copy.deepcopy(value, memo))
        return result

    def __getstate__(self):
        obj_dict = self.__dict__.copy()
        obj_dict['_data'] = dict([(k, self.getlist(k)) for k in self])
        return obj_dict

    def __setstate__(self, obj_dict):
        data = obj_dict.pop('_data', {})
        for k, v in data.items():
            self.setlist(k, v)
        self.__dict__.update(obj_dict)

    def get(self, key, default=None):
        """
        Returns the last data value for the passed key. If key doesn't exist
        or value is an empty list, then default is returned.
        """
        try:
            val = self[key]
        except KeyError:
            return default
        if val == []:
            return default
        return val

    def getlist(self, key, default=None):
        """
        Returns the list of values for the passed key. If key doesn't exist,
        then a default value is returned.
        """
        try:
            return super(MultiValueDict, self).__getitem__(key)
        except KeyError:
            if default is not None:
                return default
            return []

    def setlist(self, key, list_):
        super(MultiValueDict, self).__setitem__(key, list_)

    def setdefault(self, key, default=None):
        if key not in self:
            self[key] = default
        return self[key]

    def setlistdefault(self, key, default_list=()):
        if key not in self:
            self.setlist(key, default_list)
        return self.getlist(key)

    def appendlist(self, key, value):
        """Appends an item to the internal list associated with key."""
        self.setlistdefault(key, [])
        super(MultiValueDict, self).__setitem__(key,
                                                self.getlist(key) + [value])

    def items(self):
        """
        Returns a list of (key, value) pairs, where value is the last item in
        the list associated with the key.
        """
        return [(key, self[key]) for key in self.keys()]

    def iteritems(self):
        """
        Yields (key, value) pairs, where value is the last item in the list
        associated with the key.
        """
        for key in self.keys():
            yield (key, self[key])

    def lists(self):
        """Returns a list of (key, list) pairs."""
        return super(MultiValueDict, self).items()

    def iterlists(self):
        """Yields (key, list) pairs."""
        return super(MultiValueDict, self).iteritems()

    def values(self):
        """Returns a list of the last value on every key list."""
        return [self[key] for key in self.keys()]

    def itervalues(self):
        """Yield the last value on every key list."""
        for key in self.iterkeys():
            yield self[key]

    def copy(self):
        """Returns a shallow copy of this object."""
        return copy.copy(self)

    def update(self, *args, **kwargs):
        """
        update() extends rather than replaces existing key lists.
        Also accepts keyword args.
        """
        if len(args) > 1:
            error_msg = "update expected at most 1 arguments, got %d" \
                        % len(args)
            raise TypeError(error_msg)
        if args:
            other_dict = args[0]
            if isinstance(other_dict, MultiValueDict):
                for key, value_list in other_dict.lists():
                    self.setlistdefault(key, []).extend(value_list)
            else:
                try:
                    for key, value in other_dict.items():
                        self.setlistdefault(key, []).append(value)
                except TypeError:
                    error_msg = "MultiValueDict.update() takes either a " \
                                "MultiValueDict or dictionary"
                    raise ValueError(error_msg)
        for key, value in kwargs.iteritems():
            self.setlistdefault(key, []).append(value)

    def dict(self):
        """
        Returns current object as a dict with singular values.
        """
        return dict((key, self[key]) for key in self)
