from __future__ import division
from __future__ import print_function

import math
import numpy as np
from io import open
from scipy.stats import linregress

from geometry import Polygon, Rectangle


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
    :return: a tuple containing the list of polygons (None if errors occur or no polygons are found) and a boolean value
    representing if the polygons are loaded with errors
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


def blow_up(polygon):
    """Takes a ``polygon`` as input and adds pixels to it according to the following rule. Consider the line between two
    adjacent pixels in the polygon (i.e., if connected via an egde). Then the method adds additional equidistand pixels
    lying on that line (if the value is double, convert to int), dependent on the x- and y-distance of the pixels.

    :param polygon: input polygon that should be blown up
    :type polygon: Polygon
    :return: blown up polygon
    """
    res = Polygon()
    for i in range(1, polygon.n_points, 1):
        x1 = polygon.x_points[i - 1]
        y1 = polygon.y_points[i - 1]
        x2 = polygon.x_points[i]
        y2 = polygon.y_points[i]
        diff_x = abs(x2 - x1)
        diff_y = abs(y2 - y1)
        # if (x1,y1) = (x2, y2)
        if max(diff_x, diff_y) < 1:
            if i == polygon.n_points - 1:
                res.add_point(x2, y2)
            continue

        res.add_point(x1, y1)
        if diff_x >= diff_y:
            for j in range(1, diff_x, 1):
                if x1 < x2:
                    xn = x1 + j
                else:
                    xn = x1 - j
                yn = int(round(y1 + (xn - x1) * (y2 - y1) / (x2 - x1)))
                res.add_point(xn, yn)
        else:
            for j in range(1, diff_y, 1):
                if y1 < y2:
                    yn = y1 + j
                else:
                    yn = y1 - j
                xn = int(round(x1 + (yn - y1) * (x2 - x1) / (y2 - y1)))
                res.add_point(xn, yn)
        if i == polygon.n_points - 1:
            res.add_point(x2, y2)

    return res


def thin_out(polygon, des_dist):
    """Takes a (blown up) ``polygon`` as input and deletes pixels according to the destination distance (``des_dist``),
    s.t. two pixels have a max distance of ``des_dist``. An exception are polygons that are less than or equal to 20
    pixels.

    :param polygon: input (blown up) polygon that should be thinned out
    :param des_dist: max distance of two adjacent pixels
    :type polygon: Polygon
    :type des_dist: int
    :return: thinned out polygon
    """
    res = Polygon()
    if polygon.n_points <= 20:
        return polygon
    dist = polygon.n_points - 1
    min_pts = 20
    des_pts = max(min_pts, int(dist / des_dist) + 1)
    step = dist / (des_pts - 1)
    for i in range(des_pts - 1):
        idx = int(i * step)
        res.add_point(polygon.x_points[idx], polygon.y_points[idx])
    res.add_point(polygon.x_points[-1], polygon.y_points[-1])

    return res


def norm_poly_dists(poly_list, des_dist):
    """For a given list of polygons ``poly_list`` calculate the corresponding normed polygons, s.t. every polygon has
    adjacent pixels with a distance of ~des_dist.

    :param poly_list: list of polygons
    :param des_dist: distance (measured in pixels) of two adjecent pixels in the destination polygon
    :type poly_list: list of Polygon
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

        # to calculate the bounding box "get_bounds" must be executed
        poly_thin_out.get_bounding_box()
        res.append(poly_thin_out)

    return res


def calc_line(x_points, y_points):
    """Calculate the linear regression curve for the points ``x_points`` and ``y_points`` represented by the slope and
    the intersection of with the y-axis.

    :param x_points: array of x-coordinates.
    :param y_points: array of y-coordinates.
    :type x_points: list of int
    :type y_points: list of int
    :return: slope m and intersection with y-axis n
    """
    assert isinstance(x_points, list)
    assert isinstance(y_points, list)
    assert len(x_points) == len(y_points)

    if max([0] + x_points) - min([float("inf")] + x_points) < 2:
        return np.mean(x_points), float("inf")

    try:
        m, n, _, _, _ = linregress(x_points, y_points)
        return m, n
    except ValueError:
        print("Failed linear regression calculation for values\nx = {} and\ny = {}".format(x_points, y_points))


def calc_reg_line_stats(poly):
    """Return the angle of baseline polygon ``poly`` and the intersection of the linear regression line with the y-axis.

    :param poly: input polygon
    :type poly: Polygon
    :return: angle of baseline and intersection of the linear regression line with the y-axis.
    """
    if poly.n_points <= 1:
        return 0.0, 0.0

    n = float("inf")
    if poly.n_points > 2:
        x_max = max(poly.x_points)
        x_min = min(poly.x_points)

        if x_max == x_min:
            m = float("inf")
        else:
            m, n = calc_line(poly.x_points, [-y for y in poly.y_points])
    else:
        x1, x2 = poly.x_points
        y1, y2 = [-y for y in poly.y_points]
        if x1 == x2:
            m = float("inf")
        else:
            m = (y2 - y1) / (x2 - x1)
            n = y2 - m * x2

    if m == float("inf"):
        angle = math.pi / 2
    else:
        angle = math.atan(m)

    # in special cases change the direction of the orientation (-> add pi to angle)
    if -math.pi / 2 < angle <= -math.pi / 4:
        if poly.y_points[0] > poly.y_points[-1]:
            angle += math.pi
    if -math.pi / 4 < angle <= math.pi / 4:
        if poly.x_points[0] > poly.x_points[-1]:
            angle += math.pi
    if math.pi / 4 < angle < math.pi / 2:
        if poly.y_points[0] < poly.y_points[-1]:
            angle += math.pi
    # Make sure that the angle is positive
    if angle < 0:
        angle += 2 * math.pi

    return angle, n


def get_dist_fast(point, bb):
    """Calculate the distance between a ``point`` and a bounding box ``bb`` by adding up the x- and y-distance.

    :param point: a point given by [x, y]
    :param bb: the bounding box of a baseline polygon
    :type point: list of float
    :type bb: Rectangle
    :return: the distance of the point to the bounding box
    """
    dist = 0.0
    if point[0] < bb.x:
        dist += bb.x - point[0]
    if point[0] > bb.x + bb.width:
        dist += point[0] - bb.x - bb.width
    if point[1] < bb.y:
        dist += bb.y - point[1]
    if point[1] > bb.y + bb.height:
        dist += point[1] - bb.y - bb.height

    return dist


def get_in_dist(p1, p2, or_vec_x, or_vec_y):
    """Calculate the inline distance of the points ``p1`` and ``p2`` according to the orientation vector with
    x-coordinate ``or_vec_x`` and y-coordinate ``or_vec_y``.


    :param p1: first point
    :param p2: second point
    :param or_vec_x: x-coordinate of the orientation vector
    :param or_vec_y: y-coordinate of the orientation vector
    :return: the inline distance of the points p1 and p2 according to the given orientation vector
    """
    diff_x = p1[0] - p2[0]
    diff_y = -p1[1] + p2[1]

    # Parallel component of (diff_x, diff_y) is lambda * (or_vec_x, or_vec_y) with lambda:
    return diff_x * or_vec_x + diff_y * or_vec_y


def get_off_dist(p1, p2, or_vec_x, or_vec_y):
    """Calculate the offline distance of the points ``p1`` and ``p2`` according to the orientation vector with
    x-coordinate ``or_vec_x`` and y-coordinate ``or_vec_y``.

    :param p1: first point
    :param p2: second point
    :param or_vec_x: x-coordinate of the orientation vector
    :param or_vec_y: y-coordinate of the orientation vector
    :return: the offline distance of the points p1 and p2 according to the given orientation vector
    """
    diff_x = p1[0] - p2[0]
    diff_y = -p1[1] + p2[1]

    return diff_x * or_vec_y - diff_y * or_vec_x


# TODO: Compare calculations with Tobis dissertation
def calc_tols(polys_truth, tick_dist=5, max_d=250, rel_tol=0.25):
    """Calculate tolerance values for every GT baseline according to https://arxiv.org/pdf/1705.03311.pdf.

    :param polys_truth: groundtruth baseline polygons (normalized)
    :param tick_dist: desired distance of points of the baseline polygon (default: 5)
    :param max_d: max distance of pixels of a baseline polygon to any other baseline polygon (distance in terms of the
    x- and y-distance of the point to a bounding box of another polygon - see get_dist_fast) (default: 250)
    :param rel_tol: relative tolerance value (default: 0.25)
    :type polys_truth: list of Polygon
    :return: tolerance values of the GT baselines
    """
    tols = []
    for poly_a in polys_truth:
        # Calculate the angle of the linear regression line representing the baseline polygon poly_a
        angle = calc_reg_line_stats(poly_a)[0]
        # Orientation vector (given by angle) of length 1
        or_vec_y, or_vec_x = math.sin(angle), math.cos(angle)
        dist = max_d
        # first and last point of polygon
        pt_a1 = [poly_a.x_points[0], poly_a.y_points[0]]
        pt_a2 = [poly_a.x_points[-1], poly_a.y_points[-1]]

        # iterate over pixels of the current GT baseline polygon
        for x_a, y_a in zip(poly_a.x_points, poly_a.y_points):
            p_a = [x_a, y_a]
            # iterate over all other polygons (to calculate X_G)
            for poly_b in polys_truth:
                if poly_b != poly_a:
                    # if polygon poly_b is too far away from pixel p_a, skip
                    if get_dist_fast(p_a, poly_b.get_bounding_box()) > dist:
                        continue

                    # get first and last pixel of baseline polygon poly_b
                    pt_b1 = poly_b.x_points[0], poly_b.y_points[0]
                    pt_b2 = poly_b.x_points[-1], poly_b.y_points[-1]

                    # calculate the inline distance of the points
                    in_dist1 = get_in_dist(pt_a1, pt_b1, or_vec_x, or_vec_y)
                    in_dist2 = get_in_dist(pt_a1, pt_b2, or_vec_x, or_vec_y)
                    in_dist3 = get_in_dist(pt_a2, pt_b1, or_vec_x, or_vec_y)
                    in_dist4 = get_in_dist(pt_a2, pt_b2, or_vec_x, or_vec_y)
                    if (in_dist1 < 0 and in_dist2 < 0 and in_dist3 < 0 and in_dist4 < 0) or (
                            in_dist1 > 0 and in_dist2 > 0 and in_dist3 > 0 and in_dist4 > 0):
                        continue

                    for p_b in zip(poly_b.x_points, poly_b.y_points):
                        if abs(get_in_dist(p_a, p_b, or_vec_x, or_vec_y)) <= 2 * tick_dist:
                            dist = min(dist, abs(get_off_dist(p_a, p_b, or_vec_x, or_vec_y)))
        if dist < max_d:
            tols.append(dist)
        else:
            tols.append(0)

    sum_tols = 0.0
    num_tols = 0
    for tol in tols:
        if tol != 0:
            sum_tols += tol
            num_tols += 1

    mean_tols = max_d
    if num_tols:
        mean_tols = sum_tols / num_tols

    for i, tol in enumerate(tols):
        if tol == 0:
            tols[i] = mean_tols
        tols[i] = min(tol, mean_tols)
        tols[i] *= rel_tol

    return tols


def f_measure(precision, recall):
    """
    Computes the F1-score for given precision and recall values.

    :param precision: float
    :param recall: float
    :return: F1-score (or 0.0 if both precision and recall are 0.0)
    """
    assert precision.dtype == float and recall.dtype == float, "precision and recall have to be floats"
    if precision == 0 and recall == 0:
        return 0.0
    else:
        return 2.0 * precision * recall / (precision + recall)
