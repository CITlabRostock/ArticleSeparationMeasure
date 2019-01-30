# -*- coding: utf-8 -*-

"""This module parses PAGEXML-files to extract informations for, e.g., Article Separation or Handwriting Text
Recognition. The PAGE format is described at
    http://www.ocr-d.de/sites/all/gt_guidelines/trPage.html
    https://github.com/PRImA-Research-Lab/PAGE-XML
    http://www.primaresearch.org/tools/PAGELibraries
    https://www.primaresearch.org/schema/PAGE/gts/pagecontent/2017-07-15/pagecontent.xsd
"""

from xml.etree import ElementTree as ET
import numpy as np
import datetime
import os
from uuid import uuid4
from abc import ABCMeta

from geometry import Polygon

# https://docs.python.org/3.5/library/xml.etree.elementtree.html#parsing-xml-with-namespaces
_ns = {'p': 'http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15'}
_attribs = {'xmlns:xsi': "http://www.w3.org/2001/XMLSchema-instance",
            'xsi:schemaLocation': "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15 "
                                  "http://schema.primaresearch.org/PAGE/gts/pagecontent/2013-07-15/pagecontent.xsd"}


def _try_to_int(d):
    """Convert ``d`` to int.

    :param d: value to convert
    :type d: Union[str,int]
    :return: int representation of input
    """
    if isinstance(d, (str, np.int32, np.int64)):
        return int(d)
    else:
        return d


def _get_text_equiv(e):
    """Returns the text of the PAGEXML-Element ``e``.

    :param e: xml element
    :type e: ET.Element
    :return: text equiv of e
    """
    tmp = e.find('p:TextEquiv', _ns)
    if tmp is None:
        return ''
    tmp = tmp.find('p:Unicode', _ns)
    if tmp is None:
        return ''
    return tmp.text


class Point:
    """Point (x,y) class according to
        http://www.ocr-d.de/sites/all/gt_guidelines/pagecontent_xsd_Simple_Type_pc_PointsType.html

    :ivar x: horizontal coordinate
    :ivar y: vertical coordinate

    """

    def __init__(self, x, y):
        self.x = x
        self.y = y

    @classmethod
    def list_from_xml(cls, etree_elem):
        """Converts a PAGEXML-formatted set of coordinates to a list of ``Point``, example:
            `<Coords points="1340,240 1696,240 1696,304 1340,304"/>`

        :param etree_elem: etree XML element containing a set of coordinates
        :return: a list of coordinates as Point
        """
        if etree_elem is None:
            return []
        points = etree_elem.attrib['points']
        result = []
        for p in points.split(' '):
            values = p.split(',')
            assert len(values) == 2
            x, y = int(float(values[0])), int(float(values[1]))
            result.append(Point(x, y))
        return result

    @classmethod
    def list_point_to_string(cls, list_points):
        """Converts a list of ``Point`` to a string 'x1,y1 x2,y2 x3,y3 ...'.

        :param list_points: list of coordinates with `Point` format
        :return: a string with the coordinates
        """
        return ' '.join(['{},{}'.format(p.x, p.y) for p in list_points])

    @classmethod
    def list_to_point(cls, list_coords):
        """Converts a list of coordinates to a list of `Point`

        :param list_coords: list of coordinates, shape (N, 2)
        :return: list of Points
        """
        return [cls(coord[0], coord[1]) for coord in list_coords if list_coords]

    @classmethod
    def point_to_list(cls, points):
        """Converts a list of `Point` to a list of coordinates

        :param points: list of Points
        :return: list of shape (N,2)
        """
        return [[pt.x, pt.y] for pt in points]

    @classmethod
    def list_point_to_polygon(cls, points):
        """Converts a list of ``Point`` to a Polygon object.

        :param points: list of Point objects
        :type points: list of Point
        :return: Polygon object
        """
        x, y = np.transpose(Point.point_to_list(points))
        return Polygon(x.tolist(), y.tolist(), n_points=len(x))

    @classmethod
    def list_to_polygon(cls, coords):
        """Converts a list of coordinates ``coords`` to a Polygon object.

        :param coords: list of coordinates, shape (N, 2)
        :return: Polygon object
        """
        x, y = np.transpose(coords)
        return Polygon(x, y, n_points=len(x))


