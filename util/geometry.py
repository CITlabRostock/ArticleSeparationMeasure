# -*- coding: utf-8 -*-

import sys
import numpy as np
from util.xmlformats import *


class Rectangle(object):

    def __init__(self, x=0, y=0, width=0, height=0):
        """ Constructs a new rectangle.

        :param x: (int) x coordinate of the upper left corner of the rectangle
        :param y: (int) y coordinate of the upper left corner of the rectangle
        :param width: (int) width of the rectangle
        :param height: (int) height of the rectangle
        """
        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"
        assert type(width) == int, "width has to be int"
        assert type(height) == int, "height has to be int"

        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def get_bounds(self):
        """ Get the bounding rectangle of this rectangle.

        :return: (Rectangle) bounding rectangle
        """
        return Rectangle(self.x, self.y, width=self.width, height=self.height)

    def translate(self, dx, dy):
        """ Translates this rectangle the indicated distance, to the right along the x coordinate axis, and downward
        along the y coordinate axis.

        :param dx: (int) amount to translate along the x axis
        :param dy: (int) amount to translate along the y axis
        """
        assert type(dx) == int, "dx has to be int"
        assert type(dy) == int, "dy has to be int"

        old_v = self.x
        new_v = old_v + dx

        if dx < 0:
            # moving leftward
            if new_v > old_v:
                # negative overflow
                if self.width >= 0:
                    self.width += new_v - (-sys.maxsize - 1)

                new_v = -sys.maxsize - 1
        else:
            # moving rightward or staying still
            if new_v < old_v:
                # positive overflow
                if self.width >= 0:
                    self.width += new_v - sys.maxsize

                    if self.width < 0:
                        self.width = sys.maxsize

                new_v = sys.maxsize

        self.x = new_v

        old_v = self.y
        new_v = old_v + dy

        if dy < 0:
            # moving upward
            if new_v > old_v:
                # negative overflow
                if self.height >= 0:
                    self.height += new_v - (-sys.maxsize - 1)

                new_v = -sys.maxsize - 1
        else:
            # moving downward or staying still
            if new_v < old_v:
                # positive overflow
                if self.height >= 0:
                    self.height += new_v - sys.maxsize

                    if self.height < 0:
                        self.height = sys.maxsize

                new_v = sys.maxsize

        self.y = new_v

    def intersection(self, r):
        """ Computes the intersection of this rectangle with the specified rectangle.

        :param r: (Rectangle) specified rectangle
        :return: (Rectangle) a new rectangle presenting the intersection of the two rectangles
        """
        assert type(r) == Rectangle, "r has to be Rectangle"

        tx1 = self.x
        ty1 = self.y
        tx2 = tx1 + self.width
        ty2 = ty1 + self.height

        rx1 = r.x
        ry1 = r.y
        rx2 = rx1 + r.width
        ry2 = ry1 + r.height

        if tx1 < rx1:
            tx1 = rx1
        if ty1 < ry1:
            ty1 = ry1
        if tx2 > rx2:
            tx2 = rx2
        if ty2 > ry2:
            ty2 = ry2

        # width of the intersection rectangle
        tx2 -= tx1
        # height of the intersection rectangle
        ty2 -= ty1
        # tx2, ty2 might underflow
        if tx2 < -sys.maxsize - 1:
            tx2 = -sys.maxsize - 1
        if ty2 < -sys.maxsize - 1:
            ty2 = -sys.maxsize - 1

        return Rectangle(tx1, ty1, width=tx2, height=ty2)


class Polygon(object):

    def __init__(self, x_points=None, y_points=None, n_points=0):
        """ Constructs a new polygon.

        :param x_points: (list of ints) list of x coordinates of the polygon
        :param y_points: (list of ints) list of y coordinates of the polygon
        :param n_points: (int) total number of points in the polygon
        """
        if x_points is not None:
            assert type(x_points) == list, "x_points has to be a list of ints"
            assert all(type(x) == int for x in x_points), "x_points has to be a list of ints"
            if n_points > len(x_points) or n_points > len(y_points):
                raise Exception("Bounds Error: n_points > len(x_points) or n_points > len(y_points)")

            self.x_points = x_points
        else:
            self.x_points = []

        if y_points is not None:
            assert type(y_points) == list, "y_points has to be a list of ints"
            assert all(type(y) == int for y in y_points), "y_points has to be a list of ints"
            if n_points > len(x_points) or n_points > len(y_points):
                raise Exception("Bounds Error: n_points > len(x_points) or n_points > len(y_points)")

            self.y_points = y_points
        else:
            self.y_points = []

        assert type(n_points) == int, "n_points has to be int"
        if n_points < 0:
            raise Exception("Negative Size: n_points < 0")

        self.n_points = n_points
        self.bounds = None  # bounds of this polygon (Rectangle type !!!)

    def translate(self, delta_x, delta_y):
        """ Translates the vertices of this polygon by delta_x along the x axis and by delta_y along the y axis.

        :param delta_x: (int) amount to translate along the x axis
        :param delta_y: (int) amount to translate along the y axis
        """
        assert type(delta_x) == int, "delta_x has to be int"
        assert type(delta_y) == int, "delta_y has to be int"

        for i in range(self.n_points):
            self.x_points[i] += delta_x
            self.y_points[i] += delta_y

        if self.bounds is not None:
            self.bounds.translate(delta_x, delta_y)

    def calculate_bounds(self):
        """ Calculates the bounding box of points of the polygon. """

        bounds_min_x = min(self.x_points)
        bounds_min_y = min(self.y_points)

        bounds_max_x = max(self.x_points)
        bounds_max_y = max(self.y_points)

        self.bounds = Rectangle(bounds_min_x, bounds_min_y, width=bounds_max_x - bounds_min_x,
                                height=bounds_max_y - bounds_min_y)

    def update_bounds(self, x, y):
        """ Resizes the bounding box to accommodate the specified coordinates.

        :param x: (int) x coordinate
        :param y: (int) y coordinate
        """
        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"

        if x < self.bounds.x:
            self.bounds.width = self.bounds.width + (self.bounds.x - x)
            self.bounds.x = x
        else:
            self.bounds.width = max(self.bounds.width, x - self.bounds.x)

        if y < self.bounds.y:
            self.bounds.height = self.bounds.height + (self.bounds.y - y)
            self.bounds.y = y
        else:
            self.bounds.height = max(self.bounds.height, y - self.bounds.y)

    def add_point(self, x, y):
        """ Appends the specified coordinates to this polygon.

        :param x: (int) x coordinate of the added point
        :param y: (int) y coordinate of the added point
        """
        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"

        self.x_points.append(x)
        self.y_points.append(y)
        self.n_points += 1

        if self.bounds is not None:
            self.update_bounds(x, y)

    def get_bounding_box(self):
        """ Get the bounding box of this polygon (= smallest rectangle including this polygon).

        :return: (Rectangle) rectangle defining the bounds of this polygon
        """
        if self.n_points == 0:
            return Rectangle()

        if self.bounds is None:
            self.calculate_bounds()

        return self.bounds.get_bounds()


