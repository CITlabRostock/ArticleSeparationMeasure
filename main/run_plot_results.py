# -*- coding: utf-8 -*-

import random
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors

import util.PAGE as PAGE
from util.plot import add_baselines, add_image


BASECOLORS = mcolors.BASE_COLORS
COLORS = dict(BASECOLORS, **mcolors.CSS4_COLORS)
by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name) for name, color in COLORS.items())
COLORS_SORTED = [name for hsv, name in by_hsv]
SEED = 501
random.seed(SEED)
random.shuffle(COLORS_SORTED)

DEFAULT_COLOR = 'grey'

# black is the color for the "other" class (first entry in the "colors" list)
colors = ["black",

          "darkgreen", "red", "darkviolet", "darkblue",
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
    if color not in colors:
        colors.append(color)


def plot_results(path_gt, path_hy, path_image):
    """ plot the results of the AS algorithm in comparision with the GT """

    # plot the GT data
    page = PAGE.parse_file(path_gt)
    gt_dict = page.get_baseline_text_dict()

    gt = []
    for article_id in gt_dict:

        added_article = []
        for tpl in gt_dict[article_id]:
            added_article.append([tpl[1].x_points, tpl[1].y_points])

        # "other" class has to be the first article in this list
        if article_id == "other":
            gt.insert(0, added_article)
        else:
            gt.append(added_article)

    ax = plt.subplot(1, 2, 1)
    plt.title('Ground Truth')
    add_image(ax, path_image)

    try:
        for i, article_baselines in enumerate(gt):
            add_baselines(ax, article_baselines, color=colors[i])
    except IndexError:
        print("Plot isn't complete since too many articles!\n")
        plt.show()
        return

    # plot the HY data
    page = PAGE.parse_file(path_hy)
    hy_dict = page.get_baseline_text_dict()

    hy = []
    for article_id in hy_dict:

        added_article = []
        for tpl in hy_dict[article_id]:
            added_article.append([tpl[1].x_points, tpl[1].y_points])

        # "other" class has to be the first article in this list
        if article_id == "other":
            hy.insert(0, added_article)
        else:
            hy.append(added_article)

    ax = plt.subplot(1, 2, 2)
    plt.title('Hypotheses')
    add_image(ax, path_image)

    try:
        for i, article_baselines in enumerate(hy):
            add_baselines(ax, article_baselines, color=colors[i])
    except IndexError:
        print("Plot isn't complete since too many articles!\n")
        plt.show()
        return

    plt.show()


if __name__ == '__main__':

    image_files_path_list = "./test/resources/newseye_as_test_data/image_paths.lst"
    gt_files_path_list = "./test/resources/newseye_as_test_data/gt_xml_paths.lst"
    hy_files_path_list = "./test/resources/newseye_as_test_data/hy_xml_paths.lst"

    # image_files_path_list = "../../Le_Matin_Set/image_paths.lst"
    # gt_files_path_list = "../../Le_Matin_Set/gt_xml_paths.lst"
    # hy_files_path_list = "../../Le_Matin_Set/hy_xml_paths.lst"

    image_paths = [line.rstrip('\n') for line in open(image_files_path_list, "r")]
    gt_pagexml_paths = [line.rstrip('\n') for line in open(gt_files_path_list, "r")]
    hy_pagexml_paths = [line.rstrip('\n') for line in open(hy_files_path_list, "r")]

    for index, path_to_image in enumerate(image_paths):

        name_image = path_to_image.split("/")[-1][:-3]
        name_gt = gt_pagexml_paths[index].split("/")[-1][:-3]
        name_hy = hy_pagexml_paths[index].split("/")[-1][:-3]

        if name_image != name_gt or name_image != name_hy or name_gt != name_hy:
            print("No match of the file paths!")
            continue

        path_to_gt_pagexml = gt_pagexml_paths[index]
        path_to_hy_pagexml = hy_pagexml_paths[index]

        plot_results(path_to_gt_pagexml, path_to_hy_pagexml, path_to_image)

    # # plot examples of one special newspaper page
    # path_to_image = "../../Le_Matin_Set/Transkribus_Data/121157/Le_Matin_18840315_1/18840315_1-0001.jpg"
    # path_to_gt_pagexml = "../../Le_Matin_Set/Transkribus_Data/121157/Le_Matin_18840315_1/page/18840315_1-0001.xml"
    # path_to_hy_pagexml = "../../Le_Matin_Set/Hypotheses_Data/18840315_1-0001.xml"

    # path_to_image = "../../Le_Matin_Set/Transkribus_Data/121157/Le_Matin_18840315_1/18840315_1-0002.jpg"
    # path_to_gt_pagexml = "../../Le_Matin_Set/Transkribus_Data/121157/Le_Matin_18840315_1/page/18840315_1-0002.xml"
    # path_to_hy_pagexml = "../../Le_Matin_Set/Hypotheses_Data/18840315_1-0002.xml"

    # path_to_image = "../../Le_Matin_Set/Transkribus_Data/121167/Le_Matin_18900115_1/18900115_1-0003.jpg"
    # path_to_gt_pagexml = "../../Le_Matin_Set/Transkribus_Data/121167/Le_Matin_18900115_1/page/18900115_1-0003.xml"
    # path_to_hy_pagexml = "../../Le_Matin_Set/Hypotheses_Data/18900115_1-0003.xml"
    #
    # plot_results(path_to_gt_pagexml, path_to_hy_pagexml, path_to_image)
