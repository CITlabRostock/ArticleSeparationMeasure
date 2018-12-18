from __future__ import print_function
import sys


# rectangle class
class Rectangle(object):

    def __init__(self, x=0, y=0, width=0, height=0):
        """ constructs a new rectangle

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
        """ gets the bounding rectangle of this rectangle

        :return: (Rectangle) bounding rectangle
        """
        return Rectangle(self.x, self.y, width=self.width, height=self.height)

    def translate(self, dx, dy):
        """ translates this rectangle the indicated distance, to the right along the x coordinate axis, and downward
            along the y coordinate axis

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
                    self.width += new_v - (-sys.maxint - 1)

                new_v = -sys.maxint - 1
        else:
            # moving rightward or staying still
            if new_v < old_v:
                # positive overflow
                if self.width >= 0:
                    self.width += new_v - sys.maxint

                    if self.width < 0:
                        self.width = sys.maxint

                new_v = sys.maxint

        self.x = new_v

        old_v = self.y
        new_v = old_v + dy

        if dy < 0:
            # moving upward
            if new_v > old_v:
                # negative overflow
                if self.height >= 0:
                    self.height += new_v - (-sys.maxint - 1)

                new_v = -sys.maxint - 1
        else:
            # moving downward or staying still
            if new_v < old_v:
                # positive overflow
                if self.height >= 0:
                    self.height += new_v - sys.maxint

                    if self.height < 0:
                        self.height = sys.maxint

                new_v = sys.maxint

        self.y = new_v

    def intersection(self, r):
        """ computes the intersection of this rectangle with the specified rectangle

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
        if tx2 < -sys.maxint - 1:
            tx2 = -sys.maxint - 1
        if ty2 < -sys.maxint - 1:
            ty2 = -sys.maxint - 1

        return Rectangle(tx1, ty1, width=tx2, height=ty2)

    def contains(self, x, y):
        """ checks whether the specified point (x, y) is inside this rectangle or not
            Definition of insideness: A point is considered to lie inside a Shape if and only if:
            - it lies completely inside the Shape boundary or
            - it lies exactly on the Shape boundary and the space immediately adjacent to the point in the increasing x
              direction is entirely inside the boundary or
            - it lies exactly on a horizontal boundary segment and the space immediately adjacent to the point in the
              increasing y direction is inside the boundary

        :param x: (int) the specified x coordinate
        :param y: (int) the specified y coordinate
        :return: (bool) True (if point is inside this rectangle), False (otherwise)
        """
        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"

        w_orig = self.width
        h_orig = self.height

        if w_orig < 0 or h_orig < 0:
            # at least one of the dimensions is negative
            return False

        x_orig = self.x
        y_orig = self.y

        if x < x_orig or y < y_orig:
            return False

        w_orig += x_orig
        h_orig += y_orig

        # overflow or intersect
        return (w_orig < x_orig or w_orig > x) and (h_orig < y_orig or h_orig > y)


# polygon class
class Polygon(object):

    def __init__(self, x_points=None, y_points=None, n_points=0):
        """ constructs a new polygon

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
        """ translates the vertices of this polygon by delta_x along the x axis and by delta_y along the y axis

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
        """ calculates the bounding box of points of the polygon """

        bounds_min_x = min(self.x_points)
        bounds_min_y = min(self.y_points)

        bounds_max_x = max(self.x_points)
        bounds_max_y = max(self.y_points)

        self.bounds = Rectangle(bounds_min_x, bounds_min_y, width=bounds_max_x - bounds_min_x,
                                height=bounds_max_y - bounds_min_y)

    def update_bounds(self, x, y):
        """ resizes the bounding box to accommodate the specified coordinates

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
        """ appends the specified coordinates to this polygon

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
        """ gets the bounding box of this polygon (= smallest rectangle including this polygon)

        :return: (Rectangle) rectangle defining the bounds of this polygon
        """
        if self.n_points == 0:
            return Rectangle()

        if self.bounds is None:
            self.calculate_bounds()

        return self.bounds.get_bounds()

    # TODO: bug fix !!!
    def contains(self, x, y):
        """ determines whether the specified point is inside this polygon

        :param x: (int) x coordinate of the point
        :param y: (int) y coordinate of the point
        :return: (bool) True (if point is included), False (otherwise)
        """
        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"

        if self.n_points <= 2 or not self.get_bounds().contains(x, y):
            return False

        hits = 0

        last_x = self.x_points[-1]
        last_y = self.y_points[-1]

        # walk the edges of the polygon
        for i in range(self.n_points):

            cur_x = self.x_points[i]
            cur_y = self.y_points[i]

            if cur_y == last_y:
                continue

            if cur_x < last_x:
                if x >= last_x:
                    continue
                left_x = cur_x
            else:
                if x >= cur_x:
                    continue
                left_x = last_x

            if cur_y < last_y:
                if y < cur_y or y >= last_y:
                    continue
                if x < left_x:
                    hits += 1
                    continue
                test1 = x - cur_x
                test2 = y - cur_y
            else:
                if y < last_y or y >= cur_y:
                    continue
                if x < left_x:
                    hits += 1
                    continue
                test1 = x - last_x
                test2 = y - last_y

            if test1 < (test2 / (last_y - cur_y) * (last_x - cur_x)):
                hits += 1

            last_x = cur_x
            last_y = cur_y

        # return ((hits & 1) != 0);
        # if hits % 2 == 0:
        #     return False
        # elif hits % 2 == 1:
        #     return True

        return hits != 0


if __name__ == '__main__':
    p = Polygon([1, 2, 4, 6, 7], [2, 4, 2, 3, 1], 5)
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
    print(p.contains(2, 1))

    # r = Rectangle(1, 2, 5, 3)
    # print(r.contains(6, 2))
    #
    # int_r = r.intersection(Rectangle(1, 2, 0, 0))
    # print("(", int_r.x, ", ", int_r.y, ")", "  width = ", int_r.width, "  height = ", int_r.height)
