from __future__ import print_function
import numpy as np
from util.geometry import Polygon
import math


def count_rel_hits(poly_to_count, poly_ref, tols):
    """
    Counts the relative hits per tolerance value over all points of the polygon and corresponding
    nearest points of the reference polygon.

    :param poly_to_count: Polygon to count over
    :param poly_ref: reference Polygon
    :param tols: vector of tolerances
    :return: vector of relative hits for every tolerance value
    """
    assert isinstance(poly_to_count, Polygon) and isinstance(poly_ref, Polygon), \
        "poly_to_count and poly_ref have to be Polygons"
    assert type(tols) == np.ndarray, "tols has to be np.ndarray"
    assert len(tols.shape) == 1, "tols has to be 1d vector"
    assert tols.dtype == float, "tols has to be float"

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
            min_dist = min(min_dist, math.fabs(point[0] - point_ref[0]) + math.fabs(point[1] - point_ref[1]))
            if min_dist <= tols[0]:
                break
        for j in range(rel_hits.shape[0]):
            tol = tols[j]
            if min_dist <= tol:
                rel_hits[j] += 1
            elif tol < min_dist < 3.0 * tol:
                rel_hits[j] += (3.0 * tol - min_dist) / (2.0 * tol)

    rel_hits /= poly_to_count.n_points
    return rel_hits


def count_rel_hits_v2(poly_to_count, poly_ref, tols):
    """
    Counts the relative hits per tolerance value over all points of the polygon and corresponding
    nearest points of the reference polygon.

    :param poly_to_count: Polygon to count over
    :param poly_ref: reference Polygon
    :param tols: vector of tolerances
    :return: vector of relative hits for every tolerance value
    """
    assert isinstance(poly_to_count, Polygon) and isinstance(poly_ref, Polygon), \
        "poly_to_count and poly_ref have to be Polygons"
    assert type(tols) == np.ndarray, "tols has to be np.ndarray"
    assert len(tols.shape) == 1, "tols has to be 1d vector"
    assert tols.dtype == float, "tols has to be float"

    poly_to_count_bb = poly_to_count.get_bounding_box()
    poly_ref_bb = poly_ref.get_bounding_box()
    intersection = poly_to_count_bb.intersection(poly_ref_bb)
    rel_hits = np.zeros_like(tols)

    # Early stopping criterion
    if min(intersection.width, intersection.height) < -3.0 * tols[-1]:
        return rel_hits

    # Build and expand numpy arrays from points
    poly_to_count_x = np.array(poly_to_count.x_points)
    poly_to_count_y = np.array(poly_to_count.y_points)
    poly_ref_x = np.expand_dims(np.asarray(poly_ref.x_points), axis=1)
    poly_ref_y = np.expand_dims(np.asarray(poly_ref.y_points), axis=1)
    # poly_ref_x = np.transpose(np.array([poly_ref.x_points]))
    # poly_ref_y = np.transpose(np.array([poly_ref.y_points]))

    # Calculate minimum distances
    dist_x = abs(poly_to_count_x - poly_ref_x)
    dist_y = abs(poly_to_count_y - poly_ref_y)
    min_dist = np.amin(dist_x + dist_y, axis=0)

    # Calculate masks for two tolerance cases
    tols_t = np.expand_dims(np.asarray(tols), axis=1)
    # tols_t = np.transpose(np.array([tols]))
    mask1 = (min_dist <= tols_t).astype(float)
    mask2 = (min_dist <= 3.0 * tols_t).astype(float)
    mask2 = mask2 - mask1

    # Calculate relative hits
    rel_hits = mask1 + mask2 * ((3.0 * tols_t - min_dist) / (2.0 * tols_t))
    rel_hits = np.sum(rel_hits, axis=1)
    rel_hits /= poly_to_count.n_points
    return rel_hits


poly_num1 = 2000
poly_num2 = 1000
num_tols = 10

poly_gt_x = range(poly_num1)
poly_gt_y = range(poly_num1)
poly_gt = Polygon(poly_gt_x, poly_gt_y, len(poly_gt_x))
poly_hypo_x = range(poly_num2)
poly_hypo_y = range(poly_num2, 0, -1)
poly_hypo = Polygon(poly_hypo_x, poly_hypo_y, len(poly_hypo_x))
tolerances = np.arange(num_tols) + 1.0

hits = count_rel_hits(poly_hypo, poly_gt, tolerances)
hits2 = count_rel_hits_v2(poly_hypo, poly_gt, tolerances)
print("hits1\n", hits)
print("hits2\n", hits2)
