"""
classes and functions for resolving namespace identifiers
"""
from collections import MutableMapping

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

    def _split(self, path):
        return path.lstrip("/").split("/")

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
            nextdeeper = self.__class__(deepest._map)
            deepest._childscope[node] = nextdeeper
            deepest = nextdeeper

        return deepest

    def getMapFor(self, path):
        """
        return a mapping for the scope specified by the given path
        """
        return self.getTrackerFor(path)._map

    def setRootMapping(self, key, val):
        """
        set a key-value pair correspondig to the base or root scope 
        """
        self._map[key] = val

    def setMappingFor(self, key, val, path):
        """
        set a key-value pair correspondig to a scope specified by the given path
        """
        tracker = self.ensureTrackerFor(path)
        tracker.setRootMapping(key, val)

class NamespaceMap(ScopedPropertyMap):
    """
    a class for tracking namespace prefix definitions.  This is an extension
    of ScopedPropertyMap that adds functions for setting/retrieving prefix
    definitions in the language of namespaces.

    When this class is used with JSON Schema-compliant JSON documents, a 
    prefix, p, should be given a definition such that when the prefix in the 
    abbreviation, p:node, is replaced with its URI, the resulting URI is a 
    compliant JSON Pointer to node in the referenced JSON document.
    """

    def definePrefix(self, prefix, uri, path="/"):
        """
        define a prefix-namespace URI mapping with a scope defined by the 
        given path.

        :argument str prefix   the prefix being defined
        :argument str uri      the namespace URI that the prefix represents.
        :argument str path     the scope corresponding to a path into the 
                                 associated document; the default is the root
                                 of the document.
        """
        self.setMappingFor(prefix, uri, path)

    def getURI(self, prefix, path="/"):
        """
        return the namespace URI corresponding to the given prefix at a 
        given scope
        :argument str prefix   the namespace prefix of interest
        :argument str path     the scope corresponding to a path into the 
                                 associated document; the default is the root
                                 of the document.
        """
        return self.getMapFor(path).get(prefix)

    def expandURI(self, uri, path="/"):
        """
        expand an abbreviated URI by replacing its prefix with its definition.
        If the there is no prefix or a definition for the prefix is not found,
        the original URI is returned unchange.  

        Note that it will attempt to replace an "http:" at the beginning of a
        given URI.  As long as there is no prefix "http" defined, the URI will
        be returned unchanged.

        :argument str uri      the abbreviated URI to expand
        :argument str path     the path into the document that defines the 
                               scope for prefix definitions.
        """
        if not uri:
            return uri

        parts = uri.split(':', 1)
        if len(parts) > 1:
            baseuri = self.getURI(parts[0], path)
            if baseuri:
                uri = baseuri + parts[1]

        return uri

    