class Text:
    """Text entity produced by a transcription system.

    :ivar text_equiv: the transcription of the text
    :ivar alternatives: alternative transcriptions
    :ivar score: the confidence of the transcription output by the transcription system
    """

    def __init__(self, text_equiv=None, alternatives=None, score=None):
        self.text_equiv = text_equiv  # if text_equiv is not None else ''
        self.alternatives = alternatives  # if alternatives is not None else []
        self.score = score  # if score is not None else ''


class BaseElement:
    """
    Base page element class. (Abstract - Equivalent to Java Interfaces)
    Every subclass of BaseElement has a unique tag.
    """
    __metaclass__ = ABCMeta

    tag = None

    @classmethod
    def full_tag(cls):
        return '{{{}}}{}'.format(_ns['p'], cls.tag)

    @classmethod
    def check_tag(cls, tag):
        assert tag == cls.full_tag(), 'Invalid tag, expected {} got {}'.format(cls.full_tag(), tag)


class Region(BaseElement):
    """
    Region base class. (Abstract)
    This is the superclass for all the extracted regions. Possible region types are:

    - TextRegion (Pure text is represented as a text region. This includes drop capitals, but practically ornate text may be considered as a graphic.)
    - ImageRegion (An image is considered to be more intricate and complex than a graphic. These can be photos or drawings.)
    - LineDrawingRegion (A line drawing is a single colour illustration without solid areas.)
    - GraphicRegion (Regions containing simple graphics, such as a company logo, should be marked as graphic regions.)
    - TableRegion (Tabular data in any form is represented with a table region. Rows and columns may or may not have separator lines; these lines are not separator regions.)
    - ChartRegion (Regions containing charts or graphs of any type, should be marked as chart regions.)
    - SeparatorRegion (Separators are lines that lie between columns and paragraphs and can be used to logically separate different articles from each other.)
    - MathsRegion (Regions containing equations and mathematical symbols should be marked as maths regions.)
    - ChemRegion (Regions containing chemical formulas.)
    - MusicRegion (Regions containing musical notations.)
    - AdvertRegion (Regions containing advertisements.)
    - NoiseRegion (Noise regions are regions where no real data lies, only false data created by artifacts on the document or scanner noise.)
    - UnknownRegion (To be used if the region type cannot be ascertained.)

    according to http://www.ocr-d.de/sites/all/gt_guidelines/pagecontent_xsd_Complex_Type_pc_RegionType.html.

    :ivar id: identifier of the `Region`
    :ivar coords: coordinates of the `Region`
    """
    tag = 'Region'

    def __init__(self, id=None, coords=None, custom=None):
        self.id = id
        self.coords = coords if coords is not None else []
        self.custom = custom if custom is not None else ''

    @classmethod
    def from_xml(cls, etree_element):
        """Creates a dictionary from an XML structure in order to create the inherited objects

        :param etree_element: an XML etree
        :return: a dictionary with keys 'id' and 'coords'
        """
        return {'id': etree_element.attrib.get('id'),
                'coords': Point.list_from_xml(etree_element.find('p:Coords', _ns)),
                'custom': etree_element.attrib.get('custom')}

    def parse_custom(self):
        """Parses the custom tag of the region and returns the values as a dictionary of dictionaries, e.g.:
            `custom="readingOrder {index:0;} structure {id:a1; type:article;}` returns
            `{'readingOrder':{'index':'0'}, 'structure':{'id':'a1', type:'article'}}`
        :return: dict of dict
        """
        res = dict()
        if self.custom:
            attribs = self.custom.replace(' ', '').split('}')[:-1]
            for a in attribs:
                assert len(a.split('{', 1)) == 2
                key, vals = a.split('{', 1)
                vals = vals.split(';')[:-1]
                d = {val.split(':')[0]: val.split(':')[1] for val in vals}
                res[key] = d
        return res

    def to_xml(self, name_element=None):
        """Converts a `Region` object to an XML structure

        :param name_element: name of the object (optional)
        :return: a etree structure
        """
        et = ET.Element(name_element if name_element is not None else '')
        et.set('id', self.id if self.id is not None else '')
        if self.coords:
            coords = ET.SubElement(et, 'Coords')
            coords.set('points', Point.list_point_to_string(self.coords))
        if self.custom:
            et.set('custom', self.custom)
        return et


