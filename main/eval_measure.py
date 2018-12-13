from __future__ import print_function
import numpy as np
import math

from util.util import norm_poly_dists, calc_tols
from util.measure import BaselineMeasure
from util.geometry import Polygon, Rectangle


class BaselineMeasureEval(object):
    def __init__(self, min_tol=10, max_tol=30, rel_tol=0.25, poly_tick_dist=5):
        """
        Initialize BaselineMeasureEval object.

        :param min_tol: MINIMUM distance tolerance which is not penalized
        :param max_tol: MAXIMUM distance tolerance which is not penalized
        :param rel_tol: fraction of estimated interline distance as tolerance values
        :param poly_tick_dist: desired distance of points of the baseline
        """
        assert type(min_tol) == int and type(max_tol) == int, "min_tol and max_tol have to be ints"
        assert min_tol <= max_tol, "min_tol can't exceed max_tol"
        assert 0.0 < rel_tol <= 1.0, "rel_tol has to be in the range (0,1]"
        assert type(poly_tick_dist) == int, "poly_tick_dist has to be int"

        self.max_tols = np.arange(min_tol, max_tol + 1)
        self.rel_tol = rel_tol
        self.poly_tick_dist = poly_tick_dist
        self.truth_line_tols = None
        self.result = BaselineMeasure()

    def calc_measure_for_page_baseline_polys(self, polys_truth, polys_reco):
        """
        Calculate the BaselinMeasure stats for given truth and reco polygons of
        a single page and adds the results to the BaselineMeasure structure.

        :param polys_truth: list of TRUTH polygons corresponding to a single page
        :param polys_reco: list of RECO polygons corresponding to a single page
        """
        assert type(polys_truth) == list and type(polys_reco) == list, "polys_truth and polys_reco have to lists"
        assert all([isinstance(poly, Polygon) for poly in polys_truth + polys_reco]), \
            "elements of polys_truth and polys_reco have to be Polygons"

        # Normalize baselines, so that poly points have a desired "distance"
        polys_truth_norm = norm_poly_dists(polys_truth, self.poly_tick_dist)
        polys_reco_norm = norm_poly_dists(polys_reco, self.poly_tick_dist)

        # Optionally calculate tolerances
        if self.max_tols[0] < 0:
            tols = calc_tols(polys_truth_norm, self.poly_tick_dist, 250, self.rel_tol)
            self.truth_line_tols = np.expand_dims(tols, axis=1)
        else:
            self.truth_line_tols = np.tile(self.max_tols, [len(polys_truth_norm), 1])

        # For each reco poly calculate the precision values for all tolerances
        precision = self.calc_precision(polys_truth_norm, polys_reco_norm)
        # For each truth_poly calculate the recall values for all tolerances
        recall = self.calc_recall(polys_truth_norm, polys_reco_norm)

        # add results
        self.result.add_per_dist_tol_tick_per_line_precision(precision)
        self.result.add_per_dist_tol_tick_per_line_recall(recall)
        self.truth_line_tols = None

    def calc_precision(self, polys_truth, polys_reco):
        """
        Calculates and returns precision values for given truth and reco polygon for all tolerances.

        :param polys_truth: list of TRUTH polygons
        :param polys_reco: list of RECO polygons
        :return: precision values
        """
        assert type(polys_truth) == list and type(polys_reco) == list, "polys_truth and polys_reco have to be lists"
        assert all([isinstance(poly, Polygon) for poly in polys_truth + polys_reco]), \
            "elements of polys_truth and polys_reco have to be Polygons"

        # precisions [self.max_tols.shape[0], len(polys_reco)]

        # relative hits per tolerance value over all reco and truth polygons
        rel_hits = np.zeros([self.max_tols.shape[0], len(polys_reco), len(polys_truth)], dtype=np.float32)
        for i, poly_reco in enumerate(polys_reco):
            for j, poly_truth in enumerate(polys_truth):
                rel_hits[:, i, j] = self.count_rel_hits(poly_reco, poly_truth, self.truth_line_tols[j])

        # calculate alignment
        # TODO

        precison = None
        return precison

    def count_rel_hits(self, poly_to_count, poly_ref, tols):
        """
        Counts the relative hits per tolerance value over all points of the polygon and corresponding
        nearest points of the reference polygon.

        :param poly_to_count: polygon to count over
        :param poly_ref: reference polygon
        :param tols: vector of tolerances
        :return: vector of relative hits for every tolerance value
        """
        assert isinstance(poly_to_count, Polygon) and isinstance(poly_ref, Polygon),\
            "poly_to_count and poly_ref have to be Polygons"

        poly_to_count_bb = poly_to_count.get_bounding_box()
        poly_ref_bb = poly_ref.get_bounding_box()
        intersection = poly_to_count_bb.intersection(poly_ref_bb)

        rel_hits = np.zeros_like(tols)

        # Early stopping criterion
        if min(intersection.width, intersection.height) < -3.0 * tols[-1]:
            return rel_hits

        # calculate relative hits
        for i, point in enumerate(zip(poly_to_count.x_points, poly_to_count.y_points)):
            min_dist = float("inf")
            # find minimal distance to point in poly_ref
            for point_ref in zip(poly_ref.x_points, poly_ref.y_points):
                # min_dist = min(min_dist, math.sqrt((point[0] - point_ref[0]) * (point[0] - point_ref[0]) +
                #                                    (point[1] - point_ref[1]) * (point[1] - point_ref[1])))
                min_dist = min(min_dist, math.fabs(point[0] - point_ref[0] + math.fabs(point[1] - point_ref[1])))
                if min_dist <= tols[0]:
                    break
            for j in range(tols.shape[0]):
                tol = tols[j]
                if min_dist <= tol:
                    rel_hits[j] += 1
                elif tol < min_dist < 3.0 * tol:
                    rel_hits[j] += (3.0 * tol - min_dist) / (2.0 * tol)

        rel_hits /= poly_to_count.n_points
        return rel_hits



    def calc_recall(self, polys_reco, polys_truth):
        """
        Calculates and returns recall values for given truth and reco polygon for all tolerances.

        :param polys_truth: (normed) TRUTH polygon
        :param polys_reco: (normed) RECO polygon
        :return: recall values
        """
        recall = None
        return recall
