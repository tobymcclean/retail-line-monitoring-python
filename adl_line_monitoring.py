from shapely.geometry import LineString, box, Polygon

from collections import Counter


def get_polygon(point_list):
    return Polygon(point_list)


def get_box(points_tuple):
    return box(*points_tuple)


def get_line(data):
    return LineString(data)


class LineMonitor:
    def config_env(self):
        line = ((int(self.coords[0][0] * self.width / 100), int(self.coords[0][1] * self.height / 100)),
                (int(self.coords[1][0] * self.width / 100), int(self.coords[1][1] * self.height / 100)))
        line = get_line(line)
        self.polygon = line.buffer(5)
        self.polygon = get_polygon(list(self.polygon.exterior.coords))


    def __init__(self, width, height):
        self.running = True
        self.total_frames = 0
        self.coords = None
        self.results = {}
        self.confidence_threshold = 0.65
        self.polygon = None
        self.line = None
        self.trend = []
        self.most = 0
        self.counter = Counter()
        self.trend_window = 81
        self.width = width
        self.height = height


    def process_boxes(self, boxes):
        count_people = 0
        for box in boxes.data:
            if box.probability > self.confidence_threshold and box.class_label == 'person':
                bbox = get_box(box.x1 * self.width, box.y1 * self.height, box.x2 * self.width, box.y2 * self.height)
                if self.polygon.intersects(bbox):
                    count_people +=1
        return count_people