class ArticleRectangle(Rectangle):

    def __init__(self, x=0, y=0, width=0, height=0, textlines=None, article_ids=None):
        super().__init__(x, y, width, height)

        self.textlines = textlines
        if article_ids is None and textlines is not None:
            self.a_ids = self.get_articles()
        else:
            self.a_ids = article_ids

    def get_articles(self):
        # traverse the baselines/textlines and check the article id
        article_set = set()

        for tl in self.textlines:
            article_set.add(tl.get_article_id())

        return article_set

    def contains_polygon(self, polygon, x, y, width, height):
        """ Checks if a polygon intersects with (or lies within) a (sub)rectangle given by the coordinates x,y
        (upper left point) and the width and height of the rectangle. """

        # iterate over the points of the polygon
        for i in range(polygon.n_points - 1):
            line_segment_bl = [polygon.x_points[i:i + 2], polygon.y_points[i:i + 2]]

            # The baseline segment lies outside the rectangle completely to the right/left/top/bottom
            if max(line_segment_bl[0]) <= x or min(line_segment_bl[0]) >= x + width or max(
                    line_segment_bl[1]) <= y or min(line_segment_bl[1]) >= y + height:
                continue

            # The baseline segment lies inside the rectangle
            if min(line_segment_bl[0]) >= x and max(line_segment_bl[0]) <= x + width and min(
                    line_segment_bl[1]) >= y and max(line_segment_bl[1]) <= y + height:
                return True

            # The baseline segment intersects with the rectangle or lies outside the rectangle but doesn't lie
            # completely right/left/top/bottom
            # First check intersection with the vertical line segments of the rectangle
            line_segment_rect_left = [[x, x], [y, y + height]]
            if check_intersection(line_segment_bl, line_segment_rect_left) is not None:
                return True
            line_segment_rect_right = [[x + width, x + width], [y, y + height]]
            if check_intersection(line_segment_bl, line_segment_rect_right) is not None:
                return True

            # Check other two sides
            line_segment_rect_top = [[x, x + width], [y, y]]
            if check_intersection(line_segment_bl, line_segment_rect_top) is not None:
                return True
            line_segment_rect_bottom = [[x, x + width], [y + height, y + height]]
            if check_intersection(line_segment_bl, line_segment_rect_bottom) is not None:
                return True

        return False

    def create_subregions(self, ar_list=None):

        # width1 equals width2 if width is even, else width2 = width1 + 1
        # same for height1 and height2
        if ar_list is None:
            ar_list = []
        width1 = self.width // 2
        width2 = self.width - width1
        height1 = self.height // 2
        height2 = self.height - height1

        #########################
        #           #           #
        #     I     #     II    #
        #           #           #
        #########################
        #           #           #
        #    III    #     IV    #
        #           #           #
        #########################

        # determine textlines for each subregion
        tl1 = []
        tl2 = []
        tl3 = []
        tl4 = []
        a_ids1 = set()
        a_ids2 = set()
        a_ids3 = set()
        a_ids4 = set()

        for tl in self.textlines:
            # get baseline
            bl = tl.baseline.to_polygon()
            contains_polygon = self.contains_polygon(bl, self.x, self.y, width1, height1)
            if contains_polygon:
                tl1 += [tl]
                a_ids1.add(tl.get_article_id())
                # continue
            contains_polygon = self.contains_polygon(bl, self.x + width1, self.y, width2, height1)
            if contains_polygon:
                tl2 += [tl]
                a_ids2.add(tl.get_article_id())
                # continue
            contains_polygon = self.contains_polygon(bl, self.x, self.y + height1, width1, height2)
            if contains_polygon:
                tl3 += [tl]
                a_ids3.add(tl.get_article_id())
                # continue
            contains_polygon = self.contains_polygon(bl, self.x + width1, self.y + height1, width2, height2)
            if contains_polygon:
                tl4 += [tl]
                a_ids4.add(tl.get_article_id())
                # continue

        a_rect1 = ArticleRectangle(self.x, self.y, width1, height1, tl1, a_ids1)
        a_rect2 = ArticleRectangle(self.x + width1, self.y, width2, height1, tl2, a_ids2)
        a_rect3 = ArticleRectangle(self.x, self.y + height1, width1, height2, tl3, a_ids3)
        a_rect4 = ArticleRectangle(self.x + width1, self.y + height1, width2, height2, tl4, a_ids4)

        # run create_subregions on Rectangles that contain more than one TextLine object
        for a_rect in [a_rect1, a_rect2, a_rect3, a_rect4]:
            if len(a_rect.a_ids) > 1:  # or a_rect.width > 200:
                a_rect.create_subregions(ar_list)
            else:
                ar_list.append(a_rect)

        return ar_list


