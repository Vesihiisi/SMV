#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Construct templates and categories for Helleday data.
"""
from collections import OrderedDict
import os.path
from os import listdir

import pywikibot

import batchupload.listscraper as listscraper
import batchupload.common as common
import batchupload.helpers as helpers
from batchupload.make_info import MakeBaseInfo
import re
import utils

MAPPINGS_DIR = 'mappings'
IMAGE_DIR = 'glass_uncat_2'
# stem for maintenance categories
BATCH_CAT = 'Media contributed by the Swedish Performing Arts Agency'
BATCH_DATE = '2017-10'  # branch for this particular batch upload
LOGFILE = "glasnegativ_uncat_2.log"


class GlassInfo(MakeBaseInfo):

    def category_exists(self, cat):
        if not cat.lower().startswith('category:'):
            cat = 'Category:{0}'.format(cat)

        if cat in self.category_cache:
            return cat

        exists = pywikibot.Page(self.commons, cat).exists()
        if exists:
            self.category_cache.append(cat)
        return exists

    def __init__(self, **options):
        super(GlassInfo, self).__init__(**options)
        self.batch_cat = "{}: {}".format(BATCH_CAT, BATCH_DATE)
        self.commons = pywikibot.Site('commons', 'commons')
        self.wikidata = pywikibot.Site('wikidata', 'wikidata')
        self.log = common.LogFile('', LOGFILE)
        self.category_cache = []

    def load_data(self, in_file):
        return common.open_and_read_file(in_file, as_json=False)

    def generate_content_cats(self, item):
        item.generate_depicted_cat()
        # item.generate_yearly_cat()
        # item.generate_image_type_cats()
        # item.generate_creator_cat()
        item.content_cats.add("Glass plate negatives in the Swedish Performing Arts Agency")
        return list(item.content_cats)

    def generate_filename(self, item):
        id_no = item.id_no
        title = item.image_title
        provider = "SMV"
        return helpers.format_filename(
            title, provider, id_no)

    def generate_meta_cats(self, item, cats):
        cats = set(item.meta_cats)
        cats.add(self.batch_cat)
        return list(cats)

    def load_mappings(self, update_mappings):
        depicted_file = os.path.join(MAPPINGS_DIR, 'glass_depicted.json')
        depicted_page = 'User:Alicia_Fagerving_(WMSE)/sandbox_gn_depicted'
        if update_mappings:
            print("Updating mappings...")
            self.mappings['depicted'] = self.get_depicted_mapping(
                depicted_page)
            common.open_and_write_file(
                depicted_file, self.mappings['depicted'], as_json=True)
        else:
            self.mappings['depicted'] = common.open_and_read_file(
                depicted_file, as_json=True)
        pywikibot.output('Loaded all mappings')

    def get_depicted_mapping(self, play_page):
        theatres = {}
        page = pywikibot.Page(self.commons, play_page)
        data = listscraper.parseEntries(
            page.text,
            row_t='User:André Costa (WMSE)/mapping-row',
            default_params={'name': '', 'category': '', 'frequency': ''})
        for entry in data:
            if entry['category'] and entry['name']:
                category = entry['category'][0]
                name = entry['name'][0]
                theatres[name] = category
        return theatres

    def make_info_template(self, item):
        template_name = 'Musikverket-image'
        template_data = OrderedDict()
        template_data['title'] = item.image_title.replace("_", " ")
        template_data['depicted people'] = item.generate_depicted_people()
        template_data['date'] = item.generate_date()
        template_data['notes'] = self.generate_note()
        template_data['department'] = item.generate_collection()
        template_data['permission'] = item.generate_license()
        template_data['ID'] = item.id_no
        template_data['source'] = item.generate_source()
        return helpers.output_block_template(template_name, template_data, 0)

    def generate_note(self):
        return "This file comes from a part of the collection that had not been cataloged and provided with detailed metadata. The lack of metadata might have resulted in poor description and categorization of the file."

    def get_original_filename(self, item):
        filename = None
        path = IMAGE_DIR
        image_id = item.id_no
        for fname in listdir(path):
            if fname.startswith(image_id):
                filename = fname[:-4]
        return filename

    def process_data(self, raw_data):
        d = {}
        for line in raw_data.splitlines():
            rec_dic = {}
            id_no = line.split("_")[0]
            rec_dic["id_no"] = id_no
            rec_dic["image_title"] = line.split("_", 1)[1].split(".")[0]
            d[id_no] = GlassItem(rec_dic, self)
        self.data = d


class GlassItem(object):

    def __init__(self, initial_data, glass_info):

        for key, value in initial_data.items():
            setattr(self, key, value)

        self.wd = {}  # store for relevant Wikidata identifiers
        self.content_cats = set()  # content relevant categories without prefix
        self.meta_cats = set()  # meta/maintenance proto categories
        self.glass_info = glass_info
        self.commons = pywikibot.Site('commons', 'commons')

    def generate_source(self):
        template = '{{Musikverket cooperation project}}'
        info_link = '{{Musikverket-link|' + self.id_no + '}}'
        text = "Swedish Performing Arts Agency: {}".format(info_link)
        return "{}\n{}".format(text, template)

    def generate_date(self):
        match = re.match(r'.*([1-3][0-9]{3})', self.image_title)
        if match is not None:
            return helpers.stdDate(match.group(1))

    def generate_license(self):
        template = "{{PD-old-70}}"
        return template

    def generate_depicted_people(self):
        names = []
        before_in = self.image_title.split("_in_")[0]
        all_persons = before_in.split("_and_")
        for p in all_persons:
            for p in p.split(","):
                if "unidentified" not in p.lower() and "dancer" not in p.lower() and "scene" not in p.lower():
                    if "_as_" in p:
                        p = p.split("_as_")[0]
                    names.append(p.replace("_", " "))
        if names:
            depicted = " / ".join(names)
            return depicted

    def generate_collection(self):
        library = "Musik- och teaterbiblioteket"
        return "{}, {}".format(library, "Glasnegativsamlingen")

    def generate_yearly_cat(self):
        base = "{} portrait photographs"
        tentative = base.format(self.image_date)
        if self.glass_info.category_exists(tentative):
            self.content_cats.add(tentative)

    def generate_image_type_cats(self):
        tentative = []
        img_type = self.image_type.lower()
        if self.gender.lower() == "kvinna":
            gender = "women"
        elif self.gender.lower() == "man":
            gender = "men"
        if "porträtt" in img_type:
            tentative.append("Portrait photographs of {}".format(gender))
        if img_type == "rollporträtt":
            tentative.append("Theatrical costume in portraits")
        for t in tentative:
            if self.glass_info.category_exists(t):
                self.content_cats.add(t)

    def generate_creator_cat(self):
        c = self.creator.lower()
        if "atelier jaeger" in c:
            self.content_cats.add("Atelier Jaeger")
        elif "a. blomberg" in c:
            self.content_cats.add("Anton Blomberg")

    def generate_depicted_cat(self):
        if "_as_" not in self.image_title:
            before_in = self.image_title.split("_in_")[0]
        else:
            before_in = self.image_title.split("_as_")[0]
        all_persons = before_in.split("_and_")
        number_of_people = 0
        added_cats = 0
        for p in all_persons:
            if len(p.split(",")[0].split("_")) > 1:
                number_of_people = number_of_people + 1
                name = p.split(",")[0].replace("_", " ")
                if self.glass_info.category_exists(name):
                    self.content_cats.add(name)
                    added_cats = added_cats + 1
        if added_cats == 0 or added_cats < number_of_people:
            self.meta_cats.add(BATCH_CAT + ": needing categorisation (people)")


if __name__ == '__main__':
    GlassInfo.main()
