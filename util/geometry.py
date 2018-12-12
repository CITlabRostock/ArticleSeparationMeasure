from __future__ import print_function
import sys


# rectangle class
class Rectangle(object):

    def __init__(self):
        self.x = 0
        self.y = 0
        self.width = 0
        self.height = 0

    def set_rectangle(self, x, y, width, height):
        """ set rectangle values """

        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"
        assert type(width) == int, "width has to be int"
        assert type(height) == int, "height has to be int"

        # x coordinate of the upper-left corner
        self.x = x
        # y coordinate of the upper-left corner
        self.y = y
        self.width = width
        self.height = height

    def translate(self, dx, dy):
        """ translates the rectangle the indicated distance, to the right along the X coordinate axis, and downward
            along the Y coordinate axis """

        assert type(dx) == int, "dx has to be int"
        assert type(dy) == int, "dy has to be int"

        oldv = self.x
        newv = oldv + dx

        if dx < 0:
            # moving leftward
            if newv > oldv:
                # negative overflow
                if self.width >= 0:
                    self.width += newv - (-sys.maxint - 1)

                newv = -sys.maxint - 1
        else:
            # moving rightward or staying still
            if newv < oldv:
                # positive overflow
                if self.width >= 0:
                    self.width += newv - sys.maxint

                    if self.width < 0:
                        self.width = sys.maxint

                newv = sys.maxint

        self.x = newv

        oldv = self.y
        newv = oldv + dy

        if dy < 0:
            # moving upward
            if newv > oldv:
                # negative overflow
                if self.height >= 0:
                    self.height += newv - (-sys.maxint - 1)

                newv = (-sys.maxint - 1)
        else:
            # moving downward or staying still
            if newv < oldv:
                # positive overflow
                if self.height >= 0:
                    self.height += newv - sys.maxint

                    if self.height < 0:
                        self.height = sys.maxint

                newv = sys.maxint

        self.y = newv

    # TODO
    def intersection(self, rect):
        assert isinstance(rect, Rectangle), "rect has to be Rectangle"
        pass


# polygon class
class Polygon(object):

    def __init__(self, x_points=None, y_points=None, n_points=0):

        if x_points is not None:
            assert type(x_points) == list, "x_points has to be a list"
            assert all(type(x) == int for x in x_points), "elements of x_points have to be ints"
            if n_points > len(x_points) or n_points > len(y_points):
                raise Exception("Bounds Error: n_points > len(x_points) or n_points > len(y_points)")

            self.x_points = x_points
        else:
            self.x_points = []

        if y_points is not None:
            assert type(y_points) == list, "y_points has to be a list"
            assert all(type(y) == int for y in y_points), "elements of y_points have to be ints"
            if n_points > len(x_points) or n_points > len(y_points):
                raise Exception("Bounds Error: n_points > len(x_points) or n_points > len(y_points)")

            self.y_points = y_points
        else:
            self.y_points = []

        assert type(n_points) == int, "n_points has to be int"
        if n_points < 0:
            raise Exception("Negative Size: n_points < 0")

        self.n_points = 0
        self.bounds = None  # rectangle type!!!

        self.MIN_LENGTH = 4  # ???

    def translate(self, delta_x, delta_y):
        """ translates the vertices of the Polygon by delta_x along the x axis and by delta_y along the y axis """

        assert type(delta_x) == int, "delta_X has to be int"
        assert type(delta_y) == int, "delta_Y has to be int"

        for i in range(len(self.x_points)):
            self.x_points[i] += delta_x
            self.y_points[i] += delta_y

        if self.bounds is not None:
            self.bounds.translate(delta_x, delta_y)

    def calculate_bounds(self):
        """ calculte the bounding box of the points """

        bounds_min_x = min(self.x_points)
        bounds_min_y = min(self.y_points)

        bounds_max_x = max(self.x_points)
        bounds_max_y = max(self.y_points)

        self.bounds = Rectangle()
        self.bounds.set_rectangle(bounds_min_x, bounds_min_y,
                                  width=bounds_max_x - bounds_min_x,
                                  height=bounds_max_y - bounds_min_y)

    def update_bounds(self, x, y):
        """ resize the bounding box to accommodate the specified coordinates """

        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"

        if x < self.bounds.x:
            self.bounds.width = self.bounds.width + (self.bounds.x - x)
            self.bounds.x = x
        else:
            self.bounds.width = max(self.bounds.width, x - self.bounds.width)

        if y < self.bounds.y:
            self.bounds.height = self.bounds.height + (self.bounds.y - y)
            self.bounds.y = y
        else:
            self.bounds.height = max(self.bounds.height, y - self.bounds.height)

    def add_point(self, x, y):
        """ appends the specified coordinates to the polygon """

        assert type(x) == int, "x has to be int"
        assert type(y) == int, "y has to be int"

        self.x_points.append(x)
        self.y_points.append(y)
        self.n_points += 1

        if self.bounds is not None:
            self.update_bounds(x, y)

    def get_bounding_box(self):
        """ returns the bounding box of the polygon """

        if self.n_points == 0:
            return Rectangle()

        if self.bounds is None:
            self.calculate_bounds()


if __name__ == '__main__':
    p = Polygon([1, 2, 2, 1], [4, 5, 6, 7], 4)
    print(type(p))
    print(isinstance(p, Polygon))

    p.translate(1, 2)
    print(p.x_points)
    print(p.y_points)

    print(min([1, 2, 3, 4, -5]))
    print(max([1, 2, 3, 4, 39, 7, 3000]))

    print(type(sys.maxint))
    print(type(-sys.maxint - 1))

    print(int(sys.maxint + 45))

    r = Rectangle()
    r.set_rectangle(1, 2, 2, 2)
    r.translate(3, 1)

    print(r.x)
    print(r.y)
