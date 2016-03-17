"""
transforms for creating XML from JSON data
"""
import os, copy, re, textwrap, collections
import json as jsp

from ..exceptions import *
from ..base import Transform, ScopedDict, Context
from .std import JSON, Extract, StringTemplate, Function
from . import std

MODULE_NAME = __name__
TRANSFORMS_PKG = __name__.rsplit('.', 1)[0]

def _generate_name(spec, engine, tname=None, ttype=None):
    return _generate_value(spec, engine, tname, ttype, True)

def _generate_value(spec, engine, tname=None, ttype=None, forname=False):
    if spec is None:
        return None

    if not forname and (isinstance(spec, int) or isinstance(spec, float) or \
                        isinstance(spec, bool)):
        return spec

    if isinstance(spec, dict):
        if spec.has_key('$val'):
            spec = spec['$val']

        if isinstance(spec, dict):
            return engine.make_transform(spec)

        if isinstance(spec, str) or isinstance(spec, unicode):
            if not Function.matches(spec) and \
               (spec == '' or ':' in spec or spec.startswith('/')):
                return Extract({'select': spec}, engine, tname, ttype)

            return engine.resolve_transform(spec)
        else:
            raise TransformConfigTypeError("spec", "string or object",
                                           type(spec), self.spec)

    if isinstance(spec, str) or isinstance(spec, unicode):
        if '{' in spec and '}' in spec:
            # it's a string template
            return StringTemplate({'content': spec}, engine, 
                                  "attr spec", "xml.attribute")
                                  
    else:
        raise TransformConfigTypeError("spec", "string or object",
                                       type(spec), self.spec)

    return spec

def _generate_object(spec, engine, tname=None, ttype=None):
    if spec is None:
        return None

    if isinstance(spec, dict):
        # it's an object, either a transform or JSON template
        if not spec.has_key('$val'):
            # it's a JSON template
            return JSON({'content': spec}, engine, tname, ttype)
        else:
            spec = spec["$val"]

    if isinstance(spec, dict):
        # it's an anonymous transform
        return engine.make_transform(spec)

    if isinstance(spec, str) or isinstance(spec, unicode):
        if not Function.matches(spec) and \
           (spec == '' or ':' in spec or spec.startswith('/')):
            # it's a data pointer to select data
            return Extract({'select': spec}, engine, tname, ttype)

        # it's a named transform or transform function
        return engine.resolve_transform(spec)

    return spec



class ToAttribute(Transform):
    """
    a transform type for creating XML Attribute data.  This transform type
    takes the following paramters:

    :argument name:  the local name for the attribute.  If provided as a 
                     string (with { and } characters), it will be treated
                     as a StringTemplate.  If provided as an object with a 
                     $val property, the name will be generated by the transform
                     implied by the $val property value.  Any other kind of 
                     object will be treated as an anonymous transform that 
                     should produce a string value to provide the value of the 
                     name.  
    :argument value:
    :argument namespace:
    :argument prefix:
    """

    def mkfn(self, config, engine):
        tname = self.name or '(xml)'
        ttype = "xml.attribute"

        try:
            name = _generate_name(config['name'], engine, tname+" Attr name", 
                                  ttype)
        except KeyError, ex:
            raise MissingTransformData("name", self.name)
        try:
            value = _generate_value(config['value'], engine, 
                                    tname+" Attr val",ttype)
        except KeyError, ex:
            raise MissingTransformData("value", self.name)

        ns = _generate_name(config.get('namespace'), engine, 
                            tname+" Attr ns", ttype)
        pref = _generate_name(config.get('prefix'), engine, 
                              tname+" Attr prefix", ttype)

        def impl(input, context, *args):
            out = {}
            out['name'] = name
            if isinstance(name, Transform):
                out['name'] = name(input, context)
            out['value'] = value
            if isinstance(value, Transform):
                out['value'] = value(input, context)

            if ns:
                out['namespace'] = ns
                if isinstance(ns, Transform):
                    out['namespace'] = ns(input, context)
            if pref:
                out['prefix'] = pref
                if isinstance(pref, Transform):
                    out['prefix'] = pref(input, context)

            return out

        return impl
        

