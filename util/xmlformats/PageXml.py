# -*- coding: utf-8 -*-
import os
import datetime
import logging

import cssutils
from lxml import etree
from argparse import ArgumentParser

from util.xmlformats.PageObjects import TextLine

# Make sure that the css parser for the custom attribute doesn't spam "WARNING Property: Unknown Property name."
cssutils.log.setLevel(logging.ERROR)


class PageXmlException(Exception):
    pass


class PageXml:
    """
    Various utilities to deal with PageXml format
    """
    # Creators name
    sCREATOR = "CITlab"

    # Namespace for PageXml
    NS_PAGE_XML = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15"

    NS_XSI = "http://www.w3.org/2001/XMLSchema-instance"
    XSILOCATION = "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15 " \
                  "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd"

    # Schema for Transkribus PageXml
    XSL_SCHEMA_FILENAME = "pagecontent_transkribus.xsd"

    # XML schema loaded once for all
    cachedValidationContext = None

    sMETADATA_ELT = "Metadata"
    sCREATOR_ELT = "Creator"
    sCREATED_ELT = "Created"
    sLAST_CHANGE_ELT = "LastChange"
    sCOMMENTS_ELT = "Comments"
    sTranskribusMetadata_ELT = "TranskribusMetadata"
    sCUSTOM_ATTR = "custom"
    sTEXTLINE = "TextLine"
    sBASELINE = "Baseline"

    sEXT = ".xml"

    # Article Separation "other" class
    sAS_OTHER = "aOther"

    def __init__(self):
        pass

    # =========== SCHEMA ===========

    @classmethod
    def validate(cls, doc):
        """
        Validate against the PageXml schema used by Transkribus

        Return True or False
        """
        if not cls.cachedValidationContext:
            schema_filename_ = cls.get_schema_filename()
            xmlschema_doc = etree.parse(schema_filename_)
            cls.cachedValidationContext = etree.XMLSchema(xmlschema_doc)

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

    @classmethod
    def _get_metadata_nodes(cls, doc=None, dom_nd=None):
        """
        Parse the metadata of the PageXml DOM or of the given Metadata node
        return a 4-tuple:
            DOM nodes of Metadata, Creator, Created, Last_Change, Comments (or None if no comments)
        """
        # TODO: Changed assert, s.t. it is checked if doc and dom_nd are None -> check!
        assert doc is None or dom_nd is None or (doc is None and dom_nd is None), \
            "Internal error: pass either a DOM or a Metadata node"  # XOR
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
                raise ValueError("PageXMl mal-formed Metadata: Comments element must be 4th element")
        return dom_nd, nd1, nd2, nd3, nd4

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
    def get_child_by_id(cls, elt, id):
        """
        look for all child elements having that id
            Example: lNd = PageXMl.get_child_by_id(elt, "tl_2")
        return a DOM node
        """
        return elt.xpath(".//*[@id='%s']" % id)

    @classmethod
    def get_ancestor_by_id(cls, elt, id):
        """
        look for all ancestor elements having that id
            Example: lNd = PageXMl.get_ancestor_by_name(elt, "tl_2")
        return a DOM node
        """
        return elt.xpath("ancestor::*[@id='%s']" % id)

    @classmethod
    def get_custom_attr(cls, nd, s_attr_name, s_sub_attr_name=None):
        """
        Read the custom attribute, parse it, and extract the 1st or 1st and 2nd key value
        e.g. get_custom_attr(nd, "structure", "type")     -->  "catch-word"
        e.g. get_custom_attr(nd, "structure")             -->  {'type':'catch-word', "toto", "tutu"}
        return a dictionary if no 2nd key provided, or a string if 1st and 2nd key provided
        Raise KeyError if one of the attribute does not exist
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
        Raise KeyError if one of the attributes does not exist
        """
        if s_val is None:
            return None
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
        We parse this syntax here and return a dictionary of dictionaries

        Example:
        parse_custom_attr( "readingOrder {index:4;} structure {type:catch-word;}" )
            --> { 'readingOrder': { 'index':'4' }, 'structure':{'type':'catch-word'} }
        """
        custom_dict = {}
        sheet = cssutils.parseString(s)
        for rule in sheet:
            selector = rule.selectorText
            prop_dict = {}
            for prop in rule.style:
                prop_dict[prop.name] = prop.value
            custom_dict[selector] = prop_dict

        return custom_dict

    @classmethod
    def format_custom_attr(cls, ddic):
        """
        Format a dictionary of dictionaries in string format in the "custom attribute" syntax
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
    def get_text_equiv(cls, nd):
        textequiv = cls.get_child_by_name(nd, "TextEquiv")
        if not textequiv:
            return ''
        text = cls.get_child_by_name(textequiv[0], "Unicode")
        if not text:
            return ''
        return text[0].text

    @classmethod
    def make_text(cls, nd):
        """
        build the text of a sub-tree by considering that textual nodes are tokens to be concatenated, with a space as separator
        NO! (JLM 2018)return None if no textual node found

        return empty string if no text node found
        """
        return " ".join(nd.itertext())

    # =========== GEOMETRY ===========
    @classmethod
    def get_point_list(cls, data):
        """
        get either an XML node of a PageXml object
              , or the content of a points attribute, e.g.
                1340,240 1696,240 1696,304 1340,304
        return the list of (x,y) of the polygon of the object - ( it is a list of int tuples)
        """
        try:
            ls_pair = data.split(' ')
        except AttributeError:
            lnd_points = data.xpath("(.//@points)[1]")
            s_points = lnd_points[0]
            ls_pair = s_points.split(' ')
        l_xy = list()
        for s_pair in ls_pair:  # s_pair = 'x,y'
            (sx, sy) = s_pair.split(',')
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
        if nd is not None:
            nd.set("points", s_pairs)
        return s_pairs

    # ======== ARTICLE STUFF =========

    @classmethod
    def get_article_dict(cls, nd):
        global article_id
        textline_nds = cls.get_child_by_name(nd, "TextLine")
        article_dict = {}
        for tl in textline_nds:
            # get article_id, baseline and text of a textline
            try:
                structure = cls.get_custom_attr(tl, "structure")
                # structure = cls.get_custom_attr(tl.attrib["custom"], "structure")
                if structure["type"] == "article":
                    article_id = structure["id"]
            except PageXmlException:
                article_id = None
            baseline = PageXml.get_child_by_name(tl, "Baseline")
            baseline = baseline[0] if len(baseline) == 1 else None
            if baseline is not None:
                pt_list = cls.get_point_list(baseline)
            else:
                pt_list = []
            text = cls.get_text_equiv(tl)
            textline = TextLine(tl.get("id"), cls.parse_custom_attr(tl.get("custom")), pt_list, text)

            if article_id:
                if article_id in article_dict:
                    article_dict[article_id].append(textline)
                else:
                    article_dict[article_id] = [textline]
            else:
                if cls.sAS_OTHER in article_dict:
                    article_dict[cls.sAS_OTHER].append(textline)
                else:
                    article_dict[cls.sAS_OTHER] = [textline]

        return article_dict

    @classmethod
    def get_textlines(cls, nd):
        tl_nds = cls.get_child_by_name(nd, cls.sTEXTLINE)

        return [TextLine(tl.get("id"), cls.parse_custom_attr(tl.get(cls.sCUSTOM_ATTR)),
                         cls.get_point_list(cls.get_child_by_name(tl, cls.sBASELINE)[0]),
                         cls.get_text_equiv(tl))
                for tl in tl_nds]

    @classmethod
    def set_textline_attr(cls, nd, textlines):
        """nd must be the tree node!

        :param nd: DOM node
        :param textline: list of TextLine objects
        :type textline: list of TextLine
        :return: None
        """
        for tl in textlines:
            tl_nd = cls.get_child_by_id(nd, tl.id)[0]
            for k, d in tl.custom.items():
                for k1, v1 in d.items():
                    cls.set_custom_attr(tl_nd, k, k1, v1)

            # if tl.get_article_id() is None:
            #     continue
            # tl_nd = cls.get_child_by_id(nd, tl.id)[0]
            # cls.set_custom_attr(tl_nd, "structure", "id", tl.get_article_id())
            # cls.set_custom_attr(tl_nd, "structure", "type", "article")

    # =========== CREATION ===========
    @classmethod
    def create_page_xml_document(cls, creator_name=sCREATOR, filename=None, img_w=0, img_h=0):
        """
            create a new PageXml document
        """
        xml_page_root = etree.Element('{%s}PcGts' % cls.NS_PAGE_XML,
                                      attrib={"{" + cls.NS_XSI + "}schemaLocation": cls.XSILOCATION},  # schema loc.
                                      nsmap={None: cls.NS_PAGE_XML})  # Default ns
        xml_page_doc = etree.ElementTree(xml_page_root)

        metadata = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sMETADATA_ELT))
        xml_page_root.append(metadata)
        creator = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sCREATOR_ELT))
        creator.text = creator_name
        created = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, cls.sCREATED_ELT))
        created.text = datetime.datetime.utcnow().isoformat() + "Z"
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
    def create_page_xml_node(cls, node_name):
        """
            create a PageXMl element
        """
        node = etree.Element('{%s}%s' % (cls.NS_PAGE_XML, node_name))

        return node

    @classmethod
    def load_page_xml(cls, path_to_xml: str):
        """Load PageXml file located at ``path_to_xml`` and return a DOM node.

        :param path_to_xml: path to PageXml file
        :return: DOM document node
        :rtype: etree._ElementTree
        """
        page_doc = etree.parse(path_to_xml)
        if not PageXml.validate(page_doc):
            print("PageXml is not valid according to the Page schema definition {}.".format(cls.get_schema_filename))
        return page_doc

    @classmethod
    def load_metadata_page(cls, doc_nd):
        try:
            return doc_nd.getroot().getchildren()
        except AttributeError:
            print("The doc node must be of type lxml.etree._ElementTree but is {}".format(type(doc_nd)))
            return None

    @classmethod
    def write_page_xml(cls, save_path: str, page_doc: etree._ElementTree, creator=sCREATOR, comments=None):
        """Save PageXml file to ``save_path``.

        @:param save_path:
        @:return: None
        """
        PageXml.set_metadata(page_doc, None, creator, comments)

        with open(save_path, "w") as f:
            f.write(etree.tostring(page_doc, pretty_print=True, encoding="UTF-8", standalone=True, xml_declaration=True)
                    .decode("utf-8"))


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
    parser = ArgumentParser()
    parser.add_argument('--path_to_xml', default='', type=str, metavar="STR",
                        help="path to the PageXml file")
    flags = parser.parse_args()

    page_doc = PageXml.load_page_xml(flags.path_to_xml)

    # path_to_xml = "./test/resources/page_test.xml"
    # page_doc = load_page_xml(path_to_xml)

    metadata_nd, page_nd = PageXml.load_metadata_page(page_doc)

    textlines = PageXml.get_textlines(page_nd)
    PageXml.set_textline_attr(page_nd, textlines)

    # article_dict = PageXml.get_article_dict(page_nd)

    # # doing some changes to the article_dict - change the third entry of the 'other' class to 'a1'
    # tl_other_3 = article_dict[PageXml.sAS_OTHER][2]
    # tl_other_3_id = tl_other_3.id
    # print(tl_other_3.get_article_id())
    # print(tl_other_3.get_reading_order())
    #
    # tl_other_3.set_article_id("a3")
    # print(tl_other_3.get_article_id())
    #
    # nd = PageXml.get_child_by_id(page_doc, tl_other_3_id)
    # print("Number of nodes with id {}: {}".format(tl_other_3_id, len(nd)))
    #
    # PageXml.set_custom_attr(nd[0], "structure", "id", tl_other_3.get_article_id())
    PageXml.write_page_xml("./test/resources/page_xml_copy.xml", page_doc)

    # print(article_dict["a1"][0].text)
    # print(article_dict["a1"][0].baseline)
    # print(article_dict["a1"][0].id)
    # print(article_dict["a1"][0].custom)
    # print(article_dict["other"][0].custom)
    # if "structure" not in article_dict["other"][0].custom:
    #     article_dict["other"][0].custom["structure"] = {}
    # article_dict["other"][0].custom["structure"]["id"] = "a1"
    # print(article_dict["other"][0].custom)
    # print("Baseline Text Dictionary: {}".format(article_dict))
    #
    # tmp = page_doc.xpath(".//*[@id='%s']" % article_dict["other"][0].id)
    # PageXml.set_custom_attr(tmp[0], "structure", "id", article_dict["other"][0].custom["structure"]["id"])
    # # print("TEXT: ", PageXml.get_text_equiv(tmp[0]))
    #

    # page_doc, page_nd = PageXml.create_page_xml_document(creator_name="Max Weidemann",
    #                                                      filename="newimg.tif", img_w=20, img_h=20)
    #
    # with open("./test/resources/test.xml", "w") as f:
    #     f.write(etree.tostring(page_doc, pretty_print=True, encoding="UTF-8", standalone=True, xml_declaration=True)
    #             .decode("utf-8"))
