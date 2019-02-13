# -*- coding: utf-8 -*-

import os
import time
import random
import pickle
from random import shuffle
import util.PAGE as PAGE
import util.dbscan_baseline
import matplotlib.pyplot as plt
from matplotlib import colors as mcolors
from util.plot import add_baselines, add_image


BASECOLORS = mcolors.BASE_COLORS
COLORS = dict(BASECOLORS, **mcolors.CSS4_COLORS)
by_hsv = sorted((tuple(mcolors.rgb_to_hsv(mcolors.to_rgba(color)[:3])), name)
                for name, color in COLORS.items())
COLORS_SORTED = [name for hsv, name in by_hsv]
SEED = 501
random.seed(SEED)
random.shuffle(COLORS_SORTED)

DEFAULT_COLOR = 'grey'

# black is the color for the "other" class (first entry in the "colors" list)
colors = ["black", "darkgreen", "red", "darkviolet", "darkblue",
          "gold", "darkorange", "brown", "yellowgreen", "darkcyan"]

for color in COLORS_SORTED:
    if color not in colors:
        colors.append(color)


def write_txt_from_gtxml(directory_path, other=False):
    """ extract a txt file from the page xml's (ground truth) in a given directory """

    list_of_all_filenames = []

    # get all xml files in the given directotry
    for filename in os.listdir(directory_path):
        list_of_all_filenames.append(filename)

    list_of_all_filenames.sort()
    file_path_txt_object = open(directory_path.replace("xml_files_gt", "txt_files_gt") + "truth.lst", "w")

    for filename in list_of_all_filenames:
        page = PAGE.parse_file(directory_path + filename)
        result_dict = page.get_baseline_text_dict()

        storing_path = directory_path.replace("xml_files_gt", "txt_files_gt") + filename[:-3] + "txt"
        file_path_txt_object.write(storing_path + "\n")

        txt_to_write = ""

        for article_id in result_dict:
            # we don't want to consider the "other" class in the evaluation
            if not other:
                if article_id == "other":
                    continue

            for tpl in result_dict[article_id]:
                string_to_write = ""
                x_points = tpl[1].x_points
                y_points = tpl[1].y_points

                for index, x in enumerate(x_points):
                    if string_to_write == "":
                        string_to_write += str(x) + "," + str(y_points[index])
                    else:
                        string_to_write += ";" + str(x) + "," + str(y_points[index])

                txt_to_write += string_to_write + "\n"

            # blank line to sepearte the articles in the txt file
            txt_to_write += "\n"

        txt_object = open(storing_path, "w")
        txt_object.write(txt_to_write[:-2])


def save_results(result_dict, storing_path_dict, storing_path_txt, image_name, other=False):
    """ save the results of the AS algorithm """

    list_of_articles = []
    txt_to_write = ""

    for article_id in result_dict:

        # storing the pkl file
        added_article = []
        for tpl in result_dict[article_id]:
            added_article.append([tpl[1].x_points, tpl[1].y_points])

        # "other" class has to be the first article in this list
        if article_id == "other":
            list_of_articles.insert(0, added_article)
        else:
            list_of_articles.append(added_article)

        # storing the txt file
        # we don't want to consider the "other" class in the evaluation
        if not other:
            if article_id == "other":
                continue

        for tpl in result_dict[article_id]:
            string_to_write = ""
            x_points = tpl[1].x_points
            y_points = tpl[1].y_points

            for index, x in enumerate(x_points):
                if string_to_write == "":
                    string_to_write += str(x) + "," + str(y_points[index])
                else:
                    string_to_write += ";" + str(x) + "," + str(y_points[index])

            txt_to_write += string_to_write + "\n"

        # blank line to sepearte the articles in the txt file
        txt_to_write += "\n"

    # storing the pkl file
    with open(storing_path_dict + image_name + '.pkl', 'wb') as saver:
        pickle.dump(list_of_articles, saver, protocol=pickle.HIGHEST_PROTOCOL)

    # # storing the txt file
    # txt_object = open(storing_path_txt + image_name + ".txt", "w")
    # txt_object.write(txt_to_write[:-2])
    #
    # # create hypo.lst file
    # list_of_all_filenames = []
    #
    # # get all xml files in the given directotry
    # for filename in os.listdir("./test/resources/newseye_as_test_data/xml_files_gt/"):
    #     list_of_all_filenames.append(filename)
    #
    # list_of_all_filenames.sort()
    # file_path_txt_object = open(storing_path_txt + "hypo.lst", "w")
    #
    # for filename in list_of_all_filenames:
    #     storing_path = storing_path_txt + filename[:-3] + "txt"
    #     file_path_txt_object.write(storing_path + "\n")


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

    for index, article_baselines in enumerate(gt):
        add_baselines(ax, article_baselines, color=colors[index])

    # plot the results of the AS algorithm
    with open(path_hy, 'rb') as loader:
        hypo = pickle.load(loader)

        ax = plt.subplot(1, 2, 2)
        plt.title('Hypotheses')
        add_image(ax, path_image)

        for index, article_baselines in enumerate(hypo):
            add_baselines(ax, article_baselines, color=colors[index])

    plt.show()


