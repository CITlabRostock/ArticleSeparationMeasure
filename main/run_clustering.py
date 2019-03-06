# -*- coding: utf-8 -*-

import jpype
from argparse import ArgumentParser

from util.xmlformats import Page
from util import dbscan_baseline


def get_data_from_pagexml(path_to_pagexml):
    """

    :param path_to_pagexml: file path
    :return: a list of tuples (text of text line, baseline of text line)
    """
    # load the page xml file
    page_file = Page.Page(path_to_pagexml)
    # get all text lines of the loaded page file
    list_of_txt_lines = page_file.get_textlines()

    list_of_text = []
    list_of_polygons = []

    for txt_line in list_of_txt_lines:
        # get the text of the text line
        list_of_text.append(txt_line.text)
        # get the baseline of the text line as polygon
        list_of_polygons.append(txt_line.baseline.to_polygon())

    list_of_tuples = [(list_of_text[i], list_of_polygons[i]) for i in range(len(list_of_text))]

    return list_of_tuples


def save_results_in_pagexml(path_to_pagexml, list_of_txt_line_labels):
    """

    :param path_to_pagexml:
    :param list_of_txt_line_labels:
    """
    page_file = Page.Page(path_to_pagexml)
    # get all text lines of the loaded page file
    list_of_txt_lines = page_file.get_textlines()

    for txt_line_index, txt_line in enumerate(list_of_txt_lines):
        if list_of_txt_line_labels[txt_line_index] == -1:
            continue
        txt_line.set_article_id("a" + str(list_of_txt_line_labels[txt_line_index]))

    page_file.set_textline_attr(list_of_txt_lines)
    page_file.write_page_xml(path_to_pagexml)


def cluster_baselines_dbscan(data, min_polygons_for_cluster=2, des_dist=5, max_d=50, min_polygons_for_article=3,
                             rectangle_ratio=1 / 5, rectangle_interline_factor=3 / 2,
                             bounding_box_epsilon=5, min_intersect_ratio=3 / 5,
                             use_java_code=True):
    """

    :param data: list of tuples ("String", Polygon) as the dataset
    :param min_polygons_for_cluster: minimum number of required polygons forming a cluster
    :param des_dist: desired distance (measured in pixels) of two adjacent pixels in the normed polygons
    :param max_d: maximum distance (measured in pixels) for the calculation of the interline distances
    :param min_polygons_for_article: minimum number of required polygons forming an article

    :param rectangle_ratio: ratio between the width and the height of the rectangles
    :param rectangle_interline_factor: multiplication factor to calculate the height of the rectangles with the help
                                       of the interline distances
    :param bounding_box_epsilon: additional width and height value to calculate the bounding boxes of the polygons
                                 during the clustering progress
    :param min_intersect_ratio: minimum threshold for the intersection being necessary to determine, whether two
                                polygons are clustered together or not

    :param use_java_code: usage of methods written in java or not
    :return: list with article labels for each data tuple (i.e. for each text line)
    """
    # initialization of the clustering algorithm object
    cluster_object \
        = dbscan_baseline.DBSCANBaselines \
        (data, min_polygons_for_cluster=min_polygons_for_cluster, des_dist=des_dist, max_d=max_d,
         min_polygons_for_article=min_polygons_for_article, rectangle_ratio=rectangle_ratio,
         rectangle_interline_factor=rectangle_interline_factor, bounding_box_epsilon=bounding_box_epsilon,
         min_intersect_ratio=min_intersect_ratio, use_java_code=use_java_code)

    # AS algorithm based on DBSCAN
    cluster_object.clustering_polygons()
    article_list = cluster_object.get_cluster_of_polygons()

    return article_list


if __name__ == "__main__":
    parser = ArgumentParser()

    # Command-line arguments
    parser.add_argument('--path_to_xml_lst', default='', type=str, metavar="STR",
                        help="path to the lst file containing the file paths of the PageXmls")

    # start java virtual machine to be able to execute the java code
    jpype.startJVM(jpype.getDefaultJVMPath())

    # # example with Command-line arguments
    # flags = parser.parse_args()
    # hypo_files_paths_list = flags.path_to_xml_lst
    # hypo_files = [line.rstrip('\n') for line in open(hypo_files_paths_list, "r")]

    hypo_files_paths_list = "./test/resources/newseye_as_test_data/hy_xml_paths.lst"
    # hypo_files_paths_list = "../../Le_Matin_Set/hy_xml_paths.lst"
    hypo_files = [line.rstrip('\n') for line in open(hypo_files_paths_list, "r")]

    for counter, hypo_file in enumerate(hypo_files):
        print(hypo_file)

        data = get_data_from_pagexml(hypo_file)

        article_id_list = cluster_baselines_dbscan(data)

        save_results_in_pagexml(hypo_file, article_id_list)

        print("Progress: {:.2f} %".format(((counter + 1) / len(hypo_files)) * 100))

    # shut down the java virtual machine
    jpype.shutdownJVM()