class ToElementContent(Transform):

    def mkfn(self, config, engine):
        ttype = "xml.elementContent"
        name = self.name or "(anon)"

        attrs = None
        if config.has_key("attrs"):
            # attrs can be 
            #  1) a list where each element forms an attribute
            #  2) a dict representing a transform ({$val}, {$type}) that 
            #       generates a list of attributes
            #  3) a string providing a named transform or datapointer that 
            #       generates a list of attributes
            if isinstance(config['attrs'], list):
                attrs = []
                for attr in config['attrs']:
                    attr = self._generate_attribute(attr, engine, 
                                                    "{0} attr".format(name),
                                                    ttype)
                    attrs.append(attr)

            else:
                # some reference to a transform that should result in an array.
                # the value is interpreted just like a metaproperty directive
                attrs = std.resolve_meta_property(config['attrs'], engine,
                                                  name+':(attrs)')
        
        children = None
        if config.has_key("children"):
            if isinstance(config['children'], list) or \
               isinstance(config['children'], tuple):
                children = []
                for child in config['children']:
                    if isinstance(child, list) or isinstance(child, tuple):
                        raise TransformConfigTypeError("children item", 
                                                       "str or dict",type(child),
                                                       name)

                    elif isinstance(child, collections.Mapping):
                        child = self._generate_element(child, engine, 
                                                       "{0} child".format(name),
                                                       ttype)

                    children.append(child)

            else:
                # some reference to a transform that should result in an array.
                # the value is interpreted just like a metaproperty directive
                children = std.resolve_meta_property(config['children'], engine,
                                                     name+':(children)')

        
        def impl(input, context, *args):
            out = {}
            if attrs is not None:
                if isinstance(attrs, Transform):
                    out['attrs'] = attrs(input, context)
                else:
                    ol = []
                    for attr in attrs:
                        if isinstance(attr, Transform):
                            attr = attr(input, context)
                        elif isinstance(attr, collections.Mapping):
                            if '$ins' in attr:
                                attr = attr['$ins'](input, context)
                                if hasattr(attr, '__iter__'):
                                    ol.extend(attr)
                                    continue
                            elif '$upd' in attr:
                                # shouldn't happen
                                attr = attr['$upd'](input, context)
                        ol.append(attr)

                    out['attrs'] = ol

            if children is not None:
                if isinstance(children, Transform):
                    out['children'] = children(input, context)
                else:
                    ol = []
                    for child in children:
                        if isinstance(child, Transform):
                            child = child(input, context)
                        elif isinstance(child, collections.Mapping):
                            if '$ins' in child:
                                child = child['$ins'](input, context)
                                if hasattr(child, '__iter__'):
                                    ol.extend(child)
                                    continue
                            elif '$upd' in child:
                                # shouldn't happen
                                child = child['$upd'](input, context)
                        ol.append(child)

                    out['children'] = ol

            return out

        return impl

    def _generate_attribute(self, spec, engine, name, type=None):
        return self._gen_cont_item(spec, engine, name, ToAttribute, type)

    def _gen_cont_item(self, spec, engine, name, cls, type=None):

        if isinstance(spec, collections.Mapping):
            if '$val' in spec:
                return std.resolve_meta_directive(spec['$val'], engine, 
                                                  name+":$val")

            if '$ins' in spec or '$upd' in spec:
                key = '$upd'
                if '$ins' in spec:
                    key = '$ins'
                spec[key] = std.resolve_meta_directive(spec[key], engine, 
                                                          name+":"+key)
                return spec

        # assume this is a cls transform if it isn't some other
        # reference to a transform
        return std.resolve_meta_directive(spec, engine, name, cls)
        
    def _generate_element(self, spec, engine, name, type=None):
        return self._gen_cont_item(spec, engine, name, ToElement, type)
        

