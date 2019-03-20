# -*- coding: utf-8 -*-
import os

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

    if event.key == 'r' and "regions" in views:
        for region in views["regions"]:
            is_visible = region.get_visible()
            region.set_visible(not is_visible)
        plt.draw()

    if event.key == 'q':
        print("Terminate..")
        exit(0)

    if event.key == 'h':
        print("Usage:\n"
              "\ti: toggle image\n"
              "\tb: toggle baselines\n"
              "\tp: toggle surrounding polygons\n"
              "\tr: toggle regions\n"
              "\tq: quit\n"
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


def plot_ax(ax=None, img_path='', baselines_list=[], surr_polys=[], bcolors=[], region_list=[], rcolors=[]):
    if ax is None:
        fig, ax = plt.subplots()  # type: # (plt.Figure, plt.Axes)
        fig.canvas.set_window_title(img_path)
    views = {}

    try:
        img_plot = add_image(ax, img_path)
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

    if region_list:
        for i, regions in enumerate(region_list):
            region_collection = add_polygons(ax, regions, rcolors[i], closed=True)
            region_collection.set_visible(False)
            if 'regions' in views:
                views['regions'].append(region_collection)
            else:
                views['regions'] = [region_collection]

    # ax.autoscale_view()

    # Toggle baselines with "b", image with "i", surrounding polygons with "p"
    plt.connect('key_press_event', lambda event: toggle_view(event, views))


def plot_pagexml(page, path_to_img, ax=None, plot_article=True):
    if type(page) == str:
        page = Page(page)
    assert type(page) == Page, f"Type must be Page, got {type(page)} instead."

    # get baselines based on the article id
    article_dict = page.get_article_dict()
    if not article_dict:
        bcolors = []
        blines_list = []
    elif None in article_dict:
        if plot_article:
            bcolors = COLORS[:len(article_dict) - 1] + [DEFAULT_COLOR]
        else:
            bcolors = [DEFAULT_COLOR] * len(article_dict)

        blines_list = [[tline.baseline.points_list for tline in tlines if tline.baseline]
                       for (a_id, tlines) in article_dict.items() if a_id is not None] \
                      + [[tline.baseline.points_list for tline in article_dict[None] if tline.baseline]]
    else:
        if plot_article:
            bcolors = COLORS[:len(article_dict)]
        else:
            bcolors = [DEFAULT_COLOR] * len(article_dict)
        blines_list = [[tline.baseline.points_list for tline in tlines] for tlines in article_dict.values()]

    region_dict = page.get_regions()
    if not region_dict:
        rcolors = []
        region_list = []
    else:
        rcolors = COLORS[:len(region_dict)]
        region_list = [[region.points.points_list for region in regions] for regions in region_dict.values()]

    # get surrounding polygons
    textlines = page.get_textlines()
    surr_polys = [tl.surr_p.points_list for tl in textlines if tl]

    mng = plt.get_current_fig_manager()
    mng.resize(*mng.window.maxsize())
    plot_ax(ax, path_to_img, blines_list, surr_polys, bcolors, region_list, rcolors)


def plot_list(img_lst, hyp_lst, gt_lst=None, plot_article=True, force_equal_names=True):
    if not img_lst:
        print(f"No valid image list found: '{img_lst}'.")
        exit(1)
    if not img_lst.endswith((".lst", ".txt")) and not os.path.isfile(img_lst):
        print(f"Image list doesn't have a valid extension or doesn't exist: '{img_lst}'.")
        exit(1)

    if not hyp_lst:
        print(f"No valid hypothesis list found: '{hyp_lst}'.")
        exit(1)
    if not hyp_lst.endswith((".lst", ".txt")) and not os.path.isfile(hyp_lst):
        print(f"Hypothesis list doesn't have a valid extension or doesn't exist: '{hyp_lst}'.")
        exit(1)

    if not gt_lst:
        print(f"No valid groundtruth list found: '{gt_lst}'")
    elif not gt_lst.endswith((".lst", ".txt")) and not os.path.isfile(gt_lst):
        print(f"Groundtruth list doesn't have a valid extension or doesn't exist: '{gt_lst}'.")

    if gt_lst is not None:
        with open(img_lst, 'r') as img_paths:
            with open(hyp_lst, 'r') as hyp_paths:
                with open(gt_lst, 'r') as gt_paths:
                    for img_path, hyp_path, gt_path in zip(img_paths, hyp_paths, gt_paths):
                        img_path = img_path.strip()
                        hyp_path = hyp_path.strip()
                        gt_path = gt_path.strip()
                        if not img_path.endswith((".jpg", ".jpeg", ".png", ".tif")) and os.path.isfile(img_path):
                            print(f"File '{img_path}' does not have a valid image extension (jpg, jpeg, png, tif) "
                                  f"or is not a file, skipping.")
                            continue
                        if force_equal_names:
                            hyp_page = os.path.basename(hyp_path)
                            gt_page = os.path.basename(gt_path)
                            img_name = os.path.basename(img_path)
                            img_wo_ext = str(img_name.rsplit(".", 1)[0])
                            if hyp_page != img_wo_ext + ".xml":
                                print(f"Hypothesis: Filenames don't match: '{hyp_page}' vs. '{img_wo_ext + '.xml'}'"
                                      f", skipping.")
                                continue
                            if gt_page != img_wo_ext + ".xml":
                                print(f"Groundtruth: Filenames don't match: '{gt_page}' vs. '{img_wo_ext + '.xml'}'"
                                      f", ignoring.")
                                fig, ax = plt.subplots()
                                fig.canvas.set_window_title(img_path)
                                ax.set_title('Hypothesis')

                                # Should be save to use without opening all images of the loop in a different window
                                # The program should wait until one window is closed
                                plot_pagexml(hyp_path, img_path, ax, plot_article)
                            else:
                                fig, (ax1, ax2) = plt.subplots(1, 2)
                                fig.canvas.set_window_title(img_path)
                                ax1.set_title('Hypothesis')
                                ax2.set_title('Groundtruth')

                                plot_pagexml(hyp_path, img_path, ax1, plot_article)
                                plot_pagexml(gt_path, img_path, ax2, plot_article)

                        else:
                            fig, (ax1, ax2) = plt.subplots(1, 2)
                            fig.canvas.set_window_title(img_path)
                            ax1.set_title('Hypothesis')
                            ax2.set_title('Groundtruth')

                            plot_pagexml(hyp_path, img_path, ax1, plot_article)
                            plot_pagexml(gt_path, img_path, ax2, plot_article)

                        plt.show()

    else:
        with open(img_lst, 'r') as img_paths:
            with open(hyp_lst, 'r') as hyp_paths:
                for img_path, hyp_path in zip(img_paths, hyp_paths):
                    img_path = img_path.strip()
                    hyp_path = hyp_path.strip()
                    if not img_path.endswith((".jpg", ".jpeg", ".png", ".tif")) and os.path.isfile(img_path):
                        print(
                            f"File '{img_path}' does not have a valid image extension (jpg, jpeg, png, tif) or is not"
                            f" a file, skipping.")
                        continue
                    if force_equal_names:
                        hyp_page = os.path.basename(hyp_path)
                        img_name = os.path.basename(img_path)
                        img_wo_ext = str(img_name.rsplit(".", 1)[0])
                        if hyp_page != img_wo_ext + ".xml":
                            print(f"Hypothesis: Filenames don't match: '{hyp_page}' vs. '{img_wo_ext + '.xml'}'"
                                  f", skipping.")
                            continue
                    fig, ax = plt.subplots()
                    fig.canvas.set_window_title(img_path)
                    ax.set_title('Hypothesis')

                    plot_pagexml(hyp_path, img_path, ax, plot_article)

                    plt.show()


if __name__ == '__main__':
    # path_to_img = "./test/resources/newseye_as_test_data/image_files/0033_nzz_18120804_0_0_a1_p1_1.tif"
    # path_to_xml = "./test/resources/newseye_as_test_data/xml_files_hy/0033_nzz_18120804_0_0_a1_p1_1.xml"
    #
    # plot_pagexml(Page(path_to_xml), path_to_img, plot_article=True)
    # plt.show()

    path_to_img_lst = "./test/resources/newseye_as_test_data/image_paths.lst"
    path_to_hyp_lst = "./test/resources/newseye_as_test_data/hy_xml_paths.lst"
    path_to_gt_lst = "./test/resources/newseye_as_test_data/gt_xml_paths.lst"

    plot_list(path_to_img_lst, path_to_hyp_lst, None, plot_article=True, force_equal_names=True)
