# coding=utf-8
from unittest import TestCase
from util import misc
from util.geometry import Polygon


class TestUtil(TestCase):

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

    def test_get_polys_from_file(self):
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