class ToElement(Transform):

    def mkfn(self, config, engine):

        tname = self.name or '(xml)'
        ttype = "xml.element"

        try:
            name = _generate_name(config['name'], engine, 
                                  tname+" Element name", ttype)
        except KeyError, ex:
            raise MissingTransformData("name", self.name)

        ns = _generate_value(config.get('namespace'), engine, tname+" El ns", 
                             ttype)
        pref = _generate_name(config.get('prefix'), engine, tname+" El prefix", 
                              ttype)
        content = self._generate_content(config.get('content'), engine, 
                                         tname+" content", ttype)
        prefixes = _generate_object(config.get('prefixes'), engine, 
                                    tname+" prefixes", ttype)
                                   
        def impl(input, context, *args):
            out = {}
            out['name'] = name
            if isinstance(name, Transform):
                out['name'] = name(input, context)
            out['content'] = content
            if isinstance(content, Transform):
                out['content'] = content(input, context)

            if ns:
                out['namespace'] = ns
                if isinstance(ns, Transform):
                    out['namespace'] = ns(input, context)
            if pref:
                out['prefix'] = pref
                if isinstance(pref, Transform):
                    out['prefix'] = pref(input, context)
            if prefixes:
                out['prefixes'] = prefixes
                if isinstance(prefixes, Transform):
                    out['prefixes'] = prefixes(input, context)

            if config.has_key('hints'):
                out['hints'] = copy.deepcopy(config['hints'])

            return out

        return impl

    def _generate_content(self, spec, engine, tname, ttype):
        # a plain object (no $val or $type) is an implicit ToElementContent
        # transform

        if spec is None:
            return None

        return std.resolve_meta_directive(spec, engine, tname, ToElementContent)
        

class ToTextElement(Transform):
    """
    formats an XML element that contains only text as its contents (attributes
    are optional).

    """

    def mkfn(self, config, engine):

        elcfg = copy.deepcopy(config)
        elcfg['$type'] = 'element'
        content = { }
        if "value" in elcfg:
            content['children'] = [ elcfg['value'] ]
            del elcfg['value']
        if "attrs" in elcfg:
            content['attrs'] = [ elcfg['attrs'] ]
            del elcfg['attrs']
        elcfg['content'] = content

        transf = ToElement(elcfg, engine, self.name, 'element', True)

        def impl(input, context, *args):
            return transf(input, context, *args)

        return impl
                    
        

class ToXML(Transform):
    """
    formats XML data into an output string
    """

    def mkfn(self, config, engine):
        try:
            transf = config['element']
        except KeyError, ex:
            raise MissingTransformData("element", self.name)

        if isinstance(transf, dict):
            transf = engine.make_transform(transf)
        elif isinstance(transf, str) or isinstance(transf, unicode):
            transf = engine.resolve_transform(transf)
        else:
            raise TransformConfigTypeError('transform', 'dict or str', 
                                           type(transf))

        def impl(input, context):

            root = transf(input, context)

            return format_element(root, context, None, self.name)

        return impl

types = {
    "xml.print": ToXML,
    "xml.attribute": ToAttribute,
    "xml.elementContent": ToElementContent,
    "xml.element": ToElement,
    "xml.textElement": ToTextElement
}

class InvalidXMLError(TransformInputTypeError):
    """
    XML cannot be properly formatted because the input XML data is invalid.
    """
    def __init__(self, got=None, input=None, context=None, message=None):
                 
        if not got:
            got = str(type(input))
        if not message:
            msg = "Invalid XML data: need an object"
            if got:
                msg += ", got " + got + "."
            message = msg

        super(InvalidXMLError, self).__init__("object", got, None,
                                              input, context, message)

