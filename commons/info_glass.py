#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Construct templates and categories for Helleday data.
"""
from collections import OrderedDict
import os.path
from os import listdir

from xml.dom.minidom import parseString
import pywikibot

import batchupload.listscraper as listscraper
import batchupload.common as common
import batchupload.helpers as helpers
from batchupload.make_info import MakeBaseInfo
import utils

MAPPINGS_DIR = 'mappings'
IMAGE_DIR = 'Glasnegativsamlingen'
# stem for maintenance categories
BATCH_CAT = 'Media contributed by the Swedish Performing Arts Agency'
BATCH_DATE = '2017-10'  # branch for this particular batch upload
LOGFILE = "glasnegativ.log"


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
        item.generate_yearly_cat()
        item.generate_image_type_cats()
        item.generate_creator_cat()
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
        template_data['title'] = item.image_title
        template_data['description'] = item.generate_descriptions()
        template_data['photographer'] = item.generate_photographer()
        template_data['depicted people'] = item.generate_depicted_people()
        template_data['date'] = item.generate_date()
        template_data['department'] = item.generate_collection()
        template_data['permission'] = item.generate_license()
        template_data['ID'] = item.id_no
        template_data['source'] = item.generate_source()
        return helpers.output_block_template(template_name, template_data, 0)

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
        dom = parseString(utils.character_cleanup(raw_data))
        records = dom.getElementsByTagName("DScribeRecord")
        tagDict = {
            'image_title': 'Title',
            'id_no': 'RefNo',
            'image_date': 'Date',
            'description': 'Description',
            'depicted': 'UserText1',
            'creator': 'UserWrapped5',
            'collection': 'NamedCollection',
            'url': 'URL',
            'thumbnail': 'Thumbnail',
            'gender': 'UserText7',
            'keywords': 'Keyword',
            'image_type': 'UserWrapped2',
        }
        for record in records:
            rec_dic = {}
            for tag in tagDict:
                xml_tag = tagDict[tag]
                try:
                    if tag == "description":
                        descriptions = {}
                        nodes = record.getElementsByTagName(xml_tag)
                        swedish = nodes[0].firstChild.nodeValue.strip()
                        english = nodes[1].firstChild.nodeValue.strip()
                        descriptions["sv"] = swedish
                        descriptions["en"] = english
                        content = descriptions
                    elif tag == "depicted":
                        depicted = []
                        nodes = record.getElementsByTagName(xml_tag)
                        for node in nodes:
                            depicted.append(node.firstChild.nodeValue.strip())
                        content = depicted
                    else:
                        content = record.getElementsByTagName(
                            xml_tag)[0].firstChild.nodeValue.strip()
                except (AttributeError, IndexError):
                    content = ""
                rec_dic[tag] = content
            id_no = rec_dic["id_no"]
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

    def generate_descriptions(self):
        for desc in self.description:
            if not self.description[desc].endswith("."):
                self.description[desc] = self.description[desc] + "."
        swedish = "{{{{sv|{}}}}}".format(self.description["sv"])
        english = "{{{{en|{}}}}}".format(self.description["en"])
        return "{}\n{}".format(english, swedish)

    def generate_date(self):
        date = None
        if self.image_date:
            date = helpers.stdDate(self.image_date)
        return date

    def generate_license(self):
        template = "{{PD-old-70}}"
        return template

    def generate_photographer(self):
        c = self.creator.lower()
        if "atelier jaeger" in c:
            return "Atelier Jaeger, Stockholm"
        elif "a. blomberg" in c:
            return "{{Creator:Anton Blomberg}}"

    def generate_depicted_people(self):
        if self.depicted:
            depicted = " / ".join([utils.clean_name(x) for x in self.depicted])
            return depicted

    def generate_collection(self):
        library = "Musik- och teaterbiblioteket"
        return "{}, {}".format(library, self.collection)

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
        depicted_map = self.glass_info.mappings['depicted']
        if self.depicted:
            for person in self.depicted:
                if person in depicted_map:
                    self.content_cats.add(depicted_map[person])
                else:
                    if self.gender.lower() == "kvinna":
                        yrke = "Actresses"
                    elif self.gender.lower() == "man":
                        yrke = "Actors"
                    general_cat = "{} from Sweden".format(yrke)
                    self.content_cats.add(general_cat)
                    self.meta_cats.add(BATCH_CAT + ": needing categorisation (people)")


if __name__ == '__main__':
    GlassInfo.main()
