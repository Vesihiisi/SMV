#!/usr/bin/python
# -*- coding: utf-8  -*-
import datetime
import csv
import json
import os
import re

import pywikibot
from wikidataStuff.WikidataStuff import WikidataStuff as wds

site_cache = {}


def get_file_from_subdir(dir_name, file_name):
    """
    Get the absolute path of a file in a subdir inside current dir.

    This works in relation to where this file is actually
    located, not the current working directory, to make sure
    the tests don't try to resolve the path in relation
    to their own working directory.

    :param dir_name: name or relative path
                     (from directory containing this file) of subdirectory
    :param file_name: name of file
    """
    absolute_current = os.path.dirname(os.path.abspath(__file__))
    path_subdir = os.path.join(absolute_current, dir_name)
    return os.path.join(path_subdir, file_name)


def load_json(filename):
    try:
        with open(filename) as f:
            try:
                return json.load(f)
            except ValueError:
                print("Failed to decode file {}.".format(filename))
    except OSError:
        print("File {} does not exist.".format(filename))


def json_to_file(filename, json_content):
    with open(filename, 'w') as f:
        json.dump(json_content, f, sort_keys=True,
                  indent=4,
                  ensure_ascii=False,
                  default=datetime_convert)


def append_line_to_file(text, filename):
    with open(filename, 'a') as f:
        f.write(text + "\n")


def get_rid_of_brackets(text):
    if "(" in text:
        return re.sub('\(.*?\)', '', text).strip()
    else:
        return text


def get_current_timestamp():
    return datetime.datetime.now().strftime('%Y-%m-%d_%H:%M:%S')


def string_is_q_item(text):
    """Check if a string looks like a WD ID."""
    pattern = re.compile("^Q[0-9]+$", re.I)
    try:
        m = pattern.match(text)
    except TypeError:
        return False
    if m:
        return True
    else:
        return False


def datetime_convert(dt_object):
    if isinstance(dt_object, datetime.datetime):
        return dt_object.__str__()


def wd_template(template_type, value):
    """
    Wrap up Wikidata item/prop in a linking template.

    :param template_type: Q or P
    :param value: content of the template, eg. Q15 but
                  you can also omit the letter since the
                  template knows it already.
    """
    return "{{" + template_type + "|" + value + "}}"


def create_site_instance(language, family):
    """Create an instance of a Wiki site (convenience function)."""
    site_key = (language, family)
    site = site_cache.get(site_key)
    if not site:
        site = pywikibot.Site(language, family)
        site_cache[site_key] = site
    return site


def is_vowel(char):
    """Check whether a character is a vowel."""
    vowels = "auoiyéeöåäáæø"
    if char.lower() in vowels:
        return True
    else:
        return False


def get_last_char(text):
    """Return the last character of string."""
    return text[-1]


def last_char_is_vowel(text):
    """Check if last char of string is vowel."""
    return is_vowel(get_last_char(text))


def remove_multiple_spaces(text):
    return re.sub(' +', ' ', text)


def date_to_dict(datestring, dateformat):
    """
    Convert a date to a pwb-friendly dictionary.

    Can handle:
        * day dates, "2009-09-31",
        * month dates, "2009-09",
        * year dates, "2009"

    :param datestring: a string representing a date timestamp,
                       for example: "2009-09-31".
    :param datestring: a string key for interpreting the timestamp,
                       for example "%Y-%m-%d" which is the key for
                       the above timestamp.
    """
    date_dict = {}
    date_obj = datetime.datetime.strptime(datestring, dateformat)
    date_dict["year"] = date_obj.year
    if "%m" in dateformat:
        date_dict["month"] = date_obj.month
    if "%d" in dateformat:
        date_dict["day"] = date_obj.day
    return date_dict


def extract_municipality_name(category_name):
    """
    Extract base municipality name from category name.

    Since we can't guess whether an "s" ending the first
    part of the name belongs to the town name or is
    a genitive ending (and should be dropped), we have to
    compare against (English) list of known municipalities:

    Halmstads kommun -> Halmstad
    Kramfors kommun -> Kramfors
    Pajala kommun -> Pajala

    Known caveats:
    * Reserves in Gotland are categorized in "Gotlands län"

    :param category_name: Category of Swedish nature reserves,
                          like "Naturreservat i Foo kommun"
    """
    municipality = None
    legit_municipalities = load_json(
        get_file_from_subdir("data", "municipalities.json"))
    m = re.search('(\w?)[N|n]aturreservat i (.+?) [kommun|län]', category_name)
    if m:
        municipality = m.group(2)
        municipality_clean = [x["en"].split(" ")[0] for
                              x in legit_municipalities if
                              x["sv"] == municipality + " kommun"]
        if municipality_clean:
            municipality = municipality_clean[0]
            if municipality == "Gothenburg":
                municipality = "Göteborg"
    return municipality


def q_from_wikipedia(language, page_title):
    """
    Get the ID of the WD item linked to a wp page.

    If the page has no item and is in the article
    namespace, create an item for it.
    """
    wp_site = pywikibot.Site(language, "wikipedia")
    page = pywikibot.Page(wp_site, page_title)
    summary = "Creating item for {} on {}wp."
    summary = summary.format(page_title, language)
    wd_repo = create_site_instance("wikidata", "wikidata")
    wdstuff = wds(wd_repo, edit_summary=summary)
    if page.exists():
        if page.isRedirectPage():
            page = page.getRedirectTarget()
        try:
            item = pywikibot.ItemPage.fromPage(page)
        except pywikibot.NoPage:
            if page.namespace() != 0:  # main namespace
                return
            item = wdstuff.make_new_item_from_page(page, summary)
        return item.getID()


def remove_dic_from_list_by_value(diclist, key, value):
    """
    Remove a dictionary from a list of dictionaries by certain value.

    :param diclist: List of dictionaries
    :param key: The key whose value to check
    :param value: The value of that key that should cause removal
                  of dictionary from list.
    """
    return [x for x in diclist if value != x.get(key)]


def get_data_from_csv_file(filename):
    """Load data from csv file into a list."""
    with open(filename, "r") as f_obj:
        reader = csv.DictReader(f_obj, delimiter=',')
        csv_data = list(reader)
    return csv_data
