import "xml" as xml;

def description2doc:
    .description | xml::text_element("xs:documentation");
def notes2doc:
    (.notes//[]) | map(xml::text_element("xs:documentation"));
def comments2doc:
    .comments | xml::comment;

# convert JSON schema documentation items (description and notes)
# to XML Schema annotations
#
# @in   a JSON schema definition that contains description and notes items
#
def documentation:
    xml::element_content( [description2doc] + notes2doc ) |
    xml::element("xs:annotation")
;

# convert a JSON schema property definition to an element definition
#
# @in JSON schema definition
# @arg propname string:  the property name; this will be used as the
#                        element name
# @arg minoccurs string: the minimum-occurance number as a string (usually
#                        0 or 1); if not given the attribute will not be
#                        specified (which means 1).
# @arg maxoccurs string: the maximum-occurance number as a string (usually
#                        1 or unbounded); if not given the attribute will not be
#                        specified (which means 1).
# @arg type string:      the XSD type to specify; default: "xs:token"
# @out object:  an "xs:element" element node
#
def makesimpleelement(propname; minoccurs; maxoccurs; type):
    xml::element_content(
        [ description2doc ];
        [ type | xml::attribute("type") ] +
        [ minoccurs | xml::attribute("minoccurs") ] +
        [ maxoccurs | xml::attribute("maxoccurs") ]
    ) |
    xml::element(propname)
;

def makesimpleelement(propname; minoccurs; maxoccurs):
    makesimpleelement(propname; minoccurs; maxoccurs; "xs:token");
def makesimpleelement(propname; minoccurs):
    makesimpleelement(propname; minoccurs; empty; "xs:token");
def makesimpleelement(propname):
    makesimpleelement(propname; empty; empty; "xs:token");

