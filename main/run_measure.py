from __future__ import print_function
import datetime
from argparse import ArgumentParser

from main.eval_measure import BaselineMeasureEval
import util.misc as util


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

    poly_pages_truth = []
    poly_pages_reco = []

    num_poly_truth = 0
    num_poly_reco = 0

    list_truth_fixed = list_truth[:]
    list_reco_fixed = list_reco[:]

    for i in range(len(list_truth)):
        truth_polys_from_file = None
        reco_polys_from_file = None
        # Get truth polygons
        try:
            truth_polys_from_file, error_truth = util.get_polys_from_file(list_truth[i])
        except IOError:
            error_truth = True
        # Get reco polygons
        try:
            reco_polys_from_file, error_reco = util.get_polys_from_file(list_reco[i])
        except IOError:
            error_reco = True

        # Skip pages with errors in either truth or reco
        if not (error_truth or error_reco):
            if truth_polys_from_file is not None and reco_polys_from_file is not None:
                poly_pages_truth.append(truth_polys_from_file)
                poly_pages_reco.append(reco_polys_from_file)
                # Count polys
                num_poly_truth += len(truth_polys_from_file)
                num_poly_reco += len(reco_polys_from_file)
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
    print("Number of GT lines: {}".format(num_poly_truth))
    print("Number of HYPO lines: {}".format(num_poly_reco))

    # Create baseline measure evaluation
    bl_measure_eval = BaselineMeasureEval(min_tol, max_tol)

    # Evaluate measure for each page
    for polys_truth, polys_reco in zip(poly_pages_truth, poly_pages_reco):
        bl_measure_eval.calc_measure_for_page_baseline_polys(polys_truth, polys_reco)

    # Get the results
    bl_measure = bl_measure_eval.measure

    # Pagewise evaluation
    print("")
    print("Pagewise evaluation:")
    print("{:>10s},{:>10s},{:>10s},{:>30s},{:>30s}".format("P-value", "R-value", "F-value", "TruthFile", "HypoFile"))
    for i in range(len(list_truth_fixed)):
        page_recall = bl_measure.result.page_wise_recall[i]
        page_precision = bl_measure.result.page_wise_precision[i]
        page_f_value = util.f_measure(page_precision, page_recall)
        print("{:>10.4f} {:>10.4f} {:>10.4f} {},{}".format
              (page_recall, page_precision, page_f_value, list_truth_fixed[i], list_reco_fixed[i]))

    # Final evaluation
    print("")
    print("---Final evaluation---")
    print("")
    print("Average (over pages) P-value: {}".format(bl_measure.result.precision))
    print("Average (over pages) R-value: {}".format(bl_measure.result.recall))
    print("Resultung F1-score: {}".format(util.f_measure(bl_measure.result.precision, bl_measure.result.recall)))
    print("")

    # Global tp, fp, fn, tn for given threshold
    if threshold_tf > 0.0:
        page_wise_true_false_pos = bl_measure.get_page_wise_true_false_counts_hypo(threshold_tf)
        page_wise_true_false_neg = bl_measure.get_page_wise_true_false_counts_gt(threshold_tf)
        true_pos = 0
        false_pos = 0
        true_neg = 0
        false_neg = 0
        for i in range(page_wise_true_false_pos.shape[1]):
            true_pos += page_wise_true_false_pos[0, i]
            false_pos += page_wise_true_false_pos[1, i]
            true_neg += page_wise_true_false_neg[0, i]
            false_neg += page_wise_true_false_neg[1, i]
        print("Number of true hypothesis lines for average P-value threshold of {} is {}".format
              (threshold_tf, true_pos))
        print("Number of false hypothesis lines for average P-value threshold of {} is {}".format
              (threshold_tf, false_pos))
        print("Number of true groundtruth lines for average R-value threshold of {} is {}".format
              (threshold_tf, true_neg))
        print("Number of false groundtruth lines for average R-value threshold of {} is {}".format
              (threshold_tf, false_neg))
        print("")


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

    # Global flags
    flags = parser.parse_args()

    # Run evaluation
    run_eval(flags.truth, flags.reco, flags.min_tol, flags.max_tol, flags.threshold_tf)