class GraphicRegion(Region):
    """Region containing simple graphics. Company logos for example should be marked as graphic regions. Reference:
        http://www.ocr-d.de/sites/all/gt_guidelines/pagecontent_xsd_Complex_Type_pc_GraphicRegionType.html

    :ivar id: identifier of the `GraphicRegion`
    :ivar coords: coordinates of the `GraphicRegion`
    """
    tag = 'GraphicRegion'

    def __init__(self, id=None, coords=None, custom=None):
        super(GraphicRegion, self).__init__(id=id, coords=coords, custom=custom)

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return GraphicRegion(**super(GraphicRegion, cls).from_xml(e))

    def to_xml(self, name_element='GraphicRegion'):
        graph_et = super(GraphicRegion, self).to_xml(name_element)

        return graph_et


class TextRegion(Region):
    """Pure text is represented as a text region. This includes drop capitals, but practically ornate text may be
    considered as a graphic.

    :ivar id: identifier of the `TextRegion`
    :ivar coords: coordinates of the `TextRegion`
    :ivar text_equiv: the resulting text of the `Text` contained in the `TextLines`
    :ivar text_lines: a list of `TextLine` objects
    """
    tag = 'TextRegion'

    def __init__(self, id=None, coords=None, text_lines=None, text_equiv='', custom=None):
        super(TextRegion, self).__init__(id=id, coords=coords)
        self.text_equiv = text_equiv if text_equiv is not None else ''
        self.text_lines = text_lines if text_lines is not None else []
        self.custom = custom

    def sort_text_lines(self, top_to_bottom=True):
        """
        Sorts ``TextLine``s from top to bottom according to their mean y coordinate (centroid)
        :param top_to_bottom: order lines from top to bottom of image, default=True
        """
        if top_to_bottom:
            self.text_lines.sort(key=lambda line: np.mean([c.y for c in line.coords]))
        else:
            raise NotImplementedError

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return TextRegion(
            text_lines=[TextLine.from_xml(tl) for tl in e.findall('p:TextLine', _ns)],
            text_equiv=_get_text_equiv(e),
            **super(TextRegion, cls).from_xml(e)
        )

    def to_xml(self, name_element='TextRegion'):
        text_et = super(TextRegion, self).to_xml(name_element=name_element)
        for tl in self.text_lines:
            text_et.append(tl.to_xml())
        text_equiv = ET.SubElement(text_et, 'TextEquiv')
        text_unicode = ET.SubElement(text_equiv, 'Unicode')
        if not not self.text_equiv:
            text_unicode.text = self.text_equiv
        return text_et


class TextLine(Region):
    """Region corresponding to a text line.

    :ivar id: identifier of the `TextLine`
    :ivar coords: coordinates of the `Texline` line
    :ivar baseline: coordinates of the `Texline` baseline
    :ivar text: `Text` class containing the transcription of the `TextLine`
    :ivar article_id: identifier of the article the instance belongs to
    """
    tag = 'TextLine'

    def __init__(self, id=None, coords=None, baseline=None, text=None, article_id=None, custom=None):
        super(TextLine, self).__init__(id=id if id is not None else str(uuid4()), coords=coords)
        self.baseline = baseline if baseline is not None else []
        self.text = text if text is not None else Text()
        self.article_id = article_id if article_id is not None else ''
        self.custom = custom

    @classmethod
    def from_xml(cls, etree_element):
        cls.check_tag(etree_element.tag)
        custom_tag = etree_element.attrib.get('custom')
        if custom_tag and "structure" in custom_tag:
            structure = custom_tag[custom_tag.find('structure'):].split('}')[0] + '}'
            article_id = structure[structure.find('id:') + 3:].split(';')[0]
        else:
            article_id = None
        return TextLine(
            baseline=Point.list_from_xml(etree_element.find('p:Baseline', _ns)),
            text=Text(text_equiv=_get_text_equiv(etree_element)),
            article_id=article_id,
            **super(TextLine, cls).from_xml(etree_element)
        )

    def to_xml(self, name_element='TextLine'):
        line_et = super(TextLine, self).to_xml(name_element=name_element)
        if not not self.baseline:
            line_baseline = ET.SubElement(line_et, 'Baseline')
            line_baseline.set('points', Point.list_point_to_string(self.baseline))
        line_text_equiv = ET.SubElement(line_et, 'TextEquiv')
        text_unicode = ET.SubElement(line_text_equiv, 'Unicode')
        if not not self.text.text_equiv:
            text_unicode.text = self.text.text_equiv
        return line_et


