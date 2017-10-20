# -*- coding: utf-8 -*-
import pywikibot
from pywikibot import pagegenerators as pg
import mwparserfromhell as parser
import re

site = pywikibot.Site("commons", 'commons')
catname = "Glass plate negatives in the Swedish Performing Arts Agency"
cat = pywikibot.Category(site, catname)
gen = pg.CategorizedPageGenerator(cat)

the_map = {
    "dramaten": "Kungliga Dramatiska Teatern",
    "vasateatern": "Vasateatern",
    "kungliga operan": "Kungliga operan",
    "södra teatern": "Södra teatern",
    "folkteatern": "Folkan",
    "östermalmsteatern": "Östermalmsteatern",
    "oscarsteatern": "Oscarsteatern",
    "djurgårdsteatern": "Djurgårdsteatern",
    "dramatiska teatern": "Kungliga Dramatiska Teatern",
    "svenska teatern": "Svenska teatern, Stockholm",
    "stora teatern i göteborg": "Stora Teatern, Göteborg",
    "kristallsalongen": "Kristallsalongen",
    "operett-teatern": "Östermalmsteatern",
    "intima teatern": "Komediteatern"
}


def add_missing_creator(page):
    c_cats = {
        "Atelier Jaeger": "Category:Atelier Jaeger",
        "A. Blomberg": "Category:Anton Blomberg"
    }
    c_strings = {
        "Atelier Jaeger": "Atelier Jaeger",
        "A. Blomberg": "{{Creator:Anton Blomberg}}"
    }
    md = page.latest_file_info["metadata"]
    exif = [x for x in md if x["name"] == "exif"][0]["value"]
    creator = [x["value"] for x in exif if x["name"] == "Artist"]
    if len(creator) == 1:
        creator = creator[0]
        if creator in list(c_cats.keys()):
            parsed = parser.parse(page.text)
            templates = parsed.filter_templates()
            for t in templates:
                if t.name.matches("Musikverket-image"):
                    if not t.has("photographer"):
                        new_creator = c_strings[creator]
                        t.add("photographer", new_creator)
                        page.text = str(parsed)
                        if c_cats[creator] not in page.text:
                            page.text = page.text + "\n[[{}]]\n".format(c_cats[creator])
                        page.save("adding creator info from exif data")


def correct_as(page):
    parsed = parser.parse(page.text)
    templates = parsed.filter_templates()
    for t in templates:
        if t.name.matches("Musikverket-image") and t.has("depicted people"):
            depicted_value = t.get("depicted people").value
            if " as " in depicted_value:
                new_depicted = depicted_value.split(" as ")[0].strip()
                t.add("depicted people", new_depicted)
                page.text = str(parsed)
                page.save("description fixes")


def add_missing_theatre_cat(page):
    title = g.title(withNamespace=False)
    if " at " in title:
        the_part = title.split(" at ")[1].lower()
        matches = [x for x in the_map if the_part.startswith(x)]
        if len(matches) == 1:
            cat_to_add = "Category:{}".format(the_map[matches[0]])
            page = pywikibot.Page(page)
            p_text = page.text
            if cat_to_add not in p_text:
                p_text = p_text + "\n[[{}]]\n".format(cat_to_add)
                page.text = p_text
                page.save("adding: {}".format(cat_to_add))
        else:
            print(the_part)


def add_date_cat(page):
    title = page.title(withNamespace=False)
    match = re.match(r'.*([1-3][0-9]{3})', title)
    if match is not None:
        year = match.group(1)
        if "porträtt" in title:
            base_cat = "Category:{} portrait photographs"
        else:
            base_cat = "Category:{} photographs"
        cat_to_add = base_cat.format(year)
        if cat_to_add not in page.text:
            page.text = page.text + "\n[[{}]]\n".format(cat_to_add)
            page.save("adding: {}".format(cat_to_add))


for g in gen:
    # correct_as(g)
    # add_missing_theatre_cat(g)
    # add_missing_creator(g)
    # add_date_cat(g)
    pass
