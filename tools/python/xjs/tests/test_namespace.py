from __future__ import with_statement
import json, os, pytest, shutil
from cStringIO import StringIO

input = { "goob": "gurn" }
context = { "foo": "bar", "$count": 4 }

import xjs.namespace as ns

class TestScopedDict(object):

    def test_def(self):
        ctx = ns.ScopedDict(context)
        assert ctx.defaults is context
        assert ctx['foo'] == 'bar'
        with pytest.raises(KeyError):
            ctx['hank']

        ctx['hank'] = 3
        ctx['foo'] = 'blah'
        assert ctx['hank'] == 3
        assert ctx['foo'] == 'blah'

        del ctx['hank'] 
        del ctx['foo'] 
        assert ctx['foo'] == 'bar'
        with pytest.raises(KeyError):
            ctx['hank']

        ctx['$count'] = 5

    def test_keys(self):
        ctx = ns.ScopedDict(context)
        assert ctx.defaults is context
        keys = ctx.keys()
        assert 'foo' in keys
        assert 'hank' not in keys
        assert len(keys) == 2

        ctx['hank'] = 3
        ctx['foo'] = 'blah'
        keys = ctx.keys()
        assert 'foo' in keys
        assert 'hank' in keys
        assert len(keys) == 3

    def test_iter(self):
        ctx = ns.ScopedDict(context)
        assert ctx.defaults is context
        # pytest.set_trace()
        assert 'foo' in set(ctx.iterkeys())
        assert 'foo' in ctx
        assert 'hank' not in ctx
        assert len(ctx) == 2

        ctx['hank'] = 3
        ctx['foo'] = 'blah'
        assert 'foo' in ctx
        assert 'hank' in ctx
        assert len(ctx) == 3

    def test_nodefs(self):
        ctx = ns.ScopedDict()
        assert ctx._defaults is not None
        assert 'foo' not in ctx.keys()
        assert 'foo' not in ctx
        assert len(ctx) == 0
        assert ctx.get('foo') is None

        ctx['foo'] = 'blah'
        assert ctx.get('foo') == 'blah'
        assert 'foo' in ctx
        assert len(ctx) == 1


class TestScopedPropertyMap(object):

    def test_root_tracker(self):
        tkr = ns.ScopedPropertyMap()
        rt = tkr.getTrackerFor("/")
        assert rt is tkr

        rt = tkr.getTrackerFor("")
        assert rt is tkr

        rt = tkr.getTrackerFor("/root/goober/gurn")
        assert rt is tkr

    def test_tracker(self):
        tkr = ns.ScopedPropertyMap()
        tkr._map['bs'] = 'fake'
        goober = tkr.ensureTrackerFor("/root/goober")
        goober._map['bs'] = 'real'

        rt = tkr.getTrackerFor("/")
        assert rt._map['bs'] == 'fake'
        assert rt is tkr

        rt = tkr.getTrackerFor("/root")
        assert rt._map['bs'] == 'fake'
        assert rt is not tkr
        root = rt

        rt = tkr.getTrackerFor("/root/hamper")
        assert rt._map['bs'] == 'fake'
        assert rt is not tkr

        rt = tkr.getTrackerFor("/root/hamper/gurn")
        assert rt._map['bs'] == 'fake'
        assert rt is not tkr

        rt = tkr.getTrackerFor("/root/goober")
        assert rt._map['bs'] == 'real'
        assert rt is goober

        rt = tkr.getTrackerFor("/root/goober/gurn")
        assert rt._map['bs'] == 'real'
        assert rt is goober

        gurn = tkr.ensureTrackerFor("/root/goober/gurn")
        assert gurn is not goober
        gurn._map['fred'] = 'friendly'
        assert gurn._map['fred'] == 'friendly'
        assert gurn._map['bs'] == 'real'

        rt = tkr.ensureTrackerFor("/root")
        rt._map['bs'] = 'really'
        assert gurn._map['fred'] == 'friendly'
        assert gurn._map['bs'] == 'real'
        assert goober._map['bs'] == 'real'
        assert tkr.getTrackerFor('/root/hamper')._map['bs'] == 'really'
        assert tkr.getTrackerFor('/root')._map['bs'] == 'really'

    def test_mapping(self):
        tkr = ns.ScopedPropertyMap()

        tkr.setMappingFor('ns', 'namespace', '/')
        tkr.setMappingFor('ms', 'matsci', '/')
        tkr.setMappingFor('ns', 'not stopping', '/root/goober/gurn')

        assert tkr.getMapFor('/')['ns'] == 'namespace'
        assert tkr.getMapFor('/')['ms'] == 'matsci'
        assert tkr.getMapFor('/root')['ns'] == 'namespace'
        assert tkr.getMapFor('/root')['ms'] == 'matsci'
        assert tkr.getMapFor('/root')['ns'] == 'namespace'
        assert tkr.getMapFor('/root')['ms'] == 'matsci'
        assert tkr.getMapFor('/root/goober')['ns'] == 'namespace'
        assert tkr.getMapFor('/root/goober')['ms'] == 'matsci'
        assert tkr.getMapFor('/root/goober/gurn')['ns'] == 'not stopping'
        assert tkr.getMapFor('/root/goober/gurn')['ms'] == 'matsci'

        tkr.setMappingFor('ns', 'not sure', '/root/goober')
        assert tkr.getMapFor('/root')['ns'] == 'namespace'
        assert tkr.getMapFor('/root/goober')['ns'] == 'not sure'
        assert tkr.getMapFor('/root/goober')['ms'] == 'matsci'
        assert tkr.getMapFor('/root/goober/gurn')['ns'] == 'not stopping'

        tkr.setMappingFor('ns', 'never sadder', '/root/hamper')
        assert tkr.getMapFor('/root')['ns'] == 'namespace'
        assert tkr.getMapFor('/root/goober')['ns'] == 'not sure'
        assert tkr.getMapFor('/root/goober')['ms'] == 'matsci'
        assert tkr.getMapFor('/root/goober/gurn')['ns'] == 'not stopping'
        assert tkr.getMapFor('/root/hamper')['ns'] == 'never sadder'
        assert tkr.getMapFor('/root/hamper')['ms'] == 'matsci'

