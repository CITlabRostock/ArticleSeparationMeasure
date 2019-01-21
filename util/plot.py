# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

from matplotlib.collections import PolyCollection
from geometry import Polygon


# Two interfaces supported by matplotlib:
#   1. object-oriented interface using axes.Axes and figure.Figure objects
#   2. based on MATLAB using a state-based interface
# "In general, try to use the object-oriented interface over the pyplot interface"


def add_image(axes, path):
    """Add the image given by ``path`` to the plot ``axes``.

    :param axes: represents an individual plot
    :param path: path to the image
    :type axes: matplotlib.pyplot.Axes
    :type path: str
    :return: mpimg.AxesImage
    """
    try:
        img = mpimg.imread(path)
        return axes.imshow(img)
    except ValueError:
        print("Can't add image to the plot. Check if '{}' is a valid path.".format(path))


def add_baselines(axes, blines, color):
    """Add the baselines ``blines`` to the plot ``axes``. The baselines are given by their x- and y-coordinates, e.g.
        [[[1,2,3],[2,3,4]],[[5,6,7],[7,8,9]]]
    if we have two baseline polygons with 3 points each, where the first list is representing the x-values and the second
    the y-values.

    :param axes: represents an individual plot
    :param blines: list of lists of x- and y-coordinates or a Polygon object
    :param color: color of the baselines in the plot
    :type axes: matplotlib.pyplot.Axes
    :type blines: list of (Union[list of (list of Union[int,float]), Polygon])
    :type color: str
    :return: matplotlib.pyplot.Axes
    """

    # convert blines to a list of lists of x- and y-coordinates
    _blines = []
    for bline in blines:
        if type(bline) == Polygon:
            _blines.append([bline.x_points, bline.y_points])
        else:
            _blines.append(bline)

    # Make a list of polygons where each polygon consists of [x,y]-pairs
    blines = [np.transpose(p) for p in blines]
    # Make sure to use "None" in quotation marks, otherwise the default value is used and the polygons are filled
    try:
        baseline_collection = PolyCollection(blines, closed=False, edgecolors=color, facecolors="None")
        return axes.add_collection(baseline_collection)
    except ValueError:
        print("Could not handle the input blines: {}".format(blines))
        exit(1)


def add_surrounding_polygon(axes, polygon, color='green'):
    """Add the surrounding polygon ``polygon`` to the plot ``axes``. The polygon is given by its x- and y-coordinates.

    :param axes: represents an individual plot
    :param polygon: surrounding polygon
    :param color: color of the surrounding polygon plot (default: green)
    :return:
    """
    if type(polygon) == Polygon:
        poly_coll = PolyCollection([np.transpose([polygon.x_points, polygon.y_points])], closed=True, edgecolors=color,
                                   facecolors="None")
    else:
        poly_coll = PolyCollection([np.transpose(polygon)], closed=True, edgecolors=color, facecolors="None")
    return axes.add_collection(poly_coll)


def toggle_view(event, views):
    """Switch between different views in the current plot by pressing the ``event`` key.

    :param event: the key event given by the user, various options available, e.g. to toggle the baselines
    :param views: dictionary of different views given by name:object pairs
    :type event: matplotlib.backend_bases.KeyEvent
    :return: None
    """
    # Toggle baselines
    if event.key == 'b' and "baselines" in views:
        is_visible = views["baselines"].get_visible()
        views["baselines"].set_visible(not is_visible)
        plt.draw()

    # Toggle image
    if event.key == 'i' and "image" in views:
        is_visible = views["image"].get_visible()
        views["image"].set_visible(not is_visible)
        plt.draw()

    if event.key == 'h':
        print("Usage:\n"
              "\ti: toggle image\n"
              "\tb: toggle baselines\n"
              "\th: show this help")

    else:
        return


def check_type(lst, t):
    """Checks if all elements of list ``lst`` are of one of the types in ``t``.

    :param lst: list to check
    :param t: list of types that the elements in list should have
    :return: Bool
    """
    for el in lst:
        if type(el) not in t:
            return False
    return True


def plot(img_path='', baselines=[], surr_polys=[], bcolor="blue"):
    fig, ax = plt.subplots()  # type: (plt.Figure, plt.Axes)
    views = {}

    try:
        img_plot = add_image(ax, img_path)
        fig.canvas.set_window_title(img_path)
        views.update({"image": img_plot})
    except IOError:
        print("Can't handle image path: {}".format(img_path))
        # exit(1)

    if baselines:
        baseline_collection = add_baselines(ax, baselines, bcolor)
        views.update({"baselines": baseline_collection})

    if surr_polys:
        for poly in surr_polys:
            add_surrounding_polygon(ax, poly)

    ax.autoscale_view()

    # Toggle bsaelines with "b", image with "i"
    plt.connect('key_press_event', lambda event: toggle_view(event, views))

    # Add text
    plt.text(0, -20, "image path: {}\n"
                     "gt: {}\n"
                     "hypo: {}".format(img_path, "not implemented yet", "not implemented yet"))

    # Don't show axis
    plt.axis("off")
    plt.show()


if __name__ == '__main__':
    img_path = "./test/resources/metrEx.png"
    baselines = [[[9, 506, 684, 1139], [220, 220, 204, 211]], [[32, 537, 621, 1322], [334, 345, 325, 336]],
                 [[29, 1321], [85, 93]], [[1399, 2342, 2611], [104, 103, 130]], [[1402, 2259, 2599], [220, 211, 229]],
                 [[1395, 2228, 2661], [344, 326, 347]]]
    surr_poly = [[[0, 500, 500, 0], [0, 0, 500, 500]], [[505, 1005, 1005, 505], [505, 505, 1005, 1005]],
                 [[10, 490, 490, 10], [10, 10, 490, 490]]]

    plot(img_path, baselines, surr_poly)
    # plot(img_path='', baselines=baselines)

    path_to_img = "./test/resources/page_test.tif"
    path_to_xml = "./test/resources/page_test.xml"
