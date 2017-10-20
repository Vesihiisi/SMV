#!/usr/bin/env python3
import argparse
import pywikibot
import os

import wikidataStuff.wdqsLookup as lookup
import importer_utils as utils
from Person import Person
from Uploader import Uploader

AUTH_FILE = "authority.json"
MAPPINGS = "mappings"


def get_wd_items_using_prop(prop):
    items = {}
    print("WILL NOW DOWNLOAD WD ITEMS THAT USE " + prop)
    query = "SELECT DISTINCT ?item ?value  WHERE {?item p:" + \
        prop + "?statement. OPTIONAL { ?item wdt:" + prop + " ?value. }}"
    data = lookup.make_simple_wdqs_query(query, verbose=False)
    for x in data:
        key = lookup.sanitize_wdqs_result(x['item'])
        value = x['value']
        items[value] = key
    print("FOUND {} WD ITEMS WITH PROP {}".format(len(items), prop))
    return items


def load_mapping_files():
    mappings = {}
    available = ["first", "last", "professions", "properties"]
    for title in available:
        f = os.path.join(MAPPINGS, '{}.json'.format(title))
        mappings[title] = utils.load_json(f)
    print("Loaded mappings: {}.".format(", ".join(available)))
    return mappings


def load_auth_file():
    return utils.load_json(AUTH_FILE)


def main(arguments):
    arguments = vars(arguments)
    wikidata_site = utils.create_site_instance("wikidata", "wikidata")
    existing_people = get_wd_items_using_prop("P4357")
    auth_data = load_auth_file()
    data_files = load_mapping_files()
    if arguments["offset"]:
        print("Using offset: {}.".format(str(arguments["offset"])))
        auth_data = auth_data[arguments["offset"]:]
    if arguments["limit"]:
        print("Using limit: {}.".format(str(arguments["limit"])))
        auth_data = auth_data[:arguments["limit"]]
    for p in auth_data:
        p_data = p[list(p.keys())[0]]
        person = Person(p_data, wikidata_site, data_files, existing_people)
        if arguments["upload"]:
            live = True if arguments["upload"] == "live" else False
            uploader = Uploader(person,
                                repo=wikidata_site,
                                live=live,
                                edit_summary="importing #Musikverket authority file")
            try:
                uploader.upload()
            except pywikibot.data.api.APIError:
                continue


if __name__ == "__main__":
    arguments = {}
    parser = argparse.ArgumentParser()
    parser.add_argument("--upload", action='store')
    parser.add_argument("--offset",
                        nargs='?',
                        type=int,
                        action='store')
    parser.add_argument("--limit",
                        nargs='?',
                        type=int,
                        action='store')
    args = parser.parse_args()
    main(args)