def format_element(el, context, prefixes=None, transname=None):
    """
    format the data in an element data object into XML according to preferences
    from the context.  
    """
    if not isinstance(el, dict):
        raise InvalidXMLError(input=el, context=context)

    if prefixes is None:
        prefixes = ScopedDict()
    else:
        prefixes = ScopedDict(prefixes)

    hints = {}
    newxmlns = None
    if el.get('hints'):
        # The element data carries hints on rendering the data; these override
        # preferences given in the context.  So...
        # load the hints about formatting into our context
        hints = el['hints']
        if hints.get('xmlns') != context.get('xmlns',''):
            newxmlns
        context = Context(context)
        context.update(hints)

    if context.get('xml.style','pretty') == 'compact':
        context['xml.base_indent'] = 0
        context['xml.indent'] = -1
        context['xml.text_packing'] = 'compact'
    elif context.get('xml.value_pad', 0) > 0:
        context['xml.text_packing'] = 'pretty'

    indent = context.get('xml.base_indent', 0)
    step = context.get('xml.indent', 2)

    try: 
        # determine if we need a prefix
        prefix, pfxdefs = determine_prefix(el.get('namespace'), el.get('prefix'),
                                           context, prefixes)

        # preface opening tag with indent
        indentsp = (indent * ' ')
        opentag = indentsp + '<' + prefix + el['name']

        # assemble the attribute data
        atts = el.get('content', {}).get('attrs', [])
        if pfxdefs:
            atts.extend(pfxdefs)
        if el.get('prefixes'):
            for p, ns in el['prefixes'].items():
                if ns not in prefixes or prefixes[ns] != p:
                    prefixes[ns] = p
                    atts.append('xmlns:{0}="{1}"'.format(p, ns))
        if el.get('content', {}).get('children'):
            for child in el['content']['children']:
                p, pfxdefs = determine_prefix(el.get('namespace'), 
                                              el.get('prefix'),
                                              context, prefixes)
                atts.extend(pfxdefs)

        # now insert attributes into the opening tag
        if atts:
            atts = format_atts(atts, len(opentag), context, prefixes)
            opentag += atts

        # format the child nodes
        if not el.get('content', {}).get('children'):
            # there are none
            opentag += '/>'
            if step >= 0:
                opentag += '\n'
            return opentag

        else:
            opentag += '>'
            closetag = '</' + prefix + el['name'] + '>'

            maxlen = context.get('xml.max_line_length', 78)
            minlen = context.get('xml.min_line_length', 30)

            if len(el['content']['children']) == 1 and \
               (isinstance(el['content']['children'][0], str) or 
                isinstance(el['content']['children'][0], unicode)):

               # single text value
               child = el['content']['children'][0]
               if context.get('xml.value_pad', 0) <= 0 or \
                  context.get('xml.text_packing','pretty') == 'pretty' and \
                  len(child) < maxlen - len(opentag) - len(closetag):

                   #short enough to fit into one line
                   if context.get('xml.value_pad', 0) > 0:
                       pad = context['xml.value_pad'] * ' '
                       child = pad + child + pad

                   # return the single line
                   return opentag + child + closetag

            # treat like multi-child content
            parts = [ opentag ]
            subcontext = Context(context)
            if step < 0:
                # don't insert newlines
                subcontext['xml.base_indent'] = 0
                subcontext['xml.indent'] = -1
            else:
                subcontext['xml.base_indent'] = indent + step
                
            for child in el['content']['children']:
                if isinstance(child, str) or isinstance(child, unicode):
                    parts.append(format_text(child, subcontext))
                else:
                    parts.append(format_element(child, subcontext, prefixes))
                                                
            if step < 0:
                parts.append(closetag)
                return ''.join(parts)

            parts.append(indentsp + closetag)
            return '\n'.join(parts)

    except KeyError, ex:
        raise MissingXMLData.due_to(ex, transname)

def format_text(text, context=None):
    """
    format the given text for inclusion as the content for an element
    """
    if not isinstance(text, str) and not isinstance(text, unicode):
        raise InvalidXMLError(input=text, context=context, 
            message="Invalid XML: expected text, got "+str(type(text))+": "+text)

    if context is None:
        context = Context()

    step = context.get('xml.indent', 2)
    pack = context.get('xml.text_packing', 'compact')
    if pack == 'compact' or step < 0:
        return text

    indent = context.get('xml.base_indent', 0)
    if pack == 'loose':
        return (indent * ' ') + text

    maxlen = context.get('xml.max_line_length', 78)
    minlen = context.get('xml.min_line_length', 30)

    sublen = maxlen - indent
    if sublen < minlen:
        sublen = minlen

    return "\n".join(map(lambda l: (indent * ' ') + l, 
                         textwrap.wrap(text, sublen)))

def determine_prefix(ns, prefix, context, prefixes):

    pfxdefs = []

    xmlns = context.get('xml.xmlns', '')
    if ns and not context.get('xml.prefer_prefix', False) and ns == xmlns:
        # namespace matches xmlns
        return ('', pfxdefs)

    if ns:
        if prefix:
            if prefix != prefixes.get(ns):
                prefixes[ns] = prefix
                pfxdefs.append('xmlns:{0}="{1}"'.format(prefix, ns))
        else:
            prefix = prefixes.get(ns)

        if not prefix:
            autopat = re.compile(r'^ns\d+')
            nums = map(lambda i: int(i), 
                       map(lambda p: p[2:], 
                           filter(lambda x: autopat.match(x),
                                  prefixes.values())))
            if not nums:
                nums = [0]
            prefix = 'ns'+str(max(nums)+1)
            prefixes[ns] = prefix
            pfxdefs.append('xmlns:{0}="{1}"'.format(prefix, ns))

    if prefix:
        return (prefix+':', pfxdefs)
    return ('', pfxdefs)

