# -*- coding: utf-8 -*-


from __future__ import print_function
from __future__ import absolute_import
from __future__ import division

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np

from matplotlib.collections import PolyCollection


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
    if we have to baseline polygons with 3 points each, where the first list is representing the x-values and the second
    the y-values.

    :param axes: represents an individual plot
    :param blines: list of lists of x- and y-coordinates
    :param color: color of the baselines in the plot
    :type axes: matplotlib.pyplot.Axes
    :type blines: list of (list of (list of Union[int,float]))
    :type color: str
    :return: None
    """
    # Make a list of polygons where each polgon contains of [x,y]-pairs
    blines = [np.transpose(p) for p in blines]
    # Make sure to use "None" in quotation marks, otherwise the default value will be returned
    try:
        baseline_collection = PolyCollection(blines, closed=False, edgecolors=color, facecolors="None")
        return axes.add_collection(baseline_collection)
    except ValueError:
        print("Could not handle the input blines: {}".format(blines))
        exit(1)

    # for b in blines:
    #     assert len(b[0]) == len(b[1]), "different number of x- and y-coordinates: {}".format(b)
    #     # if type of coordinates is not int or float, then skip
    #     if not check_type(b[0], [int, float]) or not check_type(b[1], [int, float]):
    #         print("Skip baseline {}".format(b))
    #         continue
    #     b = np.transpose(b)
    #     # x, y = b
    #     # axes.plot(x, y, color=color)
    #     patches.Polygon(b, closed=False, color=color)
    # return axes


def toggle_view(event, views):
    """Switch between different views in the current plot by pressing the ``event`` key.

    :param event:
    :param views: dictionary of different views given by name:object pairs
    :type event: matplotlib.backend_bases.KeyEvent
    :return:
    """
    # Toggle baselines
    if event.key == 'b':
        is_visible = views["baselines"].get_visible()
        views["baselines"].set_visible(not is_visible)
        plt.draw()

    # Toggle image
    if event.key == 'i':
        is_visible = views["image"].get_visible()
        views["image"].set_visible(not is_visible)
        plt.draw()

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


if __name__ == '__main__':
    fig, ax = plt.subplots()  # type: (plt.Figure, plt.Axes)
    img_plot = add_image(ax, "./test/resources/metrEx.png")

    baselines = [[[9, 506, 684, 1139], [220, 220, 204, 211]], [[32, 537, 621, 1322], [334, 345, 325, 336]],
                 [[29, 1321], [85, 93]], [[1399, 2342, 2611], [104, 103, 130]], [[1402, 2259, 2599], [220, 211, 229]],
                 [[1395, 2228, 2661], [344, 326, 347]]]

    baseline_collection = add_baselines(ax, baselines, "blue")
    # ax.add_collection(baseline_collection)
    ax.autoscale_view()

    views = {"baselines": baseline_collection, "image": img_plot}

    # Toggle baselines with "b" and the image with "i"
    plt.connect('key_press_event', lambda event: toggle_view(event, views))

    # baseline_collection.set_visible(False)
    # img_plot.set_visible(False)

    plt.axis("off")
    plt.show()