def check_intersection(line_1, line_2):
    """ Checks if two line segments `line1` and `line2` intersect. If they do so, the function returns the intersection
    point as [x,y] coordinate (special case for overlapping ["inf", "inf"]), otherwise `None`.

    :param line_1: list containing the x- and y-coordinates as [[x1,x2],[y1,y2]]
    :param line_2: list containing the x- and y-coordinates as [[x1,x2],[y1,y2]]
    :return: intersection point [x,y] if the line segments intersect, None otherwise
    """
    x_points1, y_points1 = line_1
    x_points2, y_points2 = line_2

    # consider vector form (us + s*vs = u + t*v)
    us = [x_points1[0], y_points1[0]]
    vs = [x_points1[1] - x_points1[0], y_points1[1] - y_points1[0]]

    u = [x_points2[0], y_points2[0]]
    v = [x_points2[1] - x_points2[0], y_points2[1] - y_points2[0]]

    A = np.array([vs, [-v[0], -v[1]]]).transpose()
    b = np.array([u[0] - us[0], u[1] - us[1]])

    rank_A = np.linalg.matrix_rank(A)
    rank_Ab = np.linalg.matrix_rank(np.c_[A, b])

    # no solution => parallel
    if rank_A != rank_Ab:
        return None

    # infinite solutions => one line is the multiple of the other
    if rank_A == rank_Ab == 1:
        # check if there is an overlap
        # us + s*vs = u
        s1 = (u[0] - us[0]) / vs[0]
        s2 = (u[1] - us[1]) / vs[1]
        if s1 == s2:
            if 0 < s1 < 1:
                return ["inf", "inf"]
            elif s1 == 0 or s1 == 1:
                return [us[0] + s1 * vs[0], us[1] + s1 * vs[1]]

        # us + s*vs = v
        s1 = (v[0] - us[0]) / vs[0]
        s2 = (v[1] - us[1]) / vs[1]
        if s1 == s2:
            if 0 < s1 < 1:
                return ["inf", "inf"]
            elif s1 == 0 or s1 == 1:
                return [us[0] + s1 * vs[0], us[1] + s1 * vs[1]]

        # otherwise there is no overlap and no intersection
        return None

    [s, t] = np.linalg.inv(A).dot(b)

    if not (0 <= s <= 1 and 0 <= t <= 1):
        return None

    return [us[0] + s * vs[0], us[1] + s * vs[1]]


if __name__ == '__main__':
    # p = Polygon([1, 2, 4, 6, 7], [2, 4, 2, 3, 1], 5)
    #
    # print(p.x_points)
    # print(p.y_points, "\n")
    #
    # p.calculate_bounds()
    # print("(", p.bounds.x, ", ", p.bounds.y, ")", "  width = ", p.bounds.width, "  height = ", p.bounds.height, "\n")
    #
    # p.add_point(7, 1)
    # print("(", p.bounds.x, ", ", p.bounds.y, ")", "  width = ", p.bounds.width, "  height = ", p.bounds.height, "\n")
    #
    # r = Rectangle(1, 2, 5, 3)
    #
    # int_r = r.intersection(Rectangle(1, 2, 0, 0))
    # print("(", int_r.x, ", ", int_r.y, ")", "  width = ", int_r.width, "  height = ", int_r.height)

    line1 = [[0, 0], [0, 2]]
    line2 = [[2, 2], [-1, 2]]

    line1 = [[0, 0], [0, 2]]
    line2 = [[1, 3], [1, 2]]

    line1 = [[0, 0], [0, 2]]
    line2 = [[-1, 3], [0, 2]]

    line1 = [[0, 0], [0, 2]]
    line2 = [[0, 2], [0, 2]]

    lineR1 = [[0, 3], [3, 3]]
    lineR2 = [[3, 3], [3, 6]]
    lineR3 = [[0, 3], [6, 6]]
    lineR4 = [[0, 0], [3, 6]]
    lineB = [[2, 7], [7, 5]]

    print(check_intersection(lineR1, lineB))
    print(check_intersection(lineR2, lineB))
    print(check_intersection(lineR3, lineB))
    print(check_intersection(lineR4, lineB))
