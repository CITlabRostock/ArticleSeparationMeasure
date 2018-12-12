# coding=utf-8
from unittest import TestCase
from util import util
from util.geometry import Polygon


class TestUtil(TestCase):

    def test_load_text_file(self):
        filename = "./resources/lineReco1.txt"
        res = ["29,80;1321,88", "9,215;506,215;684,199;1139,206",
               "32,329;537,340;621,320;1322,331", "1399,99;2342,98;2611,125",
               "1402,215;2259,206;2599,224", "1395,339;2228,321;2661,342"]

        self.assertEqual(res, util.load_text_file(filename))

    def test_parse_string(self):
        polygon = util.parse_string("1,2;2,3;4,5")
        self.assertEqual(polygon.n_points, 3)
        self.assertEqual(polygon.x_points, [1, 2, 4])
        self.assertEqual(polygon.y_points, [2, 3, 5])

    def test_poly_to_string(self):
        polygon = Polygon()
        polygon.set_polygon([1, 2, 4], [2, 3, 5], 3)
        res = "1,2;2,3;4,5"
        self.assertEqual(res, util.poly_to_string(polygon))

    def test_get_polys_from_file(self):
        poly_file_name = "./resources/lineReco7.txt"
        # poly_file_name = "./resources/lineReco10_withError.txt"
        # poly_file_name = "./resources/lineEmpty.txt"
        polygon1 = Polygon()
        polygon2 = Polygon()
        polygon3 = Polygon()
        polygon1.set_polygon([29, 1321], [80, 88], 2)
        polygon2.set_polygon([9, 506, 684, 1139], [215, 215, 199, 206], 3)
        polygon3.set_polygon([32, 537, 621, 1322], [329, 340, 320, 331], 4)

        p_list, error = util.get_polys_from_file(poly_file_name)
        if p_list is None and len(util.load_text_file(poly_file_name)) > 0:
            print("Skip page..")
            self.assertEqual(error, True)
            self.assertEqual(p_list, None)
            return
        elif p_list is None and len(util.load_text_file(poly_file_name)) == 0:
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
