from __future__ import print_function
import datetime
from argparse import ArgumentParser
import numpy as np

from main.eval_measure import BaselineMeasureEval
import util.misc as util


def greedy_alignment(array):
    assert type(array) == np.ndarray, "array has to be np.ndarray"
    assert len(array.shape) == 2, "array has to be 2d matrix"
    assert array.dtype == float, "array has to be float"

    arr = np.copy(array)
    greedy_alignment = []  # np.zeros([min(*matrix.shape)])
    while True:
        # calculate indices for maximum alignment
        max_idx_x, max_idx_y = np.unravel_index(np.argmax(arr), arr.shape)
        # finish if all elements have been aligned
        if arr[max_idx_x, max_idx_y] < 0:
            break
        # get max alignment
        greedy_alignment.append((max_idx_x, max_idx_y))
        # set row and column to -1
        arr[max_idx_x, :] = -1.0
        arr[:, max_idx_y] = -1.0
    return greedy_alignment


def sum_over_indices(array, index_list):
    assert type(array) == np.ndarray, "array has to be np.ndarray"
    assert type(index_list) == list, "index_list has to be list"
    assert all([type(ele) == list or type(ele) == tuple for ele in index_list]),\
        "elements of index_list have to tuples or lists"
    index_size = len(index_list[0])
    assert all([len(ele) == index_size for ele in index_list]), "indices in index_list have to be of same length"
    assert len(array.shape) == index_size, "array shape and indices have to match"

    res = 0.0
    for index in index_list:
        res += array[index]
    return res


