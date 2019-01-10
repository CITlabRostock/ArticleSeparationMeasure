# -*- coding: utf-8 -*-

from xml.etree import ElementTree as ET
import numpy as np
import datetime
import cv2
import os
import json
from uuid import uuid4
from shapely.geometry import Polygon
from abc import ABCMeta
from io import open

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
    """Point (x,y) class.

    :ivar y: vertical coordinate
    :ivar x: horizontal coordinate

    """

    def __init__(self, y, x):
        self.y = y
        self.x = x

    @classmethod
    def list_from_xml(cls, etree_elem):
        """Converts a PAGEXML-formatted set of coordinates to a list of `Point`

        :param etree_elem: etree XML element containing a set of coordinates
        :return: a list of coordinates as `Point`
        """
        if etree_elem is None:
            # print('warning, trying to construct list of points from None, defaulting to []')
            return []
        t = etree_elem.attrib['points']
        result = []
        for p in t.split(' '):
            values = p.split(',')
            assert len(values) == 2
            x, y = int(float(values[0])), int(float(values[1]))
            result.append(Point(y, x))
        return result

    @classmethod
    def list_to_cv2poly(cls, list_points):
        """Converts a list of `Point` to opencv format set of coordinates

        :param list_points: set of coordinates
        :return: opencv-formatted set of points, shape (N,1,2)
        """
        return np.array([(p.x, p.y) for p in list_points], dtype=np.int32).reshape([-1, 1, 2])

    @classmethod
    def cv2_to_point_list(cls, cv2_array):
        """Converts an opencv-formatted set of coordinates to a list of `Point`

        :param cv2_array: opencv-formatted set of coordinates, shape (N,1,2)
        :return: list of `Point`
        """
        return [Point(p[0, 1], p[0, 0]) for p in cv2_array]

    @classmethod
    def list_point_to_string(cls, list_points):
        """Converts a list of `Point` to a string 'x,y'

        :param list_points: list of coordinates with `Point` format
        :return: a string with the coordinates
        """
        return ' '.join(['{},{}'.format(p.x, p.y) for p in list_points])

    @classmethod
    def array_to_list(cls, array):
        """Converts an `np.array` to a list of coordinates

        :param array: an array of coordinates. Must be of shape (N, 2)
        :return: list of coordinates, shape (N,2)
        """
        return [list(pt) for pt in array]

    @classmethod
    def list_to_point(cls, list_coords):
        """Converts a list of coordinates to a list of `Point`

        :param list_coords: list of coordinates, shape (N, 2)
        :return: list of Points
        """
        return [cls(coord[1], coord[0]) for coord in list_coords if list_coords]

    @classmethod
    def point_to_list(cls, points):
        """Converts a list of `Point` to a list of coordinates

        :param points: list of Points
        :return: list of shape (N,2)
        """
        return [[pt.x, pt.y] for pt in points]

    def to_dict(self):
        # TODO: this does not return a dictionary...
        return [int(self.x), int(self.y)]


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

    def to_dict(self):
        return vars(self)


class BaseElement:
    """
    Base page element class. (Abstract)
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
    This is the superclass for all the extracted regions

    :ivar id: identifier of the `Region`
    :ivar coords: coordinates of the `Region`
    """
    tag = 'Region'

    def __init__(self, id=None, coords=None):
        self.coords = coords if coords is not None else []
        self.id = id

    @classmethod
    def from_xml(cls, etree_element):
        """Creates a dictionary from a XML structure in order to create the inherited objects

        :param etree_element: a xml etree
        :return: a dictionary with keys 'id' and 'coords'
        """
        return {'id': etree_element.attrib.get('id'),
                'coords': Point.list_from_xml(etree_element.find('p:Coords', _ns))}

    def to_xml(self, name_element=None):
        """Converts a `Region` object to a xml structure

        :param name_element: name of the object (optional)
        :return: a etree structure
        """
        et = ET.Element(name_element if name_element is not None else '')
        et.set('id', self.id if self.id is not None else '')
        if not not self.coords:
            coords = ET.SubElement(et, 'Coords')
            coords.set('points', Point.list_point_to_string(self.coords))
        return et

    def to_dict(self, non_serializable_keys=None):
        """Converts a `Region` object to a dictionary.

        :param non_serializable_keys: list of keys that can't be directly serialized and that need some
                                      internal serialization
        :return: a dictionary with the atributes of the object serialized
        """
        if non_serializable_keys is None:
            non_serializable_keys = list()
        if 'coords' in vars(self).keys() and 'coords' not in non_serializable_keys:
            non_serializable_keys += ['coords']
        return json_serialize(vars(self), non_serializable_keys=non_serializable_keys)

    @classmethod
    def from_dict(cls, dictionary):
        """From a seralized dictionary creates a dictionary of the atributes (non serialized)

        :param dictionary: serialized dictionary
        :return: non serialized dictionary
        """
        return {'id': dictionary.get('id'),
                'coords': Point.list_to_point(dictionary.get('coords'))
                }


