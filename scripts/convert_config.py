import argparse
import json
import sys

from palisades import utils

# assume one argument only: input URI.  Print new dict to stdout.
parser = argparse.ArgumentParser(description="""Convert an IUI JSON
        configuration file to palisades JSON format.""")
parser.add_argument('iui_uri',
    help='URI to an IUI JSON object on disk')
parser.add_argument('out_uri', type=str, default=None,
    help="""Converted JSON file location.  If excluded, converted JSON will be
    printed to stdout.""")
parser.add_argument('-l', '--languages', type=str, default=['en'],
    dest='languages', nargs='+',
    help="""A space-separated list of language codes (default='en').""")
parser.add_argument('-d', '--default-lang', type=str, default='en',
    dest='default_lang',
    help="""A string language code to use as the default language.  Must be one
    of the given language codes. (default='en')""")

args = parser.parse_args()

if args.default_lang not in args.languages:
    print ('Error: Default language "%s" not found in the languages list: %s' %
        (args.default_lang, args.languages))
    sys.exit(1)

json_config = utils.load_json(args.iui_uri)
converted_config = utils.convert_iui(json_config, args.languages,
    args.default_lang)

if args.out_uri is None:
    print json.dumps(converted_config, indent=4)
else:
    utils.save_dict_to_json(converted_config, args.out_uri, indent=4)
