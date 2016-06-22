# import pytest
from __future__ import with_statement
import json, os, pytest, shutil
from cStringIO import StringIO
import pytest

import xjs.instance as instance

exdir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
                            os.path.dirname(os.path.dirname(__file__))))), 
                     'examples','json')

exfile = os.path.join(exdir, "ipr.json")

class TestInstance(object):

    def test_properties(self):
        data = None
        with open(exfile) as fd:
            data = json.load(fd)

        inst = instance.Instance(data, exfile)

        assert inst.source_location == exfile
        assert inst.source_id == "urn:nist.gov/nmrr/ipr"
        assert inst.pointer == "/"

    def test_fromlocation(self):
        # note this is not testing a remote loading yet
        inst = instance.Instance.from_location(exfile)

        assert inst.source_location == exfile
        assert inst.source_id == "urn:nist.gov/nmrr/ipr"
        assert inst.pointer == "/"
        assert "id" in inst.data

    def test_find_data_by_name(self):
        inst = instance.Instance.from_location(exfile)

        found = inst.find_data_by_name("goober")
        assert len(found) == 0

        found = inst.find_data_by_name("subject")
        assert len(found) == 1
        assert len(found[0]) == 2
        assert found[0][0] == "/content/subject"
        assert isinstance(found[0][1], list)
        assert "metals" in found[0][1]
        assert len(found[0][1]) >= 5

        found = inst.find_data_by_name(instance.EXTSCHEMAS)
        assert len(found) == 2
        assert len(found[0]) == 2

        found = dict(found)
        path = "/"+instance.EXTSCHEMAS
        assert path in found
        assert isinstance(found[path], list)
        assert "ms:Database" in found[path]
        assert len(found[path]) == 1
        path = "/applicability/0/"+instance.EXTSCHEMAS
        assert isinstance(found[path], list)
        assert "ms:MaterialScience" in found[path]
        assert len(found[path]) == 1

    def test_find_obj_by_prop(self):
        inst = instance.Instance.from_location(exfile)

        found = inst.find_obj_by_prop("goober")
        assert len(found) == 0

        found = inst.find_obj_by_prop("subject")
        assert len(found) == 1
        assert len(found[0]) == 2
        assert found[0][0] == "/content"
        assert isinstance(found[0][1], dict)
        assert "subject" in found[0][1]
        assert len(found[0][1]['subject']) >= 5

        found = inst.find_obj_by_prop(instance.EXTSCHEMAS)
        assert len(found) == 2
        assert len(found[0]) == 2

        found = dict(found)
        path = "/"
        assert path in found
        assert isinstance(found[path], dict)
        assert instance.EXTSCHEMAS in found[path]
        assert len(found[path][instance.EXTSCHEMAS]) == 1
        assert "ms:Database" in found[path][instance.EXTSCHEMAS]
        path = "/applicability/0"
        assert isinstance(found[path], dict)
        assert instance.EXTSCHEMAS in found[path]
        assert "ms:MaterialScience" in found[path][instance.EXTSCHEMAS]
        assert len(found[path][instance.EXTSCHEMAS]) == 1

    def test_find_extend_objs(self):
        inst = instance.Instance.from_location(exfile)

        foundobjs = inst.find_extended_objs()
        found = {}
        for item in foundobjs:
            found[item[0]] = (item[1], item[2])

        path = "/"
        assert path in found
        assert isinstance(found[path][1], dict)
        assert instance.EXTSCHEMAS in found[path][1]
        assert len(found[path][1][instance.EXTSCHEMAS]) == 1
        assert "ms:Database" in found[path][1][instance.EXTSCHEMAS]
        assert "ms:Database" not in found[path][0]
        assert (inst.data[instance.NS]['ms'] + "Database") in found[path][0]
        path = "/applicability/0"
        assert isinstance(found[path][1], dict)
        assert instance.EXTSCHEMAS in found[path][1]
        assert "ms:MaterialScience" in found[path][1][instance.EXTSCHEMAS]
        assert "ms:MaterialScience" not in found[path][0]
        assert (inst.data[instance.NS]['ms'] + "MaterialScience") in found[path][0]
        assert len(found[path][1][instance.EXTSCHEMAS]) == 1

    def test_extract(self):
        inst = instance.Instance.from_location(exfile)

        data = inst.extract("/content/subject")
        assert isinstance(data, list)
        assert "metals" in data
        assert len(data) >= 5

        assert inst.extract("/curation/contact/name") == "Zachary Trautt"
        assert inst.extract("/applicability/0/materialType/0") == \
            "non-specific"

