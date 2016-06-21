"""
classes and functions for resolving namespace identifiers
"""
class ScopedDict(MutableMapping):
    """
    a dictionary with hierarchical default values where the levels represent
    different scopes that can inherit values (as defaults) from parent scopes.
    """

    def __init__(self, defaults=None):
        MutableMapping.__init__(self)
        self._data = {}
        if defaults is None:
            defaults = {}
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

    @property
    def defaults(self):
        """
        the default dictionary
        """
        return self._defaults


class ScopedPropertyMap(object):
    """
    a property lookup class that can track hierarchical scopes of a data 
    structure (like XML or JSON).  

    This class was designed to track namespaces through a data hierarchy 
    like XML or JSON, but it can track any properties that have the same 
    inheritance properties.  That is, properties (such as namespace prefixes) 
    defined in an outer level (e.g. the top of the document) are inherited by
    the inner levels until overridden.  
    """

    def __init__(self, defmap=None):
        self._childscope = {}
        self._map = ScopedDict(defmap)

    def _get_tracker_for_path_stack(self, pathlist):
        if len(pathlist) == 0:
            return (self, pathlist)
        scp = self._childscope.get(pathlist[0])
        if scp:
            return scp._get_tracker_for_path_stack(pathlist[1:])
        else:
            return (self, pathlist)

    def _split(path):
        return path.split("/")

    def getTrackerFor(self, path):
        """
        return the current ScopeTracker for the given path
        """
        return self._get_tracker_for_path_stack(self._split(path))[0]

    def ensureTrackerFor(self, path):
        """
        return the current ScopeTracker for the given path, creating trackers
        for path nodes as necessary.
        """
        (deepest, rest) = self._get_tracker_for_path_stack(self._split(path))
        for node in rest:
            if not node: 
                continue
            nextdeeper = self.class(deepest._map)
            deepest._childscope[node] = nextdeeper
            deepest = nextdeeper

        return deepest

    def getMapFor(self, path):
        """
        return a mapping for the scope specified by the given path
        """
        return getTrackerFor(path)._map

    def setMappingFor(self, key, val, path):
        """
        set a key-value pair correspondig to a scope specified by the given path
        """
        tracker = self.ensureTrackerFor(path)
        tracker._map.set(key, val)

