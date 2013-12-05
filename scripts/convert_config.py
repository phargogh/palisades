import argparse
import json

from palisades import utils

# assume one argument only: input URI.  Print new dict to stdout.
parser = argparse.ArgumentParser(description="""Convert an IUI JSON
        configuration file to palisades JSON format.""")
parser.add_argument('iui_uri',
    help='URI to an IUI JSON object on disk')
parser.add_argument('out_uri', type=str, default=None,
    help="""Converted JSON file location.  If excluded, converted JSON will be
    printed to stdout.""")

args = parser.parse_args()

json_config = utils.load_json(args.iui_uri)
converted_config = utils.convert_iui(json_config)

if args.out_uri is None:
    print json.dumps(converted_config, indent=4)
else:
    utils.save_dict_to_json(converted_config, args.out_uri, indent=4)
