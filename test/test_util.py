# coding=utf-8
from unittest import TestCase
from util import util


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
        self.assertEqual(polygon.x_points, [1,2,4])
        self.assertEqual(polygon.y_points, [2,3,5])