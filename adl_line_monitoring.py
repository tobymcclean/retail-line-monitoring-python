import logging as log
from shapely.geometry import LineString, box, Polygon

from collections import Counter, namedtuple
from adl_map import Map

from adl_edge_iot.datariver.things.edge_thing import EdgeThing
from adl_edge_iot.datariver.utils import write_tag
from adlinktech.datariver import class_from_thing_input, class_from_thing_output, as_nvp_seq, as_native_class
from adlinktech.datariver import FlowState

from rx.subject import Subject

CountData = namedtuple('CountData', ['flow_id', 'count'])

tag_to_value_property_map = {
    'obj_id': 'int32',
    'obj_label': 'string',
    'class_id': 'int32',
    'class_label': 'string',
    'x1':'float32',
    'y1':'float32',
    'x2':'float32',
    'y2':'float32',
    'probability':'float32',
    'meta':'string',
    'dist_x':'float64',
    'dist_y':'float64',
    'dist_z':'float64'
}

def get_polygon(point_list):
    return Polygon(point_list)


def get_box(points_tuple):
    return box(*points_tuple)


def get_line(data):
    return LineString(data)


class LineMonitor(EdgeThing):
    def __init__(self, width, height, class_id, class_label, coords,
                 config_uri: str = '',
                 properties_str: str = '',
                 tag_group_dir: str = './definitions/TagGroup',
                 thing_class_dir: str = './definitions/ThingClass',
                 tag_groups: tuple = tuple(),
                 thing_cls: tuple = tuple()):
        super().__init__(config_uri, properties_str, tag_group_dir, thing_class_dir, tag_groups, thing_cls)
        self.class_id = class_id
        self.class_label = class_label
        self.running = True
        self.total_frames = 0
        self.coords = [[100, 70], [5, 57]]
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
        self.__detection_box_cls = class_from_thing_input(self.dr, self.thing, 'DetectionBoxData')
        self.__counter_cls = class_from_thing_output(self.dr, self.thing, 'Count')
        self.__input_subject = Subject()
        self.__input_subject.subscribe(observer=self.process_data)
        self.__output_subject = Subject()
        self.__output_subject.subscribe(observer=self.process_count)
        self.config_env()

    def config_env(self):
        line = ((int(self.coords[0][0] * self.width / 100), int(self.coords[0][1] * self.height / 100)),
                (int(self.coords[1][0] * self.width / 100), int(self.coords[1][1] * self.height / 100)))
        line = get_line(line)
        self.polygon = line.buffer(5)
        self.polygon = get_polygon(list(self.polygon.exterior.coords))


    def process_data(self, data):
        if data.flow_state == FlowState.ALIVE and data.data.size() > 0:
            detection_boxes = []
            for nvp in data.data:
                if(nvp.name == 'data'):
                    for inner_nvp in nvp.value.nvp_seq:
                        box_nvp_seq =inner_nvp.value.nvp_seq
                        box_data = Map()
                        for box_nvp in box_nvp_seq:
                            box_data[box_nvp.name] = getattr(box_nvp.value, tag_to_value_property_map[box_nvp.name])
                        detection_boxes.append(box_data)
            count = self.process_boxes(detection_boxes)
            self.__output_subject.on_next(CountData(data.flow_id, count))


    def process_boxes(self, boxes):
        count_people = 0
        for box in boxes:
            if box.probability > self.confidence_threshold and box.class_label == 'person':
                bbox = get_box((box.x1 * self.width, box.y1 * self.height, box.x2 * self.width, box.y2 * self.height))
                if self.polygon.intersects(bbox):
                    count_people +=1
        return count_people


    def process_count(self, count_data):
        count_obj = self.__counter_cls()
        count_obj.class_id = self.class_id
        count_obj.class_label = self.class_label
        count_obj.count = count_data.count
        write_tag(self.thing, 'Count', as_nvp_seq(count_obj), flow=count_data.flow_id)


    def run(self):
        log.info('Running')
        selector = self.thing.select('DetectionBoxData')
        while not self.terminate:
            samples = selector.read_iot_nvp(1000)

            for sample in samples:
                self.__input_subject.on_next(sample)



