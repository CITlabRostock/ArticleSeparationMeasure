# -*- coding: utf-8 -*-

from util.geometry import Polygon
# import util.PAGE as PAGE
from util.xmlformats.Page import Page
from util.xmlformats import PageObjects

import random
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt

from matplotlib import colors as mcolors
from matplotlib.collections import PolyCollection

# Use the default color (black) for the baselines belonging to no article
DEFAULT_COLOR = 'k'

BASECOLORS = mcolors.BASE_COLORS
print(BASECOLORS)
BASECOLORS.pop(DEFAULT_COLOR)
COLORS = dict(BASECOLORS, **mcolors.CSS4_COLORS)
by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                for name, color in COLORS.items())
COLORS_SORTED = [name for hsv, name in by_hsv]
SEED = 501
random.seed(SEED)
random.shuffle(COLORS_SORTED)

# black is the color for the "other" class (first entry in the "colors" list)
COLORS = ["darkgreen", "red", "darkviolet", "darkblue",
          "gold", "darkorange", "brown", "yellowgreen", "darkcyan",

          "darkkhaki", "firebrick", "darkorchid", "deepskyblue",
          "peru", "orangered", "rosybrown", "burlywood", "cadetblue",

          "olivedrab", "palevioletred", "plum", "slateblue",
          "tan", "coral", "sienna", "yellow", "mediumaquamarine",

          "forestgreen", "indianred", "blueviolet", "steelblue",
          "silver", "salmon", "darkgoldenrod", "greenyellow", "darkturquoise",

          "mediumseagreen", "crimson", "rebeccapurple", "navy",
          "darkgray", "saddlebrown", "maroon", "lawngreen", "royalblue",

          "springgreen", "tomato", "violet", "azure",
          "goldenrod", "chocolate", "chartreuse", "teal"]

for color in COLORS_SORTED:
    if color not in COLORS:
        COLORS.append(color)


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
        img = Image.open(path)
        return axes.imshow(img)
    except ValueError:
        print("Can't add image to the plot. Check if '{}' is a valid path.".format(path))


def add_polygons(axes, poly_list, color=DEFAULT_COLOR, closed=False):
    """poly_list = [[(x1,y1), (x2,y2), ... , (xN,yN)], ... , [(u1,v1), (u2, v2), ... , (uM, vM)]]
    else if poly_list if of type Polygon convert it to that form."""
    if check_type(poly_list, [Polygon]):
        poly_list = [list(zip(poly.x_points, poly.y_points)) for poly in poly_list]
    try:
        poly_collection = PolyCollection(poly_list, closed=closed, edgecolors=color, facecolors="None", linewidths=1.2)
        return axes.add_collection(poly_collection)
    except ValueError:
        print(f"Could not handle the input polygon format {poly_list}")
        exit(1)


