from io import open
from geometry import Polygon


def load_text_file(filename):
    """Load text file ``filename`` and return the lines as """
    res = []
    with open(filename, 'r') as f:
        for line in f:
            res.append(line.strip())
        return res


def parse_string(string_polygon):
    """Parse the polygon represented by the string ``string_polygon`` and return a ``Polygon`` object.

    :param string_polygon: coordinates of a polygon given in string format: x1,y1;x2,y2;...;xn,yn.
    :type string_polygon: str
    :return: Polygon object with the coordinates given in string_polygon.
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


