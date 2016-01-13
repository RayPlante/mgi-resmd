"""
a module providing the base utility functions and classes
"""
from collections import MutableMapping

class ScopedDict(MutableMapping):

    def __init__(self, defaults=None):
        MutableMapping.__init__(self)
        self._data = {}
        if defaults is None:
            defaults == {}
        self._defaults = defaults

    def __getitem__(self, key):
        try:
            return self._data.__getitem__(key)
        except KeyError:
            return self.__missing__(key)

    def __missing__(self, key):
        return self._defaults[key]

    def __setitem__(self, key, val):
        self._data[key] = val

    def __delitem__(self, key):
        del self._data[key]

    def __keys(self):
        return list(set(self._data.keys()).union(self._defaults))

    def __iter__(self):
        for key in self.__keys():
            yield key

    def __len__(self):
        return len(self.__keys())

    def default_to(self):
        """
        create and return a new dictionary that uses this one as its defaults
        """
        return self.__class__(self)

    @property
    def defaults(self):
        """
        the default dictionary
        """
        return self._defaults

class Transform(object):
    """
    a realization of a tranform that can be applied to input data
    """

    def __init__(self, config, engine, name=None, type=None):
        self.name = name
        if not type:
            type = config.get('type')
        self.type = type
        self.config = config
        self.engine = engine
        self._func = self.mkfn(config, engine)

    def __call__(self, input, context, *args):
        return self._func(input, context, *args)

    def mkfn(self, config, engine):
        def impl(input, context, *args):
            return input
        return impl