def toggle_view(event, views):
    """Switch between different views in the current plot by pressing the ``event`` key.

    :param event: the key event given by the user, various options available, e.g. to toggle the baselines
    :param views: dictionary of different views given by name:object pairs
    :type event: matplotlib.backend_bases.KeyEvent
    :return: None
    """
    # Toggle baselines
    if event.key == 'b' and "baselines" in views:
        for bline in views["baselines"]:
            is_visible = bline.get_visible()
            bline.set_visible(not is_visible)
        # is_visible = views["baselines"].get_visible()
        # views["baselines"].set_visible(not is_visible)
        plt.draw()

    # Toggle image
    if event.key == 'i' and "image" in views:
        is_visible = views["image"].get_visible()
        views["image"].set_visible(not is_visible)
        plt.draw()

    # Toggle surrounding polygons
    if event.key == 'p' and "surr_polys" in views:
        for surr_poly in views["surr_polys"]:
            is_visible = surr_poly.get_visible()
            surr_poly.set_visible(not is_visible)
        plt.draw()

    if event.key == 'h':
        print("Usage:\n"
              "\ti: toggle image\n"
              "\tb: toggle baselines\n"
              "\tp: toggle surrounding polygons\n"
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


def plot(img_path='', baselines_list=[], surr_polys=[], bcolors=[]):
    fig, ax = plt.subplots()  # type: (plt.Figure, plt.Axes)
    views = {}

    try:
        img_plot = add_image(ax, img_path)
        fig.canvas.set_window_title(img_path)
        views.update({"image": img_plot})
    except IOError:
        print(f"Can't display image given by path: {img_path}")

    if len(bcolors):
        assert len(bcolors) >= len(baselines_list), f"There should be at least {len(baselines_list)}" \
            f" colors but just got {len(bcolors)}"
    else:
        bcolors = [DEFAULT_COLOR] * len(baselines_list)

    if baselines_list:
        for i, blines in enumerate(baselines_list):
            baseline_collection = add_polygons(ax, blines, bcolors[i], closed=False)
            if 'baselines' in views:
                views['baselines'].append(baseline_collection)
            else:
                views['baselines'] = [baseline_collection]

    if surr_polys:
        surr_poly_collection = add_polygons(ax, surr_polys, DEFAULT_COLOR, closed=True)
        surr_poly_collection.set_visible(False)
        views['surr_polys'] = [surr_poly_collection]

    ax.autoscale_view()

    # Toggle baselines with "b", image with "i", surrounding polygons with "p"
    plt.connect('key_press_event', lambda event: toggle_view(event, views))

    # Add text
    # plt.text(0, -20, "image path: {}\n"
    #                  "gt: {}\n"
    #                  "hypo: {}".format(img_path, "not implemented yet", "not implemented yet"))

    # Don't show axis
    plt.axis("off")
    plt.show()


def plot_article_dict(article_dict, path_to_img):
    # add baselines to the image
    baselines_list = []
    for l in article_dict.itervalues():
        bline_list = []
        for _, bline in l:
            bline_list.append(bline)
        baselines_list.append(bline_list)
    plot(path_to_img, baselines_list, bcolors=COLORS[:len(baselines_list)])


def plot_pagexml(page, path_to_img):
    if type(page) == str:
        page = Page(page)
    assert type(page) == Page, f"Type must be Page, got {type(page)} instead."

    # get baselines based on the article id
    article_dict = page.get_article_dict()
    if not article_dict:
        bcolors = []
        blines_list = []
    elif None in article_dict:
        bcolors = COLORS[:len(article_dict) - 1] + [DEFAULT_COLOR]
        blines_list = [[tline.baseline.points_list for tline in tlines]
                       for (a_id, tlines) in article_dict.items() if a_id is not None] \
                      + [[tline.baseline.points_list for tline in article_dict[None]]]
    else:
        bcolors = COLORS[:len(article_dict)]
        blines_list = [[tline.baseline.points_list for tline in tlines] for tlines in article_dict.values()]

    # get surrounding polygons
    textlines = page.get_textlines()
    surr_polys = [tl.surr_p.points_list for tl in textlines if tl]

    plot(path_to_img, blines_list, surr_polys, bcolors)

    # # get article-baselines dictionary
    # ad = page.get_baseline_text_dict(as_poly=True)
    #
    # # add baselines and plot
    # plot_article_dict(ad, path_to_img)


if __name__ == '__main__':
    # img_path = "./test/resources/metrEx.png"
    # baselines = [[[9, 506, 684, 1139], [220, 220, 204, 211]], [[32, 537, 621, 1322], [334, 345, 325, 336]],
    #              [[29, 1321], [85, 93]], [[1399, 2342, 2611], [104, 103, 130]], [[1402, 2259, 2599], [220, 211, 229]],
    #              [[1395, 2228, 2661], [344, 326, 347]]]
    # surr_poly = [[[0, 500, 500, 0], [0, 0, 500, 500]], [[505, 1005, 1005, 505], [505, 505, 1005, 1005]],
    #              [[10, 490, 490, 10], [10, 10, 490, 490]]]
    #
    # plot(img_path, [baselines], surr_poly)
    # # plot(img_path='', baselines=baselines)

    # path_to_img = "./test/resources/page_test.tif"
    # path_to_xml = "./test/resources/page_test.xml"

    path_to_xml = "./test/resources/newseye_as_test_data/xml_files_gt/19000715_1-0001.xml"
    path_to_img = "./test/resources/newseye_as_test_data/image_files/19000715_1-0001.jpg"

    plot_pagexml(Page(path_to_xml), path_to_img)