def format_atts(atts, indent, context, prefixes):
    """
    format the attributes for insertion into an opening element tag.
    When many attributes are present, these can be wrapped onto separate lines.
    """
    if not isinstance(atts, list) and not isinstance(atts, tuple):
        raise InvalidXMLError(input=atts, context=context, 
           message="Invalid XML: expected array, got "+str(type(atts))+": "+atts)


    style = context.get('xml.style', 'pretty')
    maxlen = context.get('xml.max_line_length', 78)
    minlen = context.get('xml.min_line_length', 30)
    attlen = maxlen - indent

    out = ['']
    atts = list(atts)
    while len(atts) > 0:
        att = atts.pop(0)
        if isinstance(att, dict):

            prefix, pfxdefs = determine_prefix(att.get('namespace'), 
                                               att.get('prefix'),
                                               context, prefixes)
            if len(pfxdefs) > 0:
                atts.extend(pfxdefs)
            nxt = prefix+att['name'] + '="' + att['value'] + '"'
        else:
            # assume it's already formatted (better be a string)
            nxt = att

        if style == 'pretty' and \
           len(out[-1]) > minlen and len(nxt) + len(out[-1]) + 1 > attlen:
            out.append('')
        out[-1] += ' '+nxt

    if style == 'pretty':
        return ('\n'+(indent * ' ')).join(out)
    return ''.join(out)



class MissingXMLData(TransformApplicationException):

    def __init__(self, message, prop=None, input=None, context=None, name=None, 
                 cause=None):
        """
        construct the exception, providing an explanation.

        :argument str message: an explanation of what went wrong
        :argument str prop:  the name of the missing XML property 
        :argument input:    the JSON data that was being transformed
        :argument context:  the context at the point of the exception
        :argument str name:  the name of the transform being applied when
                             the exception occured.  If None, the exception 
                             is not known or not specific to a particular 
                             transform.
        :argument Exception cause:  the exception representing the underlying 
                                      cause of the exception.  If None, there 
                                      was no such underlying cause.
        """
        super(MissingXMLData, self).__init__(message,input,context,name,cause)
        self.prop = prop

    @classmethod
    def due_to(cls, cause, input=None, context=None, name=None):
        prop = None
        if isinstance(cause, KeyError):
            prop = cause.args[0]

        msg = "Missing XML data"
        if name:
            msg += " in '"+name+"' transform"
        msg += ": "
        msg += (prop or str(cause))
            
        return cls(msg, prop, input, context, name, cause)



        

# load in stylesheet-based definitions 

MOD_STYLESHEET_FILE = "xml_ss.json"

ssfile = os.path.join(os.path.dirname(__file__), MOD_STYLESHEET_FILE)
with open(ssfile) as fd:
    MOD_STYLESHEET = jsp.load(fd)
del ssfile

# load the module's initial context data.  The defaults are specified here 
# for documentation purposes; however, values set wihtin the stylesheet file 
# will take precedence.

p = "xml."

def_context = {

    # The prefered line width to use when filling data into paragraphs by 
    # the fill transform
    #
    p+"max_line_width": 75,

    # The prefered indentation amount to use when filling data into 
    # paragraphs by the fill transform
    # 
    p+"style": 'compact',

    # The number of spaces to add to indentation with each step into the 
    # XML hierarchy
    p+"indent": 2,

    # The number of spaces to indent the current element.  When printing 
    # an entire XML document, the current element is the root element; thus,
    # the whole document will be indented by this much (plus what is added
    # by xml.indent for the root's children).  This parameter is updated 
    # automatically by xml.indent amounts as the document is printed.  
    p+"base_indent": 0
}
del p

# the module's default context data
MOD_CONTEXT = ScopedDict(def_context)
MOD_CONTEXT.update(MOD_STYLESHEET.get('context',{}))
MOD_STYLESHEET['context'] = MOD_CONTEXT

        
        