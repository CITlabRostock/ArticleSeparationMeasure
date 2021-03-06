# coding=utf-8

from __future__ import division
from __future__ import print_function
from __future__ import absolute_import

import math
from unittest import TestCase
from util import misc
from util.geometry import Polygon, Rectangle


class TestMisc(TestCase):

    def test_load_text_file(self):
        filename = "./resources/lineReco1.txt"
        res = ["29,80;1321,88", "9,215;506,215;684,199;1139,206",
               "32,329;537,340;621,320;1322,331", "1399,99;2342,98;2611,125",
               "1402,215;2259,206;2599,224", "1395,339;2228,321;2661,342"]

        self.assertEqual(res, misc.load_text_file(filename))

    def test_parse_string(self):
        polygon = misc.parse_string("1,2;2,3;4,5")
        self.assertEqual(polygon.n_points, 3)
        self.assertEqual(polygon.x_points, [1, 2, 4])
        self.assertEqual(polygon.y_points, [2, 3, 5])

    def test_poly_to_string(self):
        polygon = Polygon([1, 2, 4], [2, 3, 5], 3)
        res = "1,2;2,3;4,5"
        self.assertEqual(res, misc.poly_to_string(polygon))

    def test_get_polys_from_file_txt(self):
        poly_file_name = "./resources/lineReco7.txt"
        # poly_file_name = "./resources/lineReco10_withError.txt"
        # poly_file_name = "./resources/lineEmpty.txt"
        polygon1 = Polygon([29, 1321], [80, 88], 2)
        polygon2 = Polygon([9, 506, 684, 1139], [215, 215, 199, 206], 3)
        polygon3 = Polygon([32, 537, 621, 1322], [329, 340, 320, 331], 4)

        p_list, error = misc.get_polys_from_file(poly_file_name)
        if p_list is None and len(misc.load_text_file(poly_file_name)) > 0:
            print("Skip page..")
            self.assertEqual(error, True)
            self.assertEqual(p_list, None)
            return
        elif p_list is None and len(misc.load_text_file(poly_file_name)) == 0:
            print("Empty text file..")
            self.assertEqual(error, False)
            self.assertEqual(p_list, None)
            return

        [p1, p2, p3] = p_list

        self.assertEqual(polygon1.x_points, p1.x_points)
        self.assertEqual(polygon2.x_points, p2.x_points)
        self.assertEqual(polygon3.x_points, p3.x_points)

        self.assertEqual(polygon1.y_points, p1.y_points)
        self.assertEqual(polygon2.y_points, p2.y_points)
        self.assertEqual(polygon3.y_points, p3.y_points)

        self.assertEqual(error, False)

    # TODO: add a toy example for loading a PAGEXML file
    def test_polys_from_file_xml(self):
        poly_file_name = "./resources/page_test.xml"
        p_list, error = misc.get_polys_from_file(poly_file_name)
        print(len(p_list))


    def test_blow_up(self):
        poly_in = Polygon([0, 3, 4, 5, 7, 5], [1, 3, 5, 3, 1, 0], 6)
        poly_out = misc.blow_up(poly_in)
        res = Polygon([0, 1, 2, 3, 4, 4, 5, 5, 6, 7, 6, 5], [1, 2, 2, 3, 4, 5, 4, 3, 2, 1, 1, 0], 12)

        self.assertEqual(res.x_points, poly_out.x_points)
        self.assertEqual(res.y_points, poly_out.y_points)
        self.assertEqual(res.n_points, 12)

    def test_thin_out(self):
        poly_in1 = Polygon([0, 1, 2, 3, 4, 4, 5, 5, 6, 7, 6, 5], [1, 2, 2, 3, 4, 5, 4, 3, 2, 1, 1, 0], 12)
        des_dist_1 = 1  # no changes
        des_dist_2 = 2  # distance of 2
        des_dist_100 = 100  # just consider min points (=20)

        poly1_1 = misc.thin_out(poly_in1, des_dist_1)
        poly1_2 = misc.thin_out(poly_in1, des_dist_2)
        poly1_100 = misc.thin_out(poly_in1, des_dist_100)

        for poly in [poly1_1, poly1_2, poly1_100]:
            self.assertEqual(poly_in1.x_points, poly.x_points)
            self.assertEqual(poly_in1.y_points, poly.y_points)
            self.assertEqual(poly_in1.n_points, poly.n_points)

        poly_in2 = Polygon()
        for (x, y) in zip(range(60), range(60)):
            poly_in2.add_point(x, y)

        poly2_1 = misc.thin_out(poly_in2, des_dist_1)
        poly2_2 = misc.thin_out(poly_in2, des_dist_2)
        poly2_100 = misc.thin_out(poly_in2, des_dist_100)

        self.assertEqual(poly_in2.x_points, poly2_1.x_points)
        self.assertEqual(poly_in2.y_points, poly2_1.y_points)
        self.assertEqual(poly_in2.n_points, poly2_1.n_points)

        self.assertEqual(range(0, 58, 2) + [59], poly2_2.x_points)
        self.assertEqual(range(0, 58, 2) + [59], poly2_2.y_points)
        self.assertEqual(30, poly2_2.n_points)

        self.assertEqual(range(0, 30, 3) + range(31, 57, 3) + [59], poly2_100.x_points)
        self.assertEqual(range(0, 30, 3) + range(31, 57, 3) + [59], poly2_100.y_points)
        self.assertEqual(20, poly2_100.n_points)

    def test_norm_poly_dists(self):
        des_dist = 2
        # Should not be changed (n_points <= 20 after blow_up)
        polygon1 = Polygon(range(20), range(20), 20)
        res1 = polygon1
        # Should be changed, s.t. the normed polygon has 20 (nearly equidistant) pixels
        polygon2 = Polygon(range(30), range(30), 30)
        res2 = Polygon([0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25, 27, 29],
                       [0, 1, 3, 4, 6, 7, 9, 10, 12, 13, 15, 16, 18, 19, 21, 22, 24, 25, 27, 29], 20)
        # Should not be changed, since des_dist = 2
        polygon3 = Polygon(range(0, 40, 2), range(0, 40, 2), 20)
        res3 = polygon3
        # Should be changed, s.t. every two pixels have a distance of des_dist = 2 (except for the last two pixels)
        polygon4 = Polygon(range(0, 90, 3), range(0, 90, 3), 30)
        res4 = Polygon(range(0, 86, 2) + [87], range(0, 86, 2) + [87], 44)

        poly_list = [polygon1, polygon2, polygon3, polygon4]

        normed_poly_list = misc.norm_poly_dists(poly_list, des_dist)
        res_list = [res1, res2, res3, res4]

        for normed_poly, res in zip(normed_poly_list, res_list):
            self.assertEqual(res.x_points, normed_poly.x_points)
            self.assertEqual(res.y_points, normed_poly.y_points)
            self.assertEqual(res.n_points, normed_poly.n_points)

    def test_calc_reg_line_stats(self):
        # We consider the negative y-values (since we handle computer vision problems..)
        # angle = 0°, n = 0.0
        polygon1 = Polygon(range(5), [0] * 5, 5)
        angle1, n1 = misc.calc_reg_line_stats(polygon1)

        # angle = 315°, n = 0.0
        polygon2 = Polygon(range(5), range(5), 5)
        angle2, n2 = misc.calc_reg_line_stats(polygon2)

        # angle = 306°, n = -11/13
        polygon3 = Polygon([0, 1, 2, 2, 3], [1, 2, 3, 4, 5], 5)
        angle3, n3 = misc.calc_reg_line_stats(polygon3)

        # angle ~ 354°, n = -2,3
        polygon4 = Polygon([0, 1, 2, 2, 3, 4], [1, 2, 3, 4, 5, 0], 6)
        angle4, n4 = misc.calc_reg_line_stats(polygon4)

        # Example where -math.pi / 2 < angle <= -math.pi / 4 and poly.y_points[0] > poly.y_points[-1]
        polygon5 = Polygon(range(100), range(0, 198, 2) + [-1], 100)
        angle5, n5 = misc.calc_reg_line_stats(polygon5)

        # Line y = 0 -> n = 0.0 and angle = 0.0
        self.assertEqual(0.0, angle1)
        self.assertEqual(0.0, n1)
        # Line y = -x -> n = 0.0 and angle = -pi/4 + 7*pi/4
        self.assertEqual(7 * math.pi / 4, angle2)
        self.assertEqual(0.0, n2)
        # Line y = -35/26*x - 11/13 -> n = -11/13 and angle = -0.931882342 + 2*pi
        self.assertAlmostEqual(-0.931882342 + 2 * math.pi, angle3, places=8)
        self.assertAlmostEqual(-11 / 13, n3, places=8)
        # Line y = -0.1*x - 2.3 -> n = -2.3 and angle = -0.0996686525 + 2*pi
        self.assertAlmostEqual(-0.0996686525 + 2 * math.pi, angle4, places=8)
        self.assertEqual(-2.3, n4)
        # Line y = -1.8817821782*x - 3.86178217822 -> n = -3.86178217822 and angle = -1.08233671731 + pi
        self.assertAlmostEqual(-1.08233671731 + math.pi, angle5, places=8)
        self.assertAlmostEqual(-3.86178217822, n5, places=8)

    def test_get_dist_fast(self):
        bb = Rectangle(0, 0, 10, 10)
        p_list = [[x, y] for x in [-1, 5, 11] for y in [-1, 5, 11]]
        dist_list = []
        for p in p_list:
            dist_list += [misc.get_dist_fast(p, bb)]
        self.assertEqual(2, dist_list[0])
        self.assertEqual(1, dist_list[1])
        self.assertEqual(2, dist_list[2])
        self.assertEqual(1, dist_list[3])
        self.assertEqual(0, dist_list[4])
        self.assertEqual(1, dist_list[5])
        self.assertEqual(2, dist_list[6])
        self.assertEqual(1, dist_list[7])
        self.assertEqual(2, dist_list[8])

    def test_get_in_dist(self):
        points1 = [[1, 1], [0, 0]]
        points2 = [[2, 0], [0, 0]]
        or_vec1 = [1, 0]
        or_vec2 = [1 / math.sqrt(2), 1 / math.sqrt(2)]
        in_dist1 = misc.get_in_dist(points1[0], points1[1], or_vec1[0], or_vec1[1])
        in_dist2 = misc.get_in_dist(points2[0], points2[1], or_vec2[0], or_vec2[1])
        in_dist3 = misc.get_in_dist(points1[1], points1[0], or_vec1[0], or_vec1[1])
        in_dist4 = misc.get_in_dist(points2[1], points2[0], or_vec2[0], or_vec2[1])

        self.assertEqual(1, in_dist1)
        self.assertAlmostEqual(math.sqrt(2), in_dist2, places=8)
        self.assertEqual(-1, in_dist3)
        self.assertAlmostEqual(-math.sqrt(2), in_dist4, places=8)

    def test_get_off_dist(self):
        points1 = [[1, 1], [0, 0]]
        points2 = [[2, 0], [0, 0]]
        or_vec1 = [1, 0]
        or_vec2 = [1 / math.sqrt(2), 1 / math.sqrt(2)]
        in_dist1 = misc.get_off_dist(points1[0], points1[1], or_vec1[0], or_vec1[1])
        in_dist2 = misc.get_off_dist(points2[0], points2[1], or_vec2[0], or_vec2[1])
        in_dist3 = misc.get_off_dist(points1[1], points1[0], or_vec1[0], or_vec1[1])
        in_dist4 = misc.get_off_dist(points2[1], points2[0], or_vec2[0], or_vec2[1])

        self.assertEqual(1, in_dist1)
        self.assertAlmostEqual(math.sqrt(2), in_dist2, places=8)
        self.assertEqual(-1, in_dist3)
        self.assertAlmostEqual(-math.sqrt(2), in_dist4, places=8)

    def test_calc_tols(self):
        pass

    def test_f_measure(self):
        pass
