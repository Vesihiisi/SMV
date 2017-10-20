#!/usr/bin/python
# -*- coding: utf-8  -*-
import argparse
from collections import Counter
from xml.dom.minidom import parseString
import batchupload.common as common
import batchupload.helpers as helpers
import utils


def create_wikipage(items, typ):
    table_head = "{{{{User:André Costa (WMSE)/mapping-head|name=photographer name|{}=}}}}\n".format(typ)
    table_foot = '|}'
    table_row = "{{{{User:André Costa (WMSE)/mapping-row\n| name= {}\n|frequency = {}\n|{}  = \n}}}}\n"
    wikitext = ''
    for item in items:
        count = item[1]
        value = item[0]
        wikitext += table_row.format(value, count, typ)
    return table_head + wikitext + table_foot


def save_data(out_file, text):
    return common.open_and_write_file(out_file, text)


def load_data(in_file):
    return common.open_and_read_file(in_file, as_json=False)


def get_items_by_tag(xml, tag):
    items = []
    dom = parseString(utils.character_cleanup(xml))
    records = dom.getElementsByTagName("DScribeRecord")
    for record in records:
        try:
            content = record.getElementsByTagName(
                tag)[0].firstChild.nodeValue
        except (AttributeError, IndexError):
            content = ""
        if len(content) != 0:
            items.append(content.strip())
    counted = Counter(items)
    return counted.most_common()


def create_filename(field):
    return "{}.txt".format(field)


def main(arguments):
    raw_xml = load_data(arguments.in_file)
    items = get_items_by_tag(raw_xml, arguments.field)
    wikitable = create_wikipage(items, arguments.typ)
    filename = create_filename(arguments.field)
    save_data(filename, wikitable)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_file", default="helleday.xml")
    parser.add_argument("--field", required=True)
    parser.add_argument("--typ", default="wikidata")
    parser.add_argument("--split")
    args = parser.parse_args()
    main(args)