class TableRegion(Region):
    """
    Tabular data in any form.
    Tabular data is represented with a table region. Rows and columns may or may not have separator lines;
    these lines are not separator regions.

    :ivar id: identifier of the `TableRegion`
    :ivar coords: coordinates of the `TableRegion`
    :ivar rows: number of rows in the table
    :ivar columns: number of columns in the table
    :ivar embedded_text: if text is embedded in the table
    """

    tag = 'TableRegion'

    def __init__(self, id=None, coords=None, rows=None, columns=None, embedded_text=None, custom=None):
        super(TableRegion, self).__init__(id=id, coords=coords)
        self.rows = rows
        self.columns = columns
        self.embedded_text = embedded_text
        self.custom = custom

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return TableRegion(
            rows=e.attrib.get('rows'),
            columns=e.attrib.get('columns'),
            embedded_text=e.attrib.get('embText'),
            **super(TableRegion, cls).from_xml(e)
        )

    def to_xml(self, name_element='TableRegion'):
        table_et = super(TableRegion, self).to_xml(name_element)
        table_et.set('rows', self.rows if self.rows is not None else 0)
        table_et.set('columns', self.columns if self.columns is not None else 0)
        table_et.set('embText', self.embedded_text if self.embedded_text is not None else False)
        return table_et


class SeparatorRegion(Region):
    """
    Lines separating columns or paragraphs.
    Separators are lines that lie between columns and paragraphs and can be used to logically separate
    different articles from each other.

    :ivar id: identifier of the `SeparatorRegion`
    :ivar coords: coordinates of the `SeparatorRegion`
    """

    tag = 'SeparatorRegion'

    def __init__(self, id, coords=None, custom=None):
        super(SeparatorRegion, self).__init__(id=id, coords=coords, custom=custom)

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return SeparatorRegion(**super(SeparatorRegion, cls).from_xml(e))

    def to_xml(self, name_element='SeparatorRegion'):
        separator_et = super(SeparatorRegion, self).to_xml(name_element)
        return separator_et


class Border(BaseElement):
    """
    Region containing the page.
    It is the border of the actual page of the document (if the scanned image contains parts not belonging to the page).

    :ivar coords: coordinates of the `Border` region
    """

    tag = 'Border'

    def __init__(self, coords=None, id=None):
        self.coords = coords if coords is not None else []

    @classmethod
    def from_xml(cls, e):
        if e is None:
            return None
        cls.check_tag(e.tag)
        return Border(
            coords=Point.list_from_xml(e.find('p:Coords', _ns))
        )

    def to_xml(self):
        border_et = ET.Element('Border')
        if not not self.coords:
            border_coords = ET.SubElement(border_et, 'Coords')
            border_coords.set('points', Point.list_point_to_string(self.coords))
        return border_et


class Metadata(BaseElement):
    """Metadata information.

    :ivar creator: name of the process of person that created the exported file
    :ivar created: time of creation of the file
    :ivar last_change: time of last modification of the file
    :ivar comments: comments on the process
    """
    tag = 'Metadata'

    def __init__(self, creator=None, created=None, last_change=None, comments=None):
        self.creator = creator
        self.created = created
        self.last_change = last_change
        self.comments = comments if comments is not None else ''

    @classmethod
    def from_xml(cls, e):
        if e is None:
            return None
        cls.check_tag(e.tag)
        creator_et = e.find('p:Creator', _ns)
        created_et = e.find('p:Created', _ns)
        last_change_et = e.find('p:LastChange', _ns)
        comments_et = e.find('p:Comments', _ns)
        return Metadata(creator=creator_et.text if creator_et is not None else None,
                        created=created_et.text if created_et is not None else None,
                        last_change=last_change_et.text if last_change_et is not None else None,
                        comments=comments_et.text if comments_et is not None else None)

    def to_xml(self):
        metadata_et = ET.Element('Metadata')
        creator_et = ET.SubElement(metadata_et, 'Creator')
        creator_et.text = self.creator if self.creator is not None else ''
        created_et = ET.SubElement(metadata_et, 'Created')
        created_et.text = self.created if self.created is not None else ''
        last_change_et = ET.SubElement(metadata_et, 'LastChange')
        last_change_et.text = self.last_change if self.last_change is not None else ''
        comments_et = ET.SubElement(metadata_et, 'Comments')
        comments_et.text = self.comments if self.comments is not None else ''

        return metadata_et


