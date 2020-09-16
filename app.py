import argparse
import sys
import logging as log
import json

from adl_edge_iot.datariver.things.edge_thing import EdgeThing
from adl_line_monitoring import LineMonitor

PROPERTIES_FILE = './etc/config/properties.json'

# ---------------------------------------------------------------------------------------------------------------------
# ----------
# ---------- Configure logging
# ----------
# ---------------------------------------------------------------------------------------------------------------------
log.basicConfig(format='[ %(levelname)s ] %(message)s', level=log.INFO, stream=sys.stdout)

# ---------------------------------------------------------------------------------------------------------------------
# ----------
# ---------- App parameters
# ----------
# ---------------------------------------------------------------------------------------------------------------------
def argument_parser():
    log.info('Creating the argument parser...')
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('-l', '--line', type=float, nargs=4, required=False, default=[100, 70, 5, 57])
    parser.add_argument('-w', '--width', type=int, required=False,
                        default=1024)
    parser.add_argument('-h', '--height', type=int, required=False,
                        default=768)
    parser.add_argument('-cid', '--classid', type=int, required=False,
                        default=15)
    parser.add_argument('-cl', '--classlabel', type=str, required=False,
                        default='person')
    parser.add_argument('-p', '--properties', type=str, required=False,
                        help='The URI (without file://) to the properties file.',
                        default='./config/Viewer.json')
    parser.add_argument('-tg', '--tag_group_dir', type=str, required=False,
                        help='The directory containing the TagGroups.',
                        default='./definitions/TagGroup')
    parser.add_argument('-tc', '--thing_class_dir', type=str, required=False,
                        help='The directory containing the ThingClasses.',
                        default='./definitions/ThingClass')

    return parser.parse_args()

def init_edge_thing(args):
    with open(PROPERTIES_FILE) as f:
        properties_str = json.load(f)
        properties_str = json.dumps(properties_str) if properties_str is not None else None
        coords = args['line']
        coords = [[coords[0],coords[1]], [coords[2],coords[3]]]
    return LineMonitor(args['width'], args['height'], args['classid'], args['classlabel'], coords,
                     properties_str=properties_str,
                     tag_groups=['com.vision.data/DepthDetectionBox', 'com.generic.data/ObjectCountTagGroup'],
                     thing_cls=['com.adlinktech.solution/LineCounter'])

def main():
    args = vars(argument_parser())
    app = init_edge_thing(args)
    app.run()

    return 0

if __name__ == '__main__':
    sys.exit(main())