if __name__ == '__main__':

    # write_txt_from_gtxml("./test/resources/newseye_as_test_data/xml_files_gt/", other=False)

    COMPUTE_AS = True
    PLOT_GRAPHIC = True

    prefix = './test/resources/newseye_as_test_data/'

    # newspaper france1
    image_name = '19000715_1-0001'
    # image_name = '19000715_1-0002'
    # image_name = '19000715_1-0003'
    path_to_img = prefix + "image_files/" + image_name + ".jpg"

    # newspaper france2
    # image_name = '19420115_1-0001'
    # image_name = '19420115_1-0002'
    # image_name = '19420115_1-0003'
    # path_to_img = prefix + "image_files/" + image_name + ".jpg"

    # newspaper zuerich
    # image_name = '0033_nzz_18120804_0_0_a1_p1_1'
    # image_name = '0034_nzz_18130618_0_0_a1_p1_1'
    # image_name = '0035_nzz_18141004_0_0_a1_p1_1'
    # image_name = '0036_nzz_18150131_0_0_a1_p1_1'
    # path_to_img = prefix + "image_files/" + image_name + ".tif"

    if COMPUTE_AS:
        t = time.time()

        path_to_hy_pagexml = prefix + "xml_files_hy/" + image_name + ".xml"
        page = PAGE.parse_file(path_to_hy_pagexml)
        article_dict = page.get_baseline_text_dict()
        baselines_hyp_polygon_not_normed = article_dict["other"]

        shuffle(baselines_hyp_polygon_not_normed)

        # Initialization of the Clustering - france newspaper
        dbscan_object \
            = util.dbscan_baseline.DBSCANBaselines \
            (baselines_hyp_polygon_not_normed,
             min_polygons_for_cluster=2, des_dist=5, max_d=50, min_polygons_for_article=3,
             rectangle_ratio=1 / 5, rectangle_interline_factor=4 / 2,
             bounding_box_epsilon=5, min_intersect_ratio=2 / 5,
             use_java_code=True)

        # # Initialization of the Clustering - zuerich newspaper
        # dbscan_object \
        #     = util.dbscan_baseline.DBSCANBaselines \
        #     (baselines_hyp_polygon_not_normed,
        #      min_polygons_for_cluster=2, des_dist=5, max_d=50, min_polygons_for_article=3,
        #      rectangle_ratio=1 / 5, rectangle_interline_factor=3 / 2,
        #      bounding_box_epsilon=5, min_intersect_ratio=3 / 5,
        #      use_java_code=True)

        # AS algorithm based on DBSCAN
        dbscan_object.clustering_polygons()
        article_dict = dbscan_object.get_cluster_of_polygons()
        save_results(article_dict, './test/resources/newseye_as_test_data/results_dict_new/',
                     './test/resources/newseye_as_test_data/txt_files_hy/', image_name=image_name, other=False)

        print("Time for the AS algorithm in s: {:.2f}".format(time.time() - t))

    if PLOT_GRAPHIC:
        # ground truth
        path_to_xml_gt = prefix + "xml_files_gt/" + image_name + ".xml"
        # hypothesis
        path_to_dict_hy = prefix + "results_dict_new/" + image_name + ".pkl"

        plot_results(path_to_xml_gt, path_to_dict_hy, path_to_img)