class Page(BaseElement):
    """
    Class following PAGE-XML object.
    This class is used to represent the information of the processed image. It is possible to export this info as
    PAGE-XML or JSON format.

    :ivar image_filename: filename of the image
    :ivar image_width: width of the original image
    :ivar image_height: height of the original image
    :ivar text_regions: list of `TextRegion`
    :ivar graphic_regions: list of `GraphicRegion`
    :ivar page_border: `Border` of the page
    :ivar separator_regions: list of `SeparatorRegion`
    :ivar table_regions: list of `TableRegion`
    :ivar metadata: `Metadata` of the image and process
    """
    tag = 'Page'

    def __init__(self, **kwargs):
        self.image_filename = kwargs.get('image_filename')
        self.image_width = _try_to_int(kwargs.get('image_width'))  # Needs to be int type (not np.int32/64)
        self.image_height = _try_to_int(kwargs.get('image_height'))
        self.text_regions = kwargs.get('text_regions', [])
        self.graphic_regions = kwargs.get('graphic_regions', [])
        self.page_border = kwargs.get('page_border', Border())
        self.separator_regions = kwargs.get('separator_regions', [])
        self.table_regions = kwargs.get('table_regions', [])
        self.metadata = kwargs.get('metadata', Metadata())

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return Page(
            image_filename=e.attrib.get('imageFilename'),
            image_width=e.attrib.get('imageWidth'),
            image_height=e.attrib.get('imageHeight'),
            text_regions=[TextRegion.from_xml(tr) for tr in e.findall('p:TextRegion', _ns)],
            graphic_regions=[GraphicRegion.from_xml(tr) for tr in e.findall('p:GraphicRegion', _ns)],
            page_border=Border.from_xml(e.find('p:Border', _ns)),
            separator_regions=[SeparatorRegion.from_xml(sep) for sep in e.findall('p:SeparatorRegion', _ns)],
            table_regions=[TableRegion.from_xml(tr) for tr in e.findall('p:TableRegion', _ns)]
        )

    def to_xml(self):
        page_et = ET.Element('Page')
        if self.image_filename:
            page_et.set('imageFilename', self.image_filename)
        if self.image_width:
            page_et.set('imageWidth', str(self.image_width))
        if self.image_height:
            page_et.set('imageHeight', str(self.image_height))
        for tr in self.text_regions:
            page_et.append(tr.to_xml())
        for gr in self.graphic_regions:
            page_et.append(gr.to_xml())
        if self.page_border:
            page_et.append(self.page_border.to_xml())
        for sep in self.separator_regions:
            page_et.append(sep.to_xml())
        for tr in self.table_regions:
            page_et.append(tr.to_xml())
        return page_et

    def get_baseline_text_dict(self, as_poly=True):
        text_regions = self.text_regions

        # dictionary with article_ids as keys and a list of tuple (text, baseline) as values
        article_dict = dict()

        for tr in text_regions:
            for tl in tr.text_lines:
                # tl.baseline is a list of Point elements
                if as_poly:
                    baseline = Point.list_point_to_polygon(tl.baseline)
                else:
                    baseline = Point.point_to_list(tl.baseline)
                text = tl.text.text_equiv.encode('utf8') if tl.text.text_equiv else ''

                if tl.article_id:
                    if tl.article_id in article_dict:
                        article_dict[tl.article_id].append((text, baseline))
                    else:
                        article_dict[tl.article_id] = [(text, baseline)]
                else:
                    if 'other' in article_dict:
                        article_dict['other'].append((text, baseline))
                    else:
                        article_dict['other'] = [(text, baseline)]

        return article_dict

    def write_to_file(self, filename, creator_name='ArticleSeparation', comments=''):
        """
        Export Page object to json or page-xml format. Will assume the format based on the extension of the filename,
        if there is no extension will export as an xml file.

        :param filename: filename of the file to be exported
        :param creator_name: name of the creator (process or person) creating the file
        :param comments: optionnal comment to add to the metadata of the file.
        """

        def _write_xml():
            root = ET.Element('PcGts')
            root.set('xmlns', _ns['p'])

            root.append(self.metadata.to_xml())
            root.append(self.to_xml())
            for k, v in _attribs.items():
                root.attrib[k] = v
            ET.ElementTree(element=root).write(filename)

        # Updating metadata
        self.metadata.creator = creator_name
        self.metadata.comments += comments
        generated_on = str(datetime.datetime.now().isoformat())
        if self.metadata.created is None:
            self.metadata.created = generated_on
        else:
            self.metadata.last_change = generated_on

        # Depending on the extension write xml or json file
        extension = os.path.splitext(filename)[1]

        if extension == '.xml':
            _write_xml()
        else:
            print('WARN : No extension for export, XML export by default')
            _write_xml()