def run_eval(truth_file, reco_file, min_tol, max_tol, threshold_tf):
    if not (truth_file and reco_file):
        print("No arguments given for <truth> or <reco>, exiting. See --help for usage.")
        exit(1)

    # Parse input to create truth and reco baseline polygon lists
    list_truth = []
    list_reco = []
    if truth_file.endswith(".txt"):
        list_truth.append(truth_file)
    if reco_file.endswith(".txt"):
        list_reco.append(reco_file)
    if truth_file.endswith(".lst") and reco_file.endswith(".lst"):
        try:
            list_truth = util.load_text_file(truth_file)
            list_reco = util.load_text_file(reco_file)
        except IOError:
            raise IOError("Cannot open truth- and/or reco-file.")

    if not (list_truth and list_reco):
        raise ValueError("Truth- and/or reco-file empty.")
    if not (len(list_truth) == len(list_reco)):
        raise ValueError("Same reco- and truth-list length required.")

    print("-----Baseline evaluation-----")
    print("")
    print("Evaluation performed on {}".format(datetime.datetime.now().strftime("%Y.%m.%d, %H:%M")))
    print("Evaluation performed for GT: {}".format(truth_file))
    print("Evaluation performed for HYPO: {}".format(reco_file))
    print("Number of pages: {}".format(len(list_truth)))
    print("")
    print("Loading protocol:")

    pages_article_truth = []
    pages_article_reco = []

    num_article_truth = 0
    num_poly_truth = 0
    num_article_reco = 0
    num_poly_reco = 0

    list_truth_fixed = list_truth[:]
    list_reco_fixed = list_reco[:]

    for i in range(len(list_truth)):
        truth_article_polys_from_file = None
        reco_article_polys_from_file = None
        # Get truth polygons
        try:
            truth_article_polys_from_file, error_truth = util.get_article_polys_from_file(list_truth[i])
        except IOError:
            error_truth = True
        # Get reco polygons
        try:
            reco_article_polys_from_file, error_reco = util.get_article_polys_from_file(list_reco[i])
        except IOError:
            error_reco = True

        # Skip pages with errors in either truth or reco
        if not (error_truth or error_reco):
            if truth_article_polys_from_file is not None and reco_article_polys_from_file is not None:
                pages_article_truth.append(truth_article_polys_from_file)
                pages_article_reco.append(reco_article_polys_from_file)
                # Count polys
                num_article_truth += len(truth_article_polys_from_file)
                num_poly_truth += sum(len(polys) for polys in truth_article_polys_from_file)
                num_article_reco += len(reco_article_polys_from_file)
                num_poly_reco += sum(len(polys) for polys in reco_article_polys_from_file)
        else:
            if error_truth:
                print("  Error loading: {}, skipping.".format(list_truth[i]))
            if error_reco:
                print("  Error loading: {}, skipping.".format(list_reco[i]))
            list_truth_fixed.remove(list_truth[i])
            list_reco_fixed.remove(list_reco[i])

    if len(list_truth) == len(list_truth_fixed):
        print("  Everything loaded without errors.")

    print("")
    print("{} out of {} GT-HYPO page pairs loaded without errors and used for evaluation.".format
          (len(list_truth_fixed), len(list_truth)))
    print("Number of GT: {} lines found in {} articles".format(num_poly_truth, num_article_truth))
    print("Number of HYPO: {} lines found in {} articles".format(num_poly_reco, num_article_reco))

    # Evaluate measure for each page
    print("")
    print("Pagewise evaluation:")
    print("")
    print("{:>6s} {:>10s} {:>10s} {:>10s}  {:^30s}  {:^30s}".format(
        "Mode", "P-value", "R-value", "F-value", "TruthFile", "HypoFile"))
    print("-" * (10 + 1 + 10 + 1 + 10 + 1 + 10 + 2 + 30 + 2 + 30))

    for p, page_articles in enumerate(zip(pages_article_truth, pages_article_reco)):
        page_articles_truth = page_articles[0]
        page_articles_reco = page_articles[1]
        # Create precision & recall matrices for article wise comparisons
        page_wise_article_precision = np.zeros([len(page_articles_truth), len(page_articles_reco)])
        page_wise_article_recall = np.zeros([len(page_articles_truth), len(page_articles_reco)])
        # Create baseline measure evaluation
        bl_measure_eval = BaselineMeasureEval(min_tol, max_tol)
        # Evaluate measure for each article
        for i, article_truth in enumerate(page_articles_truth):
            for j, article_reco in enumerate(page_articles_reco):
                bl_measure_eval.calc_measure_for_page_baseline_polys(article_truth, article_reco)
                page_wise_article_precision[i, j] = bl_measure_eval.measure.result.page_wise_precision[-1]
                page_wise_article_recall[i, j] = bl_measure_eval.measure.result.page_wise_recall[-1]

        # Greedy alignment of articles

        # 1) Without article weighting
        # 1.1) Greedy, independant alignment
        greedy_align_precision = greedy_alignment(page_wise_article_precision)
        greedy_align_recall = greedy_alignment(page_wise_article_recall)
        precision = sum_over_indices(page_wise_article_precision, greedy_align_precision)
        precision = precision / len(page_articles_reco)
        recall = sum_over_indices(page_wise_article_recall, greedy_align_recall)
        recall = recall / len(page_articles_truth)
        f_measure = util.f_measure(precision, recall)

        # 1.2) Greedy alignment (map precision alignment to recall)
        precision_p2r = precision
        recall_p2r = sum_over_indices(page_wise_article_recall, greedy_align_precision)
        recall_p2r = recall_p2r / len(page_articles_truth)
        f_measure_p2r = util.f_measure(precision_p2r, recall_p2r)

        # 1.3) Greeday alignment (map recall alignment to precision)
        precision_r2p = sum_over_indices(page_wise_article_precision, greedy_align_recall)
        precision_r2p = precision_r2p / len(page_articles_reco)
        recall_r2p = recall
        f_measure_r2p = util.f_measure(precision_r2p, recall_r2p)

        # 2) With article weighting (based on baseline percentage portion of truth/hypo)
        articles_truth_length = np.asarray([len(l) for l in page_articles_truth], dtype=np.float32)
        articles_reco_length = np.asarray([len(l) for l in page_articles_reco], dtype=np.float32)
        articles_truth_weighting = articles_truth_length / np.sum(articles_truth_length)
        articles_reco_weighting = articles_reco_length / np.sum(articles_reco_length)
        # column-wise weighting for precision
        article_wise_precision_w = page_wise_article_precision * articles_reco_weighting
        # row-wise weighting for recall
        article_wise_recall_w = page_wise_article_recall * np.expand_dims(articles_truth_weighting, axis=1)

        # 2.1) Greedy, independant alignment
        greedy_align_precision_w = greedy_alignment(article_wise_precision_w)
        greedy_align_recall_w = greedy_alignment(article_wise_recall_w)
        precision_w = sum_over_indices(article_wise_precision_w, greedy_align_precision_w)
        recall_w = sum_over_indices(article_wise_recall_w, greedy_align_recall_w)
        f_measure_w = util.f_measure(precision_w, recall_w)

        # 2.2) Greedy alignment (map precision alignment to recall)
        precision_w_p2r = precision_w
        recall_w_p2r = sum_over_indices(article_wise_recall_w, greedy_align_precision_w)
        f_measure_w_p2r = util.f_measure(precision_w_p2r, recall_w_p2r)

        # 2.3) Greeday alignment (map recall alignment to precision)
        precision_w_r2p = sum_over_indices(article_wise_precision_w, greedy_align_recall_w)
        recall_w_r2p = recall_w
        f_measure_w_r2p = util.f_measure(precision_w_r2p, recall_w_r2p)

        print("{:>6s} {:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format(
            "i", precision, recall, f_measure, list_truth_fixed[p], list_reco_fixed[p]))
        print("{:>6s} {:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format(
            "p2r", precision_p2r, recall_p2r, f_measure_p2r, list_truth_fixed[p], list_reco_fixed[p]))
        print("{:>6s} {:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format(
            "r2p", precision_r2p, recall_r2p, f_measure_r2p, list_truth_fixed[p], list_reco_fixed[p]))
        print("{:>6s} {:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format(
            "w, i", precision_w, recall_w, f_measure_w, list_truth_fixed[p], list_reco_fixed[p]))
        print("{:>6s} {:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format(
            "w, p2r", precision_w_p2r, recall_w_p2r, f_measure_w_p2r, list_truth_fixed[p], list_reco_fixed[p]))
        print("{:>6s} {:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format(
            "w, r2p", precision_w_r2p, recall_w_r2p, f_measure_w_r2p, list_truth_fixed[p], list_reco_fixed[p]))
        print("")

    # # Pagewise evaluation
    # print("")
    # print("Pagewise evaluation:")
    # print("{:>10s} {:>10s} {:>10s}  {:^30s}  {:^30s}".format("P-value", "R-value", "F-value", "TruthFile", "HypoFile"))
    # print("-" * (10+1+10+1+10+2+30+2+30))
    # for i in range(len(list_truth_fixed)):
    #     page_precision = bl_measure.result.page_wise_precision[i]
    #     page_recall = bl_measure.result.page_wise_recall[i]
    #     page_f_value = util.f_measure(page_precision, page_recall)
    #     print("{:>10.4f} {:>10.4f} {:>10.4f}  {}  {}".format
    #           (page_precision, page_recall, page_f_value, list_truth_fixed[i], list_reco_fixed[i]))

    # # Final evaluation
    # print("")
    # print("---Final evaluation---")
    # print("")
    # print("Average (over pages) P-value: {:.4f}".format(bl_measure.result.precision))
    # print("Average (over pages) R-value: {:.4f}".format(bl_measure.result.recall))
    # print("Resultung F1-score: {:.4f}".format(util.f_measure(bl_measure.result.precision, bl_measure.result.recall)))
    # print("")
    #
    # # Global tp, fp, fn, tn for given threshold
    # if threshold_tf > 0.0:
    #     page_wise_true_false_pos = bl_measure.get_page_wise_true_false_counts_hypo(threshold_tf)
    #     page_wise_true_false_neg = bl_measure.get_page_wise_true_false_counts_gt(threshold_tf)
    #     true_pos = 0
    #     false_pos = 0
    #     true_neg = 0
    #     false_neg = 0
    #     for i in range(page_wise_true_false_pos.shape[1]):
    #         true_pos += page_wise_true_false_pos[0, i]
    #         false_pos += page_wise_true_false_pos[1, i]
    #         true_neg += page_wise_true_false_neg[0, i]
    #         false_neg += page_wise_true_false_neg[1, i]
    #     print("Number of true hypothesis lines for average P-value threshold of {} is {}".format
    #           (threshold_tf, true_pos))
    #     print("Number of false hypothesis lines for average P-value threshold of {} is {}".format
    #           (threshold_tf, false_pos))
    #     print("Number of true groundtruth lines for average R-value threshold of {} is {}".format
    #           (threshold_tf, true_neg))
    #     print("Number of false groundtruth lines for average R-value threshold of {} is {}".format
    #           (threshold_tf, false_neg))
    #     print("")


