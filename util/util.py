from io import open
from geometry import Polygon


def load_text_file(filename):
    """Load text file ``filename`` and return the (stripped) lines as list entries.

    :param filename: path to the file to be loaded
    :type filename: str
    :return: list of strings consisting of the (stripped) lines from filename
    """

    res = []
    with open(filename, 'r') as f:
        for line in f:
            if not line.isspace():
                res.append(line.strip())
        return res


def parse_string(string_polygon):
    """Parse the polygon represented by the string ``string_polygon`` and return a ``Polygon`` object.

    :param string_polygon: coordinates of a polygon given in string format: x1,y1;x2,y2;...;xn,yn
    :type string_polygon: str
    :return: Polygon object with the coordinates given in string_polygon
    """

    polygon = Polygon()
    points = string_polygon.split(";")
    if len(points) < 2:
        raise Exception("Wrong polygon string format.")
    for p in points:
        coord = p.split(",")
        if len(coord) < 2:
            raise Exception("Wrong polygon string format.")
        coord_x = int(coord[0])
        coord_y = int(coord[1])
        polygon.add_point(coord_x, coord_y)
    return polygon


def poly_to_string(polygon):
    """Inverse method of ``parse_string``, taking a polygon as input and outputs a string holding the x,y coordinates
    of the points present in the polygon separated by semicolons ";".

    :param polygon: input polygon to be parsed
    :type polygon: Polygon
    :return: a string holding the x,y coordinates of the polygon in format: x1,y1;x2,y2;...;xn,yn
    """

    res = ""
    for x, y in zip(polygon.x_points, polygon.y_points):
        if len(res) != 0:
            res += ";"
        res += str(x) + "," + str(y)
    return res


# get_polys_from_page_file not necessary since we're only handling strings which are produced from Java routines

def get_polys_from_file(poly_file_name):
    """Load polygons from a text file ``poly_file_name`` and save them as ``Polygon`` objects in a list.

    :param poly_file_name: path to the txt file holding the polygons (one polygon per line)
    :type poly_file_name: str
    :return: a tuple containing the list of polygons and a boolean value representing if the polygons are loaded with
    errors
    """

    # TODO: Bool return value necessary? -> Just check if returned list is None (then you know if it was skipped or not)
    poly_strings = load_text_file(poly_file_name)
    if len(poly_strings) == 0:
        return None, False

    res = []
    for poly_string in poly_strings:
        try:
            poly = parse_string(str(poly_string))
            res.append(poly)
        except ValueError:
            return None, True
    return res, False


# TODO add documentation for norm_des_dist
def norm_des_dist(poly_list, des_dist):
    """

    :param poly_list: list of polygons
    :param des_dist:
    :type poly_list: list
    :type des_dist: int
    :return: list of polygons
    """

    res = []
    for poly in poly_list:
        bb = poly.get_bounding_box()
        if bb.width > 100000 or bb.height > 100000:
            poly = Polygon([0], [0], 1)

        poly_blow_up = blow_up(poly)
        poly_thin_out = thin_out(poly_blow_up, des_dist)

        # to calculate the bounding box "get_bounding_box" must be executed
        poly_thin_out.get_bounding_box()
        res.append(poly_thin_out)

    return res
