from __future__ import print_function
from argparse import ArgumentParser

from main.eval_measure import BaselineMeasureEval
import util.misc as util


if __name__ == '__main__':
    # argument parser and usage
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

    # command-line arguments
    parser.add_argument('--truth', default='', type=str, metavar="STR",
                        help="truth-files in txt- or lst-format (see usage)")
    parser.add_argument('--reco', default='', type=str, metavar="STR",
                        help="reco-files in txt- or lst-format (see usage)")
    parser.add_argument('--min_tol', default=-1.0, type=float, metavar='FLOAT',
                        help="minimum tolerance value, -1 for dynamic calculation (default: %(default)s)")
    parser.add_argument('--max_tol', default=-1.0, type=float, metavar='FLOAT',
                        help="maximum tolerance value, -1 for dynamic calculation (default: %(default)s)")
    parser.add_argument('--threshold_tf', default=-1.0, type=float, metavar='FLOAT',
                        help="threshold for P- and R-value to make a decision concerning tp, fp, fn, tn."
                             " Should be between 0 and 1, (default: %(default)s - nothing is done)")

    # def str2bool(arg):
    #     return arg.lower() in ('true', 't', '1')
    # parser.add_argument('--use_regions', default=False, nargs='?', const=True, type=str2bool, metavar='BOOL',
    #                     help="only evaluate hypo polygons if they are (partly) contained in region polygons,"
    #                          " if they are available (default: %(default)s)")

    # global flags
    flags = parser.parse_args()

    if not flags.truth and flags.reco:
        print("No arguments given for <truth> or <reco>, exiting. See --help for usage.")
        exit(1)

    # parse input to create truth and reco baseline polygon lists
    list_truth = []
    list_reco = []
    if flags.truth.endswith(".txt"):
        list_truth.append(flags.truth)
    if flags.reco.endswith(".txt"):
        list_reco.append(flags.reco)
    if flags.truth.endswith(".lst") and flags.reco.endswith(".lst"):
        try:
            list_truth = util.load_text_file(flags.truth)
            list_reco = util.load_text_file(flags.reco)
        except IOError:
            raise IOError("Cannot open truth- and/or reco-file.")

    if not (list_truth and list_reco):
        raise ValueError("Truth- and/or reco-file empty.")
    if not (len(list_truth) == len(list_reco)):
        raise ValueError("Same reco- and truth-list length required.")

    poly_pages_truth = []
    poly_pages_reco = []
    num_poly_truth = 0
    num_poly_reco = 0

    for i in range(len(list_truth)):
        # get truth polygons
        try:
            truth_polys_from_file, err = util.get_polys_from_file(list_truth[i])
            if not err:
                poly_pages_truth.append(truth_polys_from_file)
            else:
                print("Error loading: {}, skipping.".format(list_truth[i]))
        except IOError:
            print("Error loading: {}, skipping.".format(list_truth[i]))
        # get reco polygons
        try:
            reco_polys_from_file, err = util.get_polys_from_file(list_reco[i])
            if not err:
                poly_pages_reco.append(reco_polys_from_file)
            else:
                print("Error loading: {}, skipping.".format(list_reco[i]))
        except IOError:
            print("Error loading: {}, skipping.".format(list_reco[i]))
        # count polys
        if poly_pages_truth:
            num_poly_truth += len(poly_pages_truth[i])
        if poly_pages_reco:
            num_poly_reco += len(poly_pages_reco[i])

    # create baseline measure evaluation
    bl_measure_eval = BaselineMeasureEval(flags.min_tol, flags.max_tol)

    # evaluate measure for each page
    for polys_truth, polys_reco in zip(poly_pages_truth, poly_pages_reco):
        bl_measure_eval.calc_measure_for_page_baseline_polys(polys_truth, polys_reco)

    # get the results
    bl_measure = bl_measure_eval.measure

    if flags.threshold_tf > 0.0:
        page_wise_true_false_pos = bl_measure.get_page_wise_true_false_counts_hypo(flags.threshold_tf)
        page_wise_true_false_neg = bl_measure.get_page_wise_true_false_counts_gt(flags.threshold_tf)