class TextLine(Region):
    """Region corresponding to a text line.

    :ivar id: identifier of the `TextLine`
    :ivar coords: coordinates of the `Texline` line
    :ivar baseline: coordinates of the `Texline` baseline
    :ivar text: `Text` class containing the transcription of the `TextLine`
    :ivar article_id: identifier of the article the instance belongs to
    :ivar line_group_id: identifier of the line group the instance belongs to
    :ivar column_group_id: identifier of the column group the instance belongs to

    """
    tag = 'TextLine'

    def __init__(self, id=None, coords=None, baseline=None, text=None, article_id=None,
                 line_group_id=None, column_group_id=None):
        super(TextLine, self).__init__(id=id if id is not None else str(uuid4()), coords=coords)
        self.baseline = baseline if baseline is not None else []
        self.text = text if text is not None else Text()
        self.article_id = article_id if article_id is not None else ''
        self.line_group_id = line_group_id if line_group_id is not None else ''
        self.column_group_id = column_group_id if column_group_id is not None else ''

    @classmethod
    def from_xml(cls, etree_element):
        cls.check_tag(etree_element.tag)
        custom_tag = etree_element.attrib.get('custom')
        if "structure" in custom_tag:
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

    @classmethod
    def from_array(cls, cv2_coords=None, baseline_coords=None,  # cv2_coords shape [N, 1, 2]
                   text_equiv=None, id=None):
        return TextLine(
            id=id,
            coords=Point.cv2_to_point_list(cv2_coords) if cv2_coords is not None else [],
            baseline=Point.cv2_to_point_list(baseline_coords) if baseline_coords is not None else [],
            text=Text(text_equiv=text_equiv)
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

    def scale_baseline_points(self, ratio):
        """Scales the points of the baseline by a factor `ratio`.

        :param ratio: factor to rescale the baseline coordinates
        """
        scaled_points = list()
        for pt in self.baseline:
            scaled_points.append(Point(int(pt.y * ratio[0]), int(pt.x * ratio[1])))

        self.baseline = scaled_points

    def to_dict(self, non_serializable_keys=None):
        if non_serializable_keys is None:
            non_serializable_keys = list()
        return super(TextLine, self).to_dict(non_serializable_keys=['text', 'baseline'])

    @classmethod
    def from_dict(cls, dictionary):
        return cls(baseline=Point.list_to_point(dictionary.get('baseline')),
                   text=Text(**dictionary.get('text', dict())),
                   line_group_id=dictionary.get('line_group_id'),
                   column_group_id=dictionary.get('column_group_id'),
                   **super(TextLine, cls).from_dict(dictionary)
                   )


class GraphicRegion(Region):
    """Region containing simple graphics. Company logos for example should be marked as graphic regions.

    :ivar id: identifier of the `GraphicRegion`
    :ivar coords: coordinates of the `GraphicRegion`
    """
    tag = 'GraphicRegion'

    def __init__(self, id=None, coords=None, ):
        super(GraphicRegion, self).__init__(id=id, coords=coords)

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return GraphicRegion(**super(GraphicRegion, cls).from_xml(e))

    def to_xml(self, name_element='GraphicRegion'):
        graph_et = super(GraphicRegion, self).to_xml(name_element)

        return graph_et

    @classmethod
    def from_dict(cls, dictionary):
        return cls(**super(GraphicRegion, cls).from_dict(dictionary))


class TextRegion(Region):
    """Region containing text lines. It can represent a paragraph or a page for instance.

    :ivar id: identifier of the `TextRegion`
    :ivar coords: coordinates of the `TextRegion`
    :ivar text_equiv: the resulting text of the `Text` contained in the `TextLines`
    :ivar text_lines: a list of `TextLine` objects
    """
    tag = 'TextRegion'

    def __init__(self, id=None, coords=None, text_lines=None, text_equiv=''):
        super(TextRegion, self).__init__(id=id, coords=coords)
        self.text_equiv = text_equiv if text_equiv is not None else ''
        self.text_lines = text_lines if text_lines is not None else []

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

    def to_dict(self, non_serializable_keys=None):
        if non_serializable_keys is None:
            non_serializable_keys = list()
        return super(TextRegion, self).to_dict(non_serializable_keys=['text_lines'])

    @classmethod
    def from_dict(cls, dictionary):
        return cls(text_lines=[TextLine.from_dict(tl) for tl in dictionary.get('text_lines', list())],
                   text_equiv=dictionary.get('text_equiv'),
                   **super(TextRegion, cls).from_dict(dictionary)
                   )


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

    def __init__(self, id=None, coords=None, rows=None, columns=None, embedded_text=None):
        super(TableRegion, self).__init__(id=id, coords=coords)
        self.rows = rows
        self.columns = columns
        self.embedded_text = embedded_text

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

    @classmethod
    def from_dict(cls, dictionary):
        return cls(rows=dictionary.get('rows'),
                   columns=dictionary.get('columns'),
                   embedded_text=dictionary.get('embedded_text'),
                   **super(TableRegion, cls).from_dict(dictionary))


class SeparatorRegion(Region):
    """
    Lines separating columns or paragraphs.
    Separators are lines that lie between columns and paragraphs and can be used to logically separate
    different articles from each other.

    :ivar id: identifier of the `SeparatorRegion`
    :ivar coords: coordinates of the `SeparatorRegion`
    """

    tag = 'SeparatorRegion'

    def __init__(self, id, coords=None):
        super(SeparatorRegion, self).__init__(id=id, coords=coords)

    @classmethod
    def from_xml(cls, e):
        cls.check_tag(e.tag)
        return SeparatorRegion(**super(SeparatorRegion, cls).from_xml(e))

    def to_xml(self, name_element='SeparatorRegion'):
        separator_et = super(SeparatorRegion, self).to_xml(name_element)
        return separator_et

    @classmethod
    def from_dict(cls, dictionary):
        return cls(**super(SeparatorRegion, cls).from_dict(dictionary))


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

    @classmethod
    def from_dict(cls, dictionary):
        return cls(coords=Point.list_to_point(dictionary.get('coords')))

    def to_dict(self, non_serializable_keys=None):
        if non_serializable_keys is None:
            non_serializable_keys = list()
        if 'coords' in vars(self).keys() and 'coords' not in non_serializable_keys:
            non_serializable_keys += ['coords']
        return json_serialize(vars(self), non_serializable_keys=non_serializable_keys)


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

    def to_dict(self):
        return vars(self)

    @classmethod
    def from_dict(cls, dictionary):
        return cls(created=dictionary.get('created'),
                   creator=dictionary.get('creator'),
                   last_change=dictionary.get('last_change'),
                   comments=dictionary.get('comments')
                   )


class GroupSegment(Region):
    """
    Set of regions that make a bigger region (group).
    `GroupSegment` is a region containing several `TextLine` and that form a bigger region.
    It is used mainly to make line / column regions.
    Only for JSON export (no PAGE XML correspondence).

    :ivar id: identifier of the `GroupSegment`
    :ivar coords: coordinates of the `GroupSegment`
    :ivar segment_ids: list of the regions ids belonging to the group

    """

    def __init__(self, id=None, coords=None, segment_ids=None):
        super(GroupSegment, self).__init__(id=id, coords=coords)
        self.segment_ids = segment_ids if segment_ids is not None else []

    @classmethod
    def from_dict(cls, dictionary):
        return cls(segment_ids=dictionary.get('segment_ids'),
                   **super(GroupSegment, cls).from_dict(dictionary))


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
    :ivar line_groups: list of `GroupSegment` forming lines
    :ivar column_groups: list of `GroupSegment` forming columns

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
        self.line_groups = kwargs.get('line_groups', [])
        self.column_groups = kwargs.get('column_groups', [])

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

    @classmethod
    def from_dict(cls, dictionary):
        return cls(image_filename=dictionary.get('image_filename'),
                   image_height=dictionary.get('image_height'),
                   image_width=dictionary.get('image_width'),
                   metadata=Metadata.from_dict(dictionary.get('metadata')),
                   text_regions=[TextRegion.from_dict(tr) for tr in dictionary.get('text_regions', list())],
                   page_border=Border.from_dict(dictionary.get('page_border', dict())),
                   separator_regions=[SeparatorRegion.from_dict(sep) for sep in
                                      dictionary.get('separator_regions', list())],
                   graphic_regions=[GraphicRegion.from_dict(gr) for gr in dictionary.get('graphic_regions', list())],
                   table_regions=[TableRegion.from_dict(tr) for tr in dictionary.get('table_regions', list())],
                   line_groups=[GroupSegment.from_dict(lr) for lr in dictionary.get('line_groups', list())],
                   column_groups=[GroupSegment.from_dict(cr) for cr in dictionary.get('column_groups', list())]
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
        # if self.metadata:
        #     page_et.append(self.metadata.to_xml())
        return page_et

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

        def _write_json():
            self_dict = vars(self)

            # json_dict = dict()
            serializable_keys = ['image_filename', 'image_height', 'image_width']
            json_dict = json_serialize(self_dict, [k for k in self_dict.keys() if k not in serializable_keys])

            with open(filename, 'w', encoding='utf8') as file:
                json.dump(json_dict, file, indent=4, sort_keys=True, allow_nan=False)

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
        elif extension == '.json':
            _write_json()
        else:
            print('WARN : No extension for export, XML export by default')
            _write_xml()

    def draw_baselines(self, img_canvas, color=(255, 0, 0), thickness=2, endpoint_radius=4, autoscale=True):
        """
        Given an image, draws the TextLines.baselines.

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace.
        :param color: (R, G, B) value color
        :param thickness: the thickness of the line
        :param endpoint_radius: the radius of the endpoints of line s(first and last coordinates of line)
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        text_lines = [tl for tr in self.text_regions for tl in tr.text_lines]
        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        tl_coords = [(Point.list_to_cv2poly(tl.baseline) * ratio).astype(np.int32) for tl in text_lines
                     if len(tl.baseline) > 0]
        cv2.polylines(img_canvas, tl_coords, False, color, thickness=thickness)
        for coords in tl_coords:
            cv2.circle(img_canvas, (coords[0, 0, 0], coords[0, 0, 1]),
                       radius=endpoint_radius, color=color, thickness=-1)
            cv2.circle(img_canvas, (coords[-1, 0, 0], coords[-1, 0, 1]),
                       radius=endpoint_radius, color=color, thickness=-1)

    def draw_lines(self, img_canvas, color=(255, 0, 0), thickness=2, fill=True, autoscale=True):
        """
        Given an image, draws the polygons containing text lines, i.e TextLines.coords

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace.
        :param color: (R, G, B) value color
        :param thickness: the thickness of the line
        :param fill: if True fills the polygon
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        text_lines = [tl for tr in self.text_regions for tl in tr.text_lines]
        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        tl_coords = [(Point.list_to_cv2poly(tl.coords) * ratio).astype(np.int32) for tl in text_lines
                     if len(tl.coords) > 0]

        if fill:
            for tl in tl_coords:  # For loop to avoid black regions when lines overlap
                cv2.fillPoly(img_canvas, [tl], color)
        else:
            for tl in tl_coords:  # For loop to avoid black regions when lines overlap
                cv2.polylines(img_canvas, [tl], False, color, thickness=thickness)

    def draw_text_regions(self, img_canvas, color=(255, 0, 0), fill=True, thickness=3, autoscale=True):
        """
        Given an image, draws the TextRegions, either fills it (fill=True) or draws the contours (fill=False)

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace.
        :param color: (R, G, B) value color
        :param fill: either to fill the region (True) of only draw the external contours (False)
        :param thickness: in case fill=True the thickness of the line
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        tr_coords = [(Point.list_to_cv2poly(tr.coords) * ratio).astype(np.int32) for tr in self.text_regions
                     if len(tr.coords) > 0]
        if fill:
            cv2.fillPoly(img_canvas, tr_coords, color)
        else:
            cv2.polylines(img_canvas, tr_coords, True, color, thickness=thickness)

    def draw_page_border(self, img_canvas, color=(255, 0, 0), fill=True, thickness=5, autoscale=True):
        """
        Given an image, draws the page border, either fills it (fill=True) or draws the contours (fill=False)

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace.
        :param color: (R, G, B) value color
        :param fill: either to fill the region (True) of only draw the external contours (False)
        :param thickness: in case fill=True the thickness of the line
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        border_coords = (Point.list_to_cv2poly(self.page_border.coords) * ratio).astype(np.int32) \
            if len(self.page_border.coords) > 0 else []
        if fill:
            cv2.fillPoly(img_canvas, [border_coords], color)
        else:
            cv2.polylines(img_canvas, [border_coords], True, color, thickness=thickness)

    def draw_separator_lines(self, img_canvas, color=(0, 255, 0), thickness=3, filter_by_id='', autoscale=True):
        """
        Given an image, draws the SeparatorRegion.

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace.
        :param color: (R, G, B) value color
        :param thickness: thickness of the line
        :param filter_by_id: string to filter the lines by id. For example vertical/horizontal lines can be filtered
                             if 'vertical' or 'horizontal' is mentioned in the id.
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        sep_coords = [(Point.list_to_cv2poly(sep.coords) * ratio).astype(np.int32) for sep in self.separator_regions
                      if len(sep.coords) > 0 and filter_by_id in sep.id]
        cv2.polylines(img_canvas, sep_coords, True, color, thickness=thickness)

    def draw_graphic_regions(self, img_canvas, color=(255, 0, 0), fill=True, thickness=3, autoscale=True):
        """
        Given an image, draws the GraphicRegions, either fills it (fill=True) or draws the contours (fill=False)

        :param img_canvas: 3 channel image in which the region will be drawn.  The image is modified inplace.
        :param color: (R, G, B) value color
        :param fill: either to fill the region (True) of only draw the external contours (False)
        :param thickness: in case fill=True the thickness of the line
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        gr_coords = [(Point.list_to_cv2poly(gr.coords) * ratio).astype(np.int32) for gr in self.graphic_regions
                     if len(gr.coords) > 0]
        if fill:
            cv2.fillPoly(img_canvas, gr_coords, color)
        else:
            cv2.polylines(img_canvas, gr_coords, True, color, thickness=thickness)

    def draw_text(self, img_canvas, color=(255, 0, 0), thickness=5, font=cv2.FONT_HERSHEY_SIMPLEX,
                  font_scale=1.0, autoscale=True):
        """
        Writes the text of the TextLine on the given image.

        :param img_canvas: 3 channel image in which the region will be drawn.  The image is modified inplace
        :param color: (R, G, B) value color
        :param thickness: the thickness of the characters
        :param font: the type of font (``cv2`` constant)
        :param font_scale: the scale of font
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """
        text_lines = [tl for tr in self.text_regions for tl in tr.text_lines]
        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        tl_tuple_coords_text = [((np.array(Point.point_to_list(tl.coords)) * ratio).astype(np.int32),
                                 tl.text.text_equiv) for tl in text_lines if len(tl.coords) > 0]

        for coords, text in tl_tuple_coords_text:
            polyline = Polygon(coords)
            xmin, ymin, xmax, ymax = polyline.bounds
            ymin = np.maximum(0, ymin - 20)

            cv2.putText(img_canvas, text, (int(xmin), int(ymin)), fontFace=font, fontScale=font_scale, color=color,
                        thickness=thickness)

    def draw_line_groups(self, img_canvas, color=(0, 255, 0), fill=False, thickness=5, autoscale=True):
        """
        It will draw line groups. This is only valid when parsing JSON files.

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace.
        :param color: (R, G, B) value color
        :param fill: either to fill the region (True) of only draw the external contours (False)
        :param thickness: in case fill=False the thickness of the line
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """
        assert self.line_groups, "There is no Line group"

        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        lg_coords = [(Point.list_to_cv2poly(lg.coords) * ratio).astype(np.int32) for lg in self.line_groups
                     if len(lg.coords) > 0]
        if fill:
            cv2.fillPoly(img_canvas, lg_coords, color)
        else:
            cv2.polylines(img_canvas, lg_coords, True, color, thickness=thickness)

    def draw_column_groups(self, img_canvas, color=(0, 255, 0), fill=False, thickness=5, autoscale=True):
        """
        It will draw column groups (in case of a table). This is only valid when parsing JSON files.

        :param img_canvas: 3 channel image in which the region will be drawn. The image is modified inplace
        :param color: (R, G, B) value color
        :param fill: either to fill the region (True) of only draw the external contours (False)
        :param thickness: in case fill=False the thickness of the line
        :param autoscale: whether to scale the coordinates to the size of img_canvas. If True,
                          it will use the dimensions provided in Page.image_width and Page.image_height
                          to compute the scaling ratio
        """

        assert self.column_groups, "There is no Line group"

        if autoscale:
            assert self.image_height is not None
            assert self.image_width is not None
            ratio = (img_canvas.shape[0] / self.image_height, img_canvas.shape[1] / self.image_width)
        else:
            ratio = (1, 1)

        cg_coords = [(Point.list_to_cv2poly(cg.coords) * ratio).astype(np.int32) for cg in self.column_groups
                     if len(cg.coords) > 0]
        if fill:
            cv2.fillPoly(img_canvas, cg_coords, color)
        else:
            cv2.polylines(img_canvas, cg_coords, True, color, thickness=thickness)


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
    elif extension == '.json':
        with open(filename, 'r', encoding='utf8') as file:
            json_dict = json.load(file)
        return Page.from_dict(json_dict)
    else:
        raise NotImplementedError


def json_serialize(dict_to_serialize, non_serializable_keys=None):
    """
    Serialize a dictionary in order to export it.

    :param dict_to_serialize: dictionary to serialize
    :param non_serializable_keys: keys that are not directly seriazable sucha as python objects
    :return: the serialized dictionnary
    """

    if non_serializable_keys is None:
        non_serializable_keys = list()
    new_dict = dict_to_serialize.copy()
    for key in non_serializable_keys:
        if isinstance(new_dict[key], list):
            new_dict[key] = [elem.to_dict() for elem in new_dict[key]] if new_dict[key] else []
        elif isinstance(new_dict[key], np.ndarray):
            new_dict[key] = new_dict[key].tolist()
        else:
            new_dict[key] = new_dict[key].to_dict()

    return new_dict


def save_baselines(filename, baselines, ratio=(1, 1), initial_shape=None):
    txt_lines = [TextLine.from_array(baseline_coords=b, id='line_{}'.format(i)) for i, b in enumerate(baselines)]
    for l in txt_lines:
        l.scale_baseline_points(ratio)
    txt_region = TextRegion(text_lines=txt_lines, id='region_0')
    page = Page(text_regions=[txt_region],
                image_height=int(initial_shape[0] * ratio[0]) if initial_shape is not None else None,
                image_width=int(initial_shape[1] * ratio[1]) if initial_shape is not None else None)
    page.write_to_file(filename)


def get_baseline_text_dict(filename):
    page = parse_file(filename)
    text_regions = page.text_regions

    # dictionary with article_ids as keys and a list of tuple (baseline, text) as values
    article_dict = dict()

    for tr in text_regions:
        for tl in tr.text_lines:
            baseline = np.squeeze(Point.list_to_cv2poly(tl.baseline))
            text = tl.text.text_equiv

            if tl.article_id:
                if tl.article_id in article_dict:
                    # article_dict[tl.article_id] = np.concatenate((baselines[tl.article_id], [baseline]))
                    article_dict[tl.article_id].append((text, baseline))
                else:
                    # baselines[tl.article_id] = np.array([baseline])
                    article_dict[tl.article_id] = [(text, baseline)]
            else:
                if 'other' in article_dict:
                    # baselines['other'] = np.concatenate((baselines['other'], [baseline]))
                    article_dict['other'].append((text, baseline))
                else:
                    # baselines['other'] = np.array([baseline])
                    article_dict['other'] = [(text, baseline)]

    return article_dict


if __name__ == '__main__':
    # The PAGEXML will be given as follows:
    #
    # <TextRegion id="Page1_Block2"custom="readingOrder {index:0;}">
    #   <Coords points="41,215 1255,215 1255,2870 41,2870"/>
    #       <TextLine id="tl_1" custom="readingOrder {index:0;} structure {id:a1; type:article;}">
    #           <Coords points = "49,223 1231,223 1231,281 49,281"/>
    #
    path_to_pagexml = './test/resources/page_test.xml'
    article_dict = get_baseline_text_dict(path_to_pagexml)
    print(article_dict)