if __name__ == '__main__':
    # Argument parser and usage
    usage_string = """%(prog)s <truth> <reco> [OPTIONS]
    You can add specific options via '--OPTION VALUE'
    This method calculates the baseline errors in a precision/recall manner.
    As input it requires the truth and reco information.
    A basic truth (and reco) file corresponding to a page has to be a txt-file,
    where every line corresponds to a baseline polygon and should look like:
    x1,y1;x2,y2;x3,y3;...;xn,yn.
    As arguments (truth, reco) such txt-files OR lst-files (containing a path to
    a basic txt-file per line) are required. For lst-files, the order of the
    truth/reco-files in both lists has to be identical."""
    parser = ArgumentParser(usage=usage_string)

    # Command-line arguments
    parser.add_argument('--truth', default='', type=str, metavar="STR",
                        help="truth-files in txt- or lst-format (see usage)")
    parser.add_argument('--reco', default='', type=str, metavar="STR",
                        help="reco-files in txt- or lst-format (see usage)")
    parser.add_argument('--min_tol', default=-1, type=int, metavar='FLOAT',
                        help="minimum tolerance value, -1 for dynamic calculation (default: %(default)s)")
    parser.add_argument('--max_tol', default=-1, type=int, metavar='FLOAT',
                        help="maximum tolerance value, -1 for dynamic calculation (default: %(default)s)")
    parser.add_argument('--threshold_tf', default=-1.0, type=float, metavar='FLOAT',
                        help="threshold for P- and R-value to make a decision concerning tp, fp, fn, tn."
                             " Should be between 0 and 1, (default: %(default)s - nothing is done)")

    # def str2bool(arg):
    #     return arg.lower() in ('true', 't', '1')
    # parser.add_argument('--use_regions', default=False, nargs='?', const=True, type=str2bool, metavar='BOOL',
    #                     help="only evaluate hypo polygons if they are (partly) contained in region polygons,"
    #                          " if they are available (default: %(default)s)")

    # Run evaluation
    flags = parser.parse_args()
    run_eval(flags.truth, flags.reco, flags.min_tol, flags.max_tol, flags.threshold_tf)

