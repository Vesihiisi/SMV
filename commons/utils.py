#!/usr/bin/python
# -*- coding: utf-8  -*-
import batchupload.helpers as helpers


def character_cleanup(txt):
    glossary = {
        "&Aacute;": "Á",
        "&aacute;": "á",
        "&Aring;": "Å",
        "&Auml;": "Ä",
        "&auml;": "ä",
        "&apos;": "'",
        "&eacute;": "é",
        "&egrave;": "è",
        "&Egrave;": "È",
        "&oacute;": "ó",
        "&uuml;": "ü",
    }
    for key in glossary.keys():
        txt = txt.replace(key, glossary[key])
    return txt


def clean_name(name_string):
    good_name = None
    if "f." in name_string:
        born_name = name_string.split("f.")[1].strip().split("(")[0].strip()
        good_name = helpers.flip_name(
            name_string.split("f.")[0]) + " f. " + born_name
    else:
        good_name = helpers.flip_name(name_string.split("(")[0].strip())
    return good_name
