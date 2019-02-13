# -*- coding: utf-8 -*-

class Coords:
    def __init__(self, coords_list):
        self.coords_list = coords_list

    def get_coords(self):
        """Convert self.coords_list to a PageXml valid format:
        'x1,y1 x2,y2 ... xN,yN'.

        :return: PageXml valid format of coordinates.
        """
        s = ""
        for pt in self.coords_list:
            if s:
                s += " "
            s += "%s,%s" % (pt[0], pt[1])
        return s


class Region:
    def __init__(self, id, custom, coords):
        self.id = id
        self.custom = custom
        self.coords = coords


class TextRegion(Region):
    def __init__(self, id, custom, coords):
        super().__init__(id, custom, coords)


class TextLine:
    def __init__(self, id, custom, baseline, text):
        self.id = id
        # dictionary of dictionaries, e.g. {'readingOrder':{ 'index':'4' },'structure':{'type':'catch-word'}}
        self.custom = custom
        self.baseline = baseline
        self.text = text

    def get_reading_order(self):
        try:
            return self.custom["readingOrder"]["index"]
        except KeyError:
            # print("Reading order index missing.")
            return None

    def get_article_id(self):
        try:
            return self.custom["structure"]["id"] if self.custom["structure"]["type"] == "article" else None
        except KeyError:
            # print("Article ID missing.")
            return None

    def set_reading_order(self, reading_order):
        try:
            self.custom["readingOrder"]["index"] = str(reading_order)
        except KeyError:
            self.custom["readingOrder"] = {}
            self.custom["readingOrder"]["index"] = str(reading_order)

    def set_article_id(self, article_id):
        try:
            self.custom["structure"]["id"] = str(article_id)
        except KeyError:
            self.custom["structure"] = {}
            self.custom["structure"]["id"] = str(article_id)
        self.custom["structure"]["type"] = "article"


if __name__ == '__main__':
    points = [(1, 2), (3, 4), (5, 6)]
    coords = Coords(points)
    print(coords.get_coords())
