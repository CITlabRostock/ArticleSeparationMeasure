from __future__ import print_function
import numpy as np
from scipy.stats import linregress


def calc_line(x_points, y_points):
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


if __name__ == '__main__':
    # (1,30) (10,30) (25, 28) (60,32)
    x_points = [1, 10, 25, 60]
    y_points = [30, 30, 28, 32]

    res = calc_line(x_points, y_points)

    print("res = \n", res)
