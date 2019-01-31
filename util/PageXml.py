# -*- coding: utf-8 -*-
import os
import datetime

from lxml import etree


class PageXmlException(Exception):
    pass


class PageXml:
    """
    Various utilities to deal with PageXml format
    """

    # Namespace for PageXml
    NS_PAGE_XML = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"

    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    XSILOCATION = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15 " \
                  "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd"

    # Schema for Transkribus PageXml
    XSL_SCHEMA_FILENAME = "pagecontent.xsd"

    # XML schema loaded once for all
    cachedValidationContext = None

    sMETADATA_ELT = "Metadata"
    sCREATOR_ELT = "Creator"
    sCREATED_ELT = "Created"
    sLAST_CHANGE_ELT = "LastChange"
    sCOMMENTS_ELT = "Comments"
    sTranskribusMetadata_ELT = "TranskribusMetadata"
    sCUSTOM_ATTR = "custom"

    sEXT = ".pxml"

    def __init__(self):
        pass

    # =========== SCHEMA ===========

    @classmethod
    def validate(cls, doc):
        """
        Validate against the PageXml schema used by Transkribus

        Return True or False
        """
        #         schDoc = cls.getSchemaAsDoc()
        if not cls.cachedValidationContext:
            schema_filename_ = cls.get_schema_filename()
            #             buff = open(schemaFilename).read()
            xmlschema_doc = etree.parse(schema_filename_)
            xmlschema = etree.XMLSchema(xmlschema_doc)

            #             prsrCtxt = libxml2.schemaNewMemParserCtxt(buff, len(buff))
            #             schema = prsrCtxt.schemaParse()
            #             cls.cachedValidationContext = schema.schemaNewValidCtxt()
            cls.cachedValidationContext = xmlschema
        #             del buff , prsrCtxt

        #         res = cls.cachedValidationContext.schemaValidateDoc(doc)
        b_valid = cls.cachedValidationContext.validate(doc)
        log = cls.cachedValidationContext.error_log
        if not b_valid:
            print(log)
        return b_valid

    @classmethod
    def get_schema_filename(cls):
        """
        Return the path to the schema, built from the path of this module.
        """
        filename = os.path.join(os.path.dirname(__file__), cls.XSL_SCHEMA_FILENAME)
        return filename

    # =========== METADATA ===========
    """
    <complexType name="MetadataType">
        <sequence>
            <element name="Creator" type="string"></element>
            <element name="Created" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="LastChange" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="Comments" type="string" minOccurs="0"
                maxOccurs="1"></element>
        </sequence>
    </complexType>
    """

    @classmethod
    def get_metadata(cls, doc=None, dom_nd=None):
        """
        Parse the metadata of the PageXml DOM or of the given Metadata node
        return a Metadata object
        """
        _, nd_creator, nd_created, nd_last_change, nd_comments = cls._get_metadata_nodes(doc, dom_nd)
        return Metadata(nd_creator.text
                        , nd_created.text
                        , nd_last_change.text
                        , nd_comments.text if nd_comments is not None else None)

    @classmethod
    def set_metadata(cls, doc, dom_nd, creator, comments=None):
        """
        Pass EITHER a DOM or a Metadata DOM node!! (and pass None for the other)
        Set the metadata of the PageXml DOM or of the given Metadata node

        Update the Created and LastChange fields.
        Either update the comments fields or delete it.

        You MUST indicate the creator (a string)
        You MAY give a comments (a string)
        The Created field is kept unchanged
        The LastChange field is automatically set.
        The comments field is either updated or deleted.
        return the Metadata DOM node
        """
        nd_metadata, nd_creator, nd_created, nd_last_change, nd_comments = cls._get_metadata_nodes(doc, dom_nd)
        nd_creator.text = creator
        # The schema seems to call for GMT date&time  (IMU)
        # ISO 8601 says:  "If the time is in UTC, add a Z directly after the time without a space. Z is the zone
        # designator for the zero UTC offset."
        # Python seems to break the standard unless one specifies properly a timezone by sub-classing tzinfo.
        # But too complex stuff so, I simply add a 'Z'
        nd_last_change.text = datetime.datetime.utcnow().isoformat() + "Z"
        if comments is not None:
            if not nd_comments:  # we need to add one!
                nd_comments = etree.SubElement(nd_metadata, cls.sCOMMENTS_ELT)
            nd_comments.text = comments
        return nd_metadata

    # =========== XML STUFF ===========
    @classmethod
    def get_child_by_name(cls, elt, s_child_name):
        """
        look for all child elements having that name in PageXml namespace!!!
            Example: lNd = PageXMl.get_child_by_name(elt, "Baseline")
        return a DOM node
        """
        # return elt.findall(".//{%s}:%s"%(cls.NS_PAGE_XML,s_child_name))
        return elt.xpath(".//pc:%s" % s_child_name, namespaces={"pc": cls.NS_PAGE_XML})

    @classmethod
    def get_ancestor_by_name(cls, elt, s_name):
        return elt.xpath("ancestor::pc:%s" % s_name, namespaces={"pc": cls.NS_PAGE_XML})

    @classmethod
    def get_custom_attr(cls, nd, s_attr_name, s_sub_attr_name=None):
        """
        Read the custom attribute, parse it, and extract the 1st or 1st and 2nd key value
        e.g. get_custom_attr(nd, "structure", "type")     -->  "catch-word"
        e.g. get_custom_attr(nd, "structure")             -->  {'type':'catch-word', "toto", "tutu"}
        return a dictionary if no 2nd key provided, or a string if 1st and 2nd key provided
        Raise KeyError is one of the attribute does not exist
        """
        ddic = cls.parse_custom_attr(nd.get(cls.sCUSTOM_ATTR))

        # First key
        try:
            dic2 = ddic[s_attr_name]
            if s_sub_attr_name:
                return dic2[s_sub_attr_name]
            else:
                return dic2
        except KeyError as e:
            raise PageXmlException("node %s: %s and %s not found in %s" % (nd, s_attr_name, s_sub_attr_name, ddic))

    @classmethod
    def set_custom_attr(cls, nd, s_attr_name, s_sub_attr_name, s_val):
        """
        Change the custom attribute by setting the value of the 1st+2nd key in the DOM
        return the value
        Raise KeyError is one of the attribute does not exist
        """
        ddic = cls.parse_custom_attr(nd.get(cls.sCUSTOM_ATTR))
        try:
            ddic[s_attr_name][s_sub_attr_name] = str(s_val)
        except KeyError:
            ddic[s_attr_name] = dict()
            ddic[s_attr_name][s_sub_attr_name] = str(s_val)

        sddic = cls.format_custom_attr(ddic)
        nd.set(cls.sCUSTOM_ATTR, sddic)
        return s_val

    @classmethod
    def parse_custom_attr(cls, s):
        """
        The custom attribute contains data in a CSS style syntax.
        We parse this syntax here and return a dictionary of dictionary

        Example:
        parse_custom_attr( "readingOrder {index:4;} structure {type:catch-word;}" )
            --> { 'readingOrder': { 'index':'4' }, 'structure':{'type':'catch-word'} }
        """
        dic = dict()

        s = s.strip()
        l_chunk = s.split('}')
        if l_chunk:
            for chunk in l_chunk:  # things like  "a {x:1"
                chunk = chunk.strip()
                if not chunk: continue

                try:
                    s_names, s_values = chunk.split('{')  # things like: ("a,b", "x:1 ; y:2")
                except Exception:
                    raise ValueError("Expected a '{' in '%s'" % chunk)

                # the dictionary for that name
                dic_val_for_name = dict()

                ls_key_val = s_values.split(';')  # things like  "x:1"
                for sKeyVal in ls_key_val:
                    if not sKeyVal.strip():
                        continue  # empty
                    try:
                        s_key, s_val = sKeyVal.split(':')
                    except Exception:
                        raise ValueError("Expected a comma-separated string, got '%s'" % sKeyVal)
                    dic_val_for_name[s_key.strip()] = s_val.strip()

                l_name = s_names.split(',')
                for name in l_name:
                    dic[name.strip()] = dic_val_for_name
        return dic

    @classmethod
    def format_custom_attr(cls, ddic):
        """
        Format a dictionary of dictionary of string in the "custom attribute" syntax
        e.g. custom="readingOrder {index:1;} structure {type:heading;}"
        """
        s = ""
        for k1, d2 in ddic.items():
            if s:
                s += " "
            s += "%s" % k1
            s2 = ""
            for k2, v2 in d2.items():
                if s2:
                    s2 += " "
                s2 += "%s:%s;" % (k2, v2)
            s += " {%s}" % s2
        return s

    @classmethod
    def make_text(cls, nd, ctxt=None):
        """
        build the text of a sub-tree by considering that textual nodes are tokens to be concatenated, with a space as separator
        NO! (JLM 2018)return None if no textual node found

        return empty string if no text node found
        """
        return " ".join(nd.itertext())

    def add_prefix(cls, s_prefix, nd, s_attr="id"):
        """
        Utility to add a add_prefix to a certain attribute of a sub-tree.

        By default works on the 'id' attribute

        return the number of modified attributes
        """
        s_attr = s_attr.strip()
        l_nd = nd.xpath(".//*[@%s]" % s_attr)
        ret = len(l_nd)
        for nd in l_nd:
            s_new_value = s_prefix + nd.get(s_attr)
            nd.set(s_attr, s_new_value)
        #         ctxt.xpathFreeContext()
        return ret

    add_prefix = classmethod(add_prefix)

    @classmethod
    def rm_prefix(cls, s_prefix, nd, s_attr="id"):
        """
        Utility to remove a add_prefix from a certain attribute of a sub-tree.

        By default works on the 'id' attribute

        return the number of modified attributes
        """
        s_attr = s_attr.strip()
        #         ctxt = nd.doc.xpathNewContext()
        #         ctxt.setContextNode(nd)
        l_nd = nd.findall(".//*[@%s]" % s_attr)
        n = len(s_prefix)
        ret = len(l_nd)
        for nd in l_nd:
            s_value = nd.get(s_attr)
            assert s_value.startswith(s_prefix), "Prefix '%s' from attribute '@%s=%s' is missing" % (
                s_prefix, s_attr, s_value)
            s_new_value = s_value[n:]
            nd.set(s_attr, s_new_value)

        #         ctxt.xpathFreeContext()
        return ret

    @classmethod
    def _get_metadata_nodes(cls, doc=None, dom_nd=None):
        """
        Parse the metadata of the PageXml DOM or of the given Metadata node
        return a 4-tuple:
            DOM nodes of Metadata, Creator, Created, Last_Change, Comments (or None if no comments)
        """
        assert doc is None or dom_nd is None, "Internal error: pass either a DOM or a Metadata node"  # XOR
        if doc:
            l_nd = cls.get_child_by_name(doc.getroot(), cls.sMETADATA_ELT)
            if len(l_nd) != 1:
                raise ValueError("PageXml should have exactly one %s node" % cls.sMETADATA_ELT)
            dom_nd = l_nd[0]
            assert etree.QName(dom_nd.tag).localname == cls.sMETADATA_ELT
        #         nd1 = dom_nd.firstElementChild()
        nd1 = dom_nd[0]

        if etree.QName(nd1.tag).localname != cls.sCREATOR_ELT:
            raise ValueError("PageXMl mal-formed Metadata: Creator element must be 1st element")

        nd2 = nd1.getnext()
        if etree.QName(nd2.tag).localname != cls.sCREATED_ELT:
            raise ValueError("PageXMl mal-formed Metadata: Created element must be 2nd element")

        nd3 = nd2.getnext()
        if etree.QName(nd3.tag).localname != cls.sLAST_CHANGE_ELT:
            raise ValueError("PageXMl mal-formed Metadata: LastChange element must be 3rd element")

        nd4 = nd3.getnext()
        if nd4 is not None:
            if etree.QName(nd4.tag).localname not in [cls.sCOMMENTS_ELT, cls.sTranskribusMetadata_ELT]:
                raise ValueError("PageXMl mal-formed Metadata: LastChange element must be 3rd element")
        return dom_nd, nd1, nd2, nd3, nd4

    # =========== GEOMETRY ===========
    @classmethod
    def get_point_list(cls, data):
        """
        get either an XML node of a PageXml object
              , or the content of a points attribute

        return the list of (x,y) of the polygon of the object - ( it is a list of int tuples)
        """
        try:
            ls_pair = data.split(' ')
        except AttributeError:
            lnd_points = data.xpath("(.//@points)[1]")
            s_points = lnd_points[0]  # .getContent()
            ls_pair = s_points.split(' ')
        l_xy = list()
        for sPair in ls_pair:
            (sx, sy) = sPair.split(',')
            l_xy.append((int(sx), int(sy)))
        return l_xy

    @classmethod
    def set_points(cls, nd, l_xy):
        """
        set the points attribute of that node to reflect the l_xy values
        if nd is None, only returns the string that should be set to the @points attribute
        return the content of the @points attribute
        """
        s_pairs = " ".join(["%d,%d" % (int(x), int(y)) for x, y in l_xy])
        if nd is not None: nd.set("points", s_pairs)
        return s_pairs

    @classmethod
    def get_points_from_bb(cls, x1, y1, x2, y2):
        """
        get the polyline of this bounding box
        return a list of int tuples
        """
        return [(x1, y1), (x2, y1), (x2, y2), (x1, y2), (x1, y1)]

    # =========== CREATION ===========
    @classmethod
    def create_page_xml_document(cls, creator_name='NLE', filename=None, img_w=0, img_h=0):
        """
            create a new PageXml document
        """
        xml_page_root = etree.Element('{%s}PcGts' % cls.NS_PAGE_XML,
                                      attrib={"{" + cls.NS_XSI + "}schemaLocation": cls.XSILOCATION},
                                      nsmap={None: cls.NS_PAGE_XML})
        xml_page_doc = etree.ElementTree(xml_page_root)

        metadata = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sMETADATA_ELT))
        xml_page_root.append(metadata)
        creator = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sCREATOR_ELT))
        creator.text = creator_name
        created = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sCREATED_ELT))
        created.text = datetime.datetime.now().isoformat()
        last_change = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sLAST_CHANGE_ELT))
        last_change.text = datetime.datetime.utcnow().isoformat() + "Z"
        metadata.append(creator)
        metadata.append(created)
        metadata.append(last_change)

        page_node = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, 'Page'))
        page_node.set('imageFilename', filename)
        page_node.set('imageWidth', str(img_w))
        page_node.set('imageHeight', str(img_h))

        xml_page_root.append(page_node)

        b_validate = cls.validate(xml_page_doc)
        assert b_validate, 'new file not validated by schema'

        return xml_page_doc, page_node

    @classmethod
    def create_page_xml_node(cls, nodeName):
        """
            create a PageXMl element
        """
        node = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, nodeName))

        return node


