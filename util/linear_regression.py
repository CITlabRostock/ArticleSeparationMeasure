from __future__ import print_function
import numpy as np


def calc_line(x_points, y_points):
    assert isinstance(x_points, list)
    assert isinstance(y_points, list)
    assert len(x_points) == len(y_points)
    n_points = len(x_points)

    min_x = 10000
    max_x = 0
    sum_x = 0.0

    a = np.zeros([n_points, 2])
    y = np.zeros([n_points])

    for i in range(n_points):
        y[i] = y_points[i]
        px = x_points[i]
        a[i, 0] = 1.0
        a[i, 1] = px

        min_x = min(px, min_x)
        max_x = max(px, max_x)
        sum_x += px
    if max_x - min_x < 2:
        print("TODO")

    return solve_lin(a, y)


def solve_lin(a, y):
    assert isinstance(a, np.ndarray)
    assert isinstance(y, np.ndarray)

    a_t = np.transpose(a)
    ls = np.matmul(a_t, a)
    rs = np.matmul(a_t, y)

    assert ls.shape == (2, 2)
    det = ls[0, 0] * ls[1, 1] - ls[0, 1] * ls[1, 0]
    if det < 1e-9:
        print("LinearRegression Error: Numerically unstable.")
        print("TODO")
        inv = np.zeros_like(ls)
    else:
        d = 1.0 / det
        inv = np.empty_like(ls)
        inv[0, 0] = d * ls[1, 1]
        inv[1, 1] = d * ls[0, 0]
        inv[1, 0] = -d * ls[1, 0]
        inv[0, 1] = -d * ls[0, 1]

    return np.matmul(inv, rs)


if __name__ == '__main__':
    # (1,30) (10,25) (25, 22) (60,36)
    # x_points = [1, 10, 25, 60]
    # y_points = [30, 25, 22, 36]

    # (1,10) (2, 20) (3,15)
    x_points = [1, 2, 3]
    y_points = [10, 20, 15]

    res = calc_line(x_points, y_points)

    print("res = \n", res)