def parse_file(filename):
    """
    Parses the files to create the corresponding ``Page`` object. The files can be a .xml or a .json.

    :param filename: file to parse (either json of page xml)
    :return: Page object containing all the parsed elements
    """
    extension = os.path.splitext(filename)[1]

    if extension == '.xml':
        xml_page = ET.parse(filename)
        page_elements = xml_page.find('p:Page', _ns)
        metadata_et = xml_page.find('p:Metadata', _ns)
        page = Page.from_xml(page_elements)
        page.metadata = Metadata.from_xml(metadata_et)
        return page
    else:
        raise NotImplementedError


# def get_baseline_text_dict(filename):
#     page = parse_file(filename)
#     text_regions = page.text_regions
#
#     # dictionary with article_ids as keys and a list of tuple (text, baseline) as values
#     article_dict = dict()
#
#     for tr in text_regions:
#         for tl in tr.text_lines:
#             # tl.baseline is a list of Point elements
#             # baseline = Point.point_to_list(tl.baseline)
#             baseline = Point.list_point_to_polygon(tl.baseline)
#             # baseline = np.squeeze(Point.list_to_cv2poly(tl.baseline))
#             text = tl.text.text_equiv.encode('utf8')
#
#             if tl.article_id:
#                 if tl.article_id in article_dict:
#                     # article_dict[tl.article_id] = np.concatenate((baselines[tl.article_id], [baseline]))
#                     article_dict[tl.article_id].append((text, baseline))
#                 else:
#                     # baselines[tl.article_id] = np.array([baseline])
#                     article_dict[tl.article_id] = [(text, baseline)]
#             else:
#                 if 'other' in article_dict:
#                     # baselines['other'] = np.concatenate((baselines['other'], [baseline]))
#                     article_dict['other'].append((text, baseline))
#                 else:
#                     # baselines['other'] = np.array([baseline])
#                     article_dict['other'] = [(text, baseline)]
#
#     return article_dict


if __name__ == '__main__':
    # The PAGEXML will be given as follows:
    #
    # <TextRegion id="Page1_Block2"custom="readingOrder {index:0;}">
    #   <Coords points="41,215 1255,215 1255,2870 41,2870"/>
    #       <TextLine id="tl_1" custom="readingOrder {index:0;} structure {id:a1; type:article;}">
    #           <Coords points = "49,223 1231,223 1231,281 49,281"/>
    #
    # path_to_pagexml = './test/resources/page_test.xml'
    prefix = '/home/max/data/as/newseye_as_test_data/files_hy/'
    # path_to_pagexml = prefix + '19000715_1-0001.xml'  # 19000715_1-0002.xml & 19000715_1-0003.xml
    path_to_pagexml = prefix + '19000715_1-0001.xml'
    page = parse_file(path_to_pagexml)
    article_dict = page.get_baseline_text_dict()
    print(article_dict)
    for a, t_list in article_dict.iteritems():
        print("=====================\nArticle {}".format(a))
        for t in t_list:
            print("\t{}".format(t[0]))
            # print("\t{}".format(t[1]))
            print("\t{} - {}".format(t[1].x_points, t[1].y_points))

    # page = parse_file(path_to_pagexml)
    # for tr in page.text_regions:
    #     print(tr.parse_custom())
    #     for tl in tr.text_lines:
    #         print("\t{}".format(tl.parse_custom()))
    #     print("================")
