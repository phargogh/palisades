"""Convert an IUI JSON configuration object to palisades format.  For usage
instructions:
    python convert_config.py --help
"""
import argparse
import json
import sys

from palisades import utils

def _find_ids(args_dict):
    """Recurse through args_dict (an IUI config dict), returning element ids."""
    ids = []
    try:
        ids.append(args_dict['id'])
    except KeyError:
        pass

    for key, value in args_dict.iteritems():
        if key == 'elements':
            for element in value:
                ids += _find_ids(element)
    return ids


def main(user_args=None):
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

    args = parser.parse_args(user_args)

    if args.default_lang not in args.languages:
        raise ValueError('Error: Default language "%s" not found in the '
                         'languages list: %s' % (args.default_lang,
                                                 args.languages))

    json_config = utils.load_json(args.iui_uri)

    element_ids = _find_ids(json_config)
    if 'workspace_dir' not in element_ids:
        raise ValueError('Error: config missing required element_id '
                         '"workspace_dir"')

    converted_config = utils.convert_iui(json_config, args.languages,
        args.default_lang)

    if args.out_uri is None:
        print json.dumps(converted_config, indent=4)
    else:
        utils.save_dict_to_json(converted_config, args.out_uri, indent=4)

if __name__ == '__main__':
    try:
        main(sys.argv[1:])
    except ValueError as error:
        print error
        sys.exit(1)
