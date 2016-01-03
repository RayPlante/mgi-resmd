"""
a module that provides support for loading schemas, particularly those 
cached on local disk.  
"""
from __future__ import with_statement
import sys, os, json

from urlparse import urlparse
from urllib2 import urlopen
from collections import Mapping

from .location import read_loc_file

try:
    import requests
except ImportError:
    requests = None

class SchemaLoader(object):
    """
    A class that can be configured to load schemas from particular locations.
    For example, it can be used as a schema handler that loads schemas from
    local disk files rather than from remote locations.  It can also provide
    map schema URIs to arbitrary URL locations.  

    This class can be used (indirectly) as a JSON Schema URI handler to a 
    jsonschema.RefResolver instance; see SchemaHandler.
    """

    def __init__(self, urilocs={}):
        """
        initialize the handler

        :argument dict urilocs:  a dictionary mapping URIs to local file paths
                                 that define the schema identified by the URI.
        """
        self._map = dict(urilocs)

        # the following are used to support SchemaHandler; may be removed if 
        # SchemaHandler is not required for RefResolver
        self._schemes = set()
        self._addschemes(urilocs)

    def _addschemes(self, map):
        # used to support SchemaHandler
        for loc in self._map:
            self._schemes.add(urlparse(loc).scheme)

    def locate(self, uri):
        """
        return the file path location of the schema for the given URI or None
        if the schema is not known to be available locally.
        """
        return self._map.get(uri)

    def iterURIs(self):
        """
        return an iterator for the uris mapped in this instance
        """
        return self._map.iterkeys()

    def add_location(self, uri, path):
        """
        set the location of the schema file corresponding to the given URI
        """
        self._map[uri] = path
        self._schemes.add(urlparse(uri).scheme)

    def add_locations(self, urifiles):
        """
        add all the URI-file mappings in the given dictionary
        """
        self._map.update(urifiles)
        self._addschemes(urifiles)

    def load_schema(self, uri):
        """
        return the parsed json schema document for a given URI.

        :exc `KeyError` if the location of the schema has not been set
        :exc `IOError` if an error occurs while trying to read from the 
                       registered location.  This includes if the file is
                       not found or reading causes a syntax error.  
        """
        loc = self.locate(uri)
        url = urlparse(loc)

        # Note: this part adapted from jsonschema.RefResolver.resolve_remote()
        # (v2.5.1)
        if not url.scheme:
            with open(loc) as fd:
                return json.load(fd)
        elif (
            scheme in [u"http", u"https"] and
            requests and
            getattr(requests.Response, "json", None) is not None
        ):
            # Requests has support for detecting the correct encoding of
            # json over http
            if callable(requests.Response.json):
                result = requests.get(loc).json()
            else:
                result = requests.get(loc).json
        else: 
            # Otherwise, pass off to urllib and assume utf-8
            result = json.loads(urlopen(uri).read().decode("utf-8"))

        return result

    def load_locations(self, filename):
        """
        load in a mapping of URIs to file paths from a file.

        :argument str filename:  a file path to the mappings file.  The format 
                                 should be any of the formats supported by this 
                                 class.
        """
        self.add_locations(location.read_loc_file(file))

    def __call__(self, uri):
        """
        return the parsed json schema document for a given URI.  Calling an
        instance as a function is equivalent to calling load_schema().
        """
        return self.load_schema(uri)

class SchemaHandler(Mapping):
    """
    A wrapper class to use a SchemaLoader as a JSON Schema URI handler to a 
    jsonschema.RefResolver instance.  
    """

    def __init__(self, loader, strict=False):
        """
        initialize the handler

        :argument dict urilocs:  a dictionary mapping URIs to local file paths
                                 that define the schema identified by the URI.
        """
        self._loader = loader
        self._strict = strict
            
    def __getitem__(self, scheme):
        if self._strict and scheme not in self._loader._schemes:
            raise KeyError(scheme)
        return self._loader

    def __len__(self):
        return len(self._loader._schemes)

    def __iter__(self):
        return self._loader._schemes.__iter__()

