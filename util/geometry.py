from __future__ import print_function
import sys


# rectangle class
class Rectangle(object):

    def __init__(self):
        self.x = None
        self.y = None
        self.width = None
        self.height = None

    def set_rectangle(self, x, y, width, height):
        """ set rectangle values """

        assert type(x) == int, "x have to be int"
        assert type(y) == int, "y have to be int"
        assert type(width) == int, "width have to be int"
        assert type(height) == int, "height have to be int"

        # x coordinate of the upper-left corner
        self.x = x
        # y coordinate of the upper-left corner
        self.y = y
        self.width = width
        self.height = height

    def translate(self, dx, dy):
        """ translates the rectangle the indicated distance, to the right along the X coordinate axis, and downward
            along the Y coordinate axis """

        assert type(dx) == int, "dx have to be int"
        assert type(dy) == int, "dy have to be int"

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


# polygon class
class Polygon(object):

    def __init__(self):
        self.n_points = 0
        self.x_points = []
        self.y_points = []
        self.bounds = Rectangle()  # rectangle type!!!
        self.MIN_LENGTH = 4

    def set_polygon(self, x_points, y_points, n_points):
        """ set Polygon values """

        assert type(n_points) == int, "n_points have to be int"
        assert type(x_points) == list, "x_points have to be a list of ints"
        assert all(type(x) == int for x in x_points), "x_points have to be a list of ints"
        assert type(y_points) == list, "y_points have to be a list of ints"
        assert all(type(y) == int for y in y_points), "y_points have to be a list of ints"

        if n_points > len(x_points) or n_points > len(y_points):
            raise Exception("Bounds Error: n_points > len(x_points) or n_points > len(y_points)")

        if n_points < 0:
            raise Exception("Negative Size: n_points < 0")

        self.n_points = n_points
        self.x_points = x_points
        self.y_points = y_points

    def translate(self, delta_X, delta_Y):
        """ translates the vertices of the Polygon by delta_X along the x axis and by delta_Y along the y axis """

        assert type(delta_X) == int, "type(delta_X) have to be int"
        assert type(delta_Y) == int, "type(delta_Y) have to be int"

        for i in range(len(self.x_points)):
            self.x_points[i] += delta_X
            self.y_points[i] += delta_Y

        # if self.bounds != None:
        #     self.bounds.Translate(delta_X, delta_Y)

    def calculate_bounds(self):
        """ calculte the bounding box of the points """

        bounds_Min_X = min(self.x_points)
        bounds_Min_Y = min(self.y_points)

        bounds_Max_X = max(self.x_points)
        bounds_Max_Y = max(self.y_points)

        self.bounds = Rectangle()
        self.bounds.set_rectangle(bounds_Min_X, bounds_Min_Y, width=bounds_Max_X - bounds_Min_X,
                                  height=bounds_Max_Y - bounds_Min_Y)

    def update_bounds(self, x, y):
        """ resize the bounding box to accommodate the specified coordinates """

        assert type(x) == int, "x have to be int"
        assert type(y) == int, "y have to be int"

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

        assert type(x) == int, "x have to be int"
        assert type(y) == int, "y have to be int"

        self.x_points.append(x)
        self.y_points.append(y)
        self.n_points += 1

        # if self.bounds != None:
        #     self.update_bounds(x, y)









if __name__ == '__main__':
    p = Polygon()
    p.set_polygon([1,2,2,1], [4,5,6,7], 4)

    p.translate(1,2)
    print(p.x_points)
    print(p.y_points)

    print(min([1,2,3,4,-5]))
    print(max([1,2,3,4,39,7,3000]))


    print(type(sys.maxint))
    print(type(-sys.maxint - 1))

    print(int(sys.maxint + 45))


    r = Rectangle()


    r.set_rectangle(1,2,2,2)

    r.translate(3,1)

    print(r.x)
    print(r.y)