class TestNamespaceMap(object):

    def test_root_tracker(self):
        tkr = ns.NamespaceMap()
        rt = tkr.getTrackerFor("/")
        assert rt is tkr

        rt = tkr.getTrackerFor("")
        assert rt is tkr

        rt = tkr.getTrackerFor("/root/goober/gurn")
        assert rt is tkr

    def test_tracker(self):
        tkr = ns.NamespaceMap()
        tkr._map['bs'] = 'fake'
        goober = tkr.ensureTrackerFor("/root/goober")
        goober._map['bs'] = 'real'

        rt = tkr.getTrackerFor("/")
        assert rt._map['bs'] == 'fake'
        assert rt is tkr

        rt = tkr.getTrackerFor("/root")
        assert rt._map['bs'] == 'fake'
        assert rt is not tkr
        root = rt

        rt = tkr.getTrackerFor("/root/hamper")
        assert rt._map['bs'] == 'fake'
        assert rt is not tkr

        rt = tkr.getTrackerFor("/root/hamper/gurn")
        assert rt._map['bs'] == 'fake'
        assert rt is not tkr

        rt = tkr.getTrackerFor("/root/goober")
        assert rt._map['bs'] == 'real'
        assert rt is goober

        rt = tkr.getTrackerFor("/root/goober/gurn")
        assert rt._map['bs'] == 'real'
        assert rt is goober

        gurn = tkr.ensureTrackerFor("/root/goober/gurn")
        assert gurn is not goober
        gurn._map['fred'] = 'friendly'
        assert gurn._map['fred'] == 'friendly'
        assert gurn._map['bs'] == 'real'

        rt = tkr.ensureTrackerFor("/root")
        rt._map['bs'] = 'really'
        assert gurn._map['fred'] == 'friendly'
        assert gurn._map['bs'] == 'real'
        assert goober._map['bs'] == 'real'
        assert tkr.getTrackerFor('/root/hamper')._map['bs'] == 'really'
        assert tkr.getTrackerFor('/root')._map['bs'] == 'really'

    def test_mapping(self):
        tkr = ns.NamespaceMap()

        tkr.definePrefix('ns', 'namespace')
        tkr.definePrefix('ms', 'matsci')
        tkr.definePrefix('ns', 'not stopping', '/root/goober/gurn')

        assert tkr.getURI('ns') == 'namespace'
        assert tkr.getURI('ms') == 'matsci'
        assert tkr.getURI('ns', '/root') == 'namespace'
        assert tkr.getURI('ms', '/root') == 'matsci'
        assert tkr.getURI('ns', '/root') == 'namespace'
        assert tkr.getURI('ms', '/root') == 'matsci'
        assert tkr.getURI('ns', '/root/goober') == 'namespace'
        assert tkr.getURI('ms', '/root/goober') == 'matsci'
        assert tkr.getURI('ns', '/root/goober/gurn') == 'not stopping'
        assert tkr.getURI('ms', '/root/goober/gurn') == 'matsci'

        tkr.definePrefix('ns', 'not sure', '/root/goober')
        assert tkr.getURI('ns', '/root') == 'namespace'
        assert tkr.getURI('ns', '/root/goober') == 'not sure'
        assert tkr.getURI('ms', '/root/goober') == 'matsci'
        assert tkr.getURI('ns', '/root/goober/gurn') == 'not stopping'

        tkr.definePrefix('ns', 'never sadder', '/root/hamper')
        assert tkr.getURI('ns', '/root') == 'namespace'
        assert tkr.getURI('ns', '/root/goober') == 'not sure'
        assert tkr.getURI('ms', '/root/goober') == 'matsci'
        assert tkr.getURI('ns', '/root/goober/gurn') == 'not stopping'
        assert tkr.getURI('ns', '/root/hamper') == 'never sadder'
        assert tkr.getURI('ms', '/root/hamper') == 'matsci'

    def test_expandURI(self):
        tkr = ns.NamespaceMap()

        tkr.definePrefix('ns', 'http://namespace.org/jschema.json#/definitions/')
        tkr.definePrefix('ms', 'https://matsci.org#')
        tkr.definePrefix('ns', '/fs/gurn/', '/root/goober/gurn')
        tkr.definePrefix('ns', '/fs/goober/', '/root/goober')
        tkr.definePrefix('ns', '/fs/hamper/', '/root/hamper')

        assert tkr.expandURI("ms:Database") == 'https://matsci.org#Database'
        assert tkr.expandURI("ns:Node") == 'http://namespace.org/jschema.json#/definitions/Node'
        assert tkr.expandURI("ns:nut", '/root/goober') == '/fs/goober/nut'
        assert tkr.expandURI("ba:hoodoo", '/root') == "ba:hoodoo"
        assert tkr.expandURI("https://matsci.org", '/root') == "https://matsci.org"
        
