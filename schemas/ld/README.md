# Linked-Data Schemas

This directory contains schemas and related definitions that enable
support for resource metadata using JSON-LD.

## Motivation

Another emerging technique for encoding and transmitting metadata is using
JSON-LD.  This format allows one to connect a piece of metadata (its
label and value) to an existing term in an existing, defined "vocabulary".  A
defined vocabulary is normally either an ontology defined with OWL or
RDFS, or a taxonomy defined with SKOS.  This, in effect, discourages
metadata providers from (re-)creating a new vocabulary when existing
terms exist and work well enough.

Being RDF-based, ontologies are typically less about defining strict
syntactic rules for describing something, say, in terms of required
and optional attributes; rather, if one knows something about a
resource, one can typically make an appropriate statement using the 
necssary property from the ontology, independent of any other
properties.  Nevertheless, some applications--like repositories--need
to support the concept of a complete, validate-able, and standardized
record describing a resource.  This has led to a type of schema I
call a _profile schema_ for metadata stored in a JSON-LD
document; examples include the DCAT schema, the US POD schema, and the
HCLS Data Description Profile.  

A profile schema is one in which the classes and properties of the
schema are pulled from (typically, several) existing ontologies and
vocabularies (defined elsewhere).  Thus, all the semantics associated
with the borrowed terms are pulled into the schema as well.  The
schema will typically add constraints that control whether properties
are required, optional, or can have multiple values
(i.e. cardinality).  The advantage of JSON-LD and the profile schema
is in providing a stricter syntax for describing a resource completely
while remaining compatible with the Linked Data and Semmantic Web
worlds.  

Profile schema definitions typically are in the form of a
human-readable document (though it is usually accompanied by a JSON-LD
context definition file).  As is the case for the examples above, the
schemas are typically quite straight-forward and not complicated;
thus, the prose specification documents are easy to create.  A
disadvantage of having a non-machine-readable specification is that it
is not possible to create a schema-independent validater.

This directory presents a means for defining a profile schema in a
machine-readable way.  Not only does this allow for the creation of
a general validator, but also allows for different views of the schema
(e.g. for documentation purposes).  Most importantly for the purpose
of this repo, it provides a means to automatically manage
transformations of metadata instances between formats based on
different schema systems--namely, JSON-LD, JSON Schema, and XML
Schema.

## A Machine-readable Profile Schema Definition Framework

Schemas in this directory present a particular technique for defining
a profile schema in a machine-readable way.  The approach is based on
the following assumptions:

* A JSON-LD instance document is an RDF description based on an
  ontology.
* The description is primarily about one RDF resource in particular.
* The ontology, based on classes and properties taken from other
  ontologies, can be expressed correctly and effectively in JSON-LD.

### profile-schema-onto.json:  a Supporting Ontology

This file has two purposes:

* to define a JSON-LD context that can be used in schema definitions
* to define some super-classes and super-properties useful for
  defining the ontology specifically as a profile schema.  Their
  semantics specify how the end classes and properties should be
  encoded in a JSON-LD instance.