# =========== METADATA OF PAGEXML ===========
class Metadata:
    """
    <complexType name="MetadataType">
        <sequence>
            <element name="Creator" type="string"></element>
            <element name="Created" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="LastChange" type="dateTime">
                <annotation>
                    <documentation>The timestamp has to be in UTC (Coordinated Universal Time) and not local time.</documentation></annotation></element>
            <element name="Comments" type="string" minOccurs="0"
                maxOccurs="1"></element>
        </sequence>
    </complexType>
    """

    def __init__(self, creator, created, last_change, comments=None):
        self.Creator = creator  # a string
        self.Created = created  # a string
        self.LastChange = last_change  # a string
        self.Comments = comments  # None or a string


if __name__ == "__main__":

    import sys, glob, optparse

    usage = """%s dirname + Utility to create a set of MultipageXml XML files from a set of folders, 
    each containing several PageXml files.""" % sys.argv[0]

    parser = optparse.OptionParser(usage=usage)

    parser.add_option("--format", dest='bIndent', action="store_true"
                      , help="reformat/reindent the input")
    parser.add_option("--compress", dest='bCompress', action="store_true"
                      , help="Turn on gzip compression of output")
    parser.add_option("--ext", dest='extension', action="store", default=''
                      , help="process only .ext ")
    (options, args) = parser.parse_args()

    try:
        lsDir = args
        lsDir[0]
    except:
        parser.print_help()
        parser.exit(1, "")

    print("TODO: ", lsDir)

    for sDir in lsDir:
        if not os.path.isdir(sDir):
            print("skipping %s (not a directory)" % sDir)
            continue

        print("Processing %s..." % sDir, )
        if options.extension != '':
            l = glob.glob(os.path.join(sDir, "*.%s" % options.extension))
        else:
            l = glob.glob(os.path.join(sDir, "*.xml"))
            l.extend(glob.glob(os.path.join(sDir, "*.pxml")))
            l.extend(glob.glob(os.path.join(sDir, "*.xml.gz")))
            l.extend(glob.glob(os.path.join(sDir, "*.pxml.gz")))
        l.sort()
        print("   %d pages" % len(l))

        doc = MultiPageXml.makeMultiPageXml(l)
        print(MultiPageXml.validate(doc))
        filename = sDir + ".mpxml"
        if options.bCompress:
            iCompress = 9
        #             doc.setDocCompressMode(9)
        else:
            iCompress = 0
        #             doc.setDocCompressMode(0)

        doc.write(filename, encoding='UTF-8', xml_declaration=True, compression=iCompress)
        #             doc.setDocCompressMode(0)

        #         doc.saveFormatFileEnc(filename, "utf-8", bool(options.bIndent))
        #         doc.freeDoc()
        del (doc)

        print("\t done: %s" % filename)

    print("DONE")
