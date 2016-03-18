include "xml";

#["xmlns=\"\"", 
# "xsi:type=\"rsm:Resource\"", 
# "xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"", 
# "xmlns:rsm=\"urn:nist.gov/schema/res-md/1.0wd\"", 
# "xmlns:ms=\"urn:nist.gov/schema/mat-sci_res-md/1.0wd\"", 
# "status=\"active\"", "localid=\"urn:nist.gov/nmrr/ipr\""] |
#_pack(60)


#def tf(prefixes): 
#    prefixes|.["urn:goob"] = "go";
#
#def parent(prefixes):
#    [tf(prefixes), prefixes];
#
#{"urn:gurn": "gu"} as $p | parent($p)

#{ "ns": { "namespace": "urn:gurn", "prefix": "gu" }} | new_namespaces({})

#{"urn:gurn": "ns4"} | newprefix
#[] | map(select(test("^ns\\d+$"))) | map(.[2:]|tonumber) | max+1


#{ "name": "role", "value": "updated",
#  "ns": { "namespace": "urn:goob" }}  as $attr |
#
#{
#      "name": "date", "content": { "children": [ "2016" ] },
#      "ns": { "namespace": "urn:gurn" }
#} | 
#
#add_attr2element($attr) |
#
#format_element(0; {})

#{ "name": "date", "content": { "children": [{"name": "today"}, {"name": "tomorrow", "content": { "children": ["never knows"] }}, {"name": "never", "content": { "children": ["in a million years, when hell freezes over, and the land tumbles into the sea"] }}] }, "ns": { "namespace": "urn:gurn" }} |
#
#format_element(0; {"style": "pretty", "max_line_length": 75, "indent": 2, "value_pad": 1})


#{ "_ntype": "#COMM", "paras": [ "The quick brown fox jumped over the lazy dogs.  The quick brown fox jumped over the lazy dogs.  The quick brown fox jumped over the lazy dogs.  The quick brown fox jumped over the lazy dogs." ] } |
#format_comment(4; {"style": "pretty", "max_line_length": 70})

include "json2xml-schema"; 
import "xml" as xml;

{ "type": "string" } |
makesimpleelement("name"; "0"; "1"; "xs:string") |
xml::print


