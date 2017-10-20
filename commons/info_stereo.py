#!/usr/bin/python
# -*- coding: utf-8  -*-
"""
Construct templates and categories for Helleday data.
"""
from collections import OrderedDict
from os import listdir

from xml.dom.minidom import parseString
import pywikibot

import batchupload.listscraper as listscraper
import batchupload.common as common
import batchupload.helpers as helpers
from batchupload.make_info import MakeBaseInfo
import utils

MAPPINGS_DIR = 'mappings'
IMAGE_DIR = 'Stereokortsamlingen'
# stem for maintenance categories
BATCH_CAT = 'Media contributed by the Swedish Performing Arts Agency'
BATCH_DATE = '2017-10'  # branch for this particular batch upload
LOGFILE = "stereokort.log"


class StereoInfo(MakeBaseInfo):

    def __init__(self, **options):
        super(StereoInfo, self).__init__(**options)
        self.batch_cat = "{}: {}".format(BATCH_CAT, BATCH_DATE)
        self.commons = pywikibot.Site('commons', 'commons')
        self.wikidata = pywikibot.Site('wikidata', 'wikidata')
        self.log = common.LogFile('', LOGFILE)
        self.category_cache = []

    def category_exists(self, cat):
        if not cat.lower().startswith('category:'):
            cat = 'Category:{0}'.format(cat)

        if cat in self.category_cache:
            return cat

        exists = pywikibot.Page(self.commons, cat).exists()
        if exists:
            self.category_cache.append(cat)
        return exists

    def load_data(self, in_file):
        return common.open_and_read_file(in_file, as_json=False)

    def generate_content_cats(self, item):
        item.generate_yearly_cat()
        item.content_cats.add("Color stereo cards")
        item.content_cats.add("Stereo cards in the Swedish Performing Arts Agency")
        return list(item.content_cats)

    def generate_filename(self, item):
        id_no = item.id_no
        title = item.image_title
        number = item.number
        provider = "SMV"
        filename = helpers.format_filename(
            title, provider, id_no + number)
        return filename

    def generate_meta_cats(self, item, cats):
        cats = set([self.make_maintenance_cat(cat) for cat in item.meta_cats])
        cats.add(self.batch_cat)
        return list(cats)

    def load_mappings(self, update_mappings):
        pywikibot.output('Loaded all mappings')

    def make_info_template(self, item):
        template_name = 'Musikverket-image'
        template_data = OrderedDict()
        template_data['title'] = item.image_title
        template_data['description'] = item.generate_descriptions()
        template_data['dimensions'] = item.generate_dimensions()
        template_data['date'] = item.generate_date()
        template_data['department'] = item.generate_collection()
        template_data['permission'] = item.generate_license()
        template_data['ID'] = item.id_no
        template_data['source'] = item.generate_source()
        template_data['other versions'] = item.get_other_versions()
        return helpers.output_block_template(template_name, template_data, 0)

    def get_original_filename(self, item):
        filename = None
        path = IMAGE_DIR
        image_id = item.id_no
        number = item.number
        for fname in listdir(path):
            fname = fname.split(".")[0]
            if fname.split("_")[0] == image_id and fname.endswith(number):
                filename = fname
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
            'keywords': 'Keyword',
            'record_type': 'RecordType',
            'dimensions': 'DimensionValue'
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
                    else:
                        content = record.getElementsByTagName(
                            xml_tag)[0].firstChild.nodeValue.strip()
                except (AttributeError, IndexError):
                    content = ""
                rec_dic[tag] = content
            id_no = rec_dic["id_no"]
            if rec_dic["record_type"] != "Collection":
                rec_dic_a = rec_dic.copy()
                rec_dic_b = rec_dic.copy()
                rec_dic_a["number"] = "a"
                rec_dic_b["number"] = "b"
                d[id_no + "a"] = StereoItem(rec_dic_a, self)
                d[id_no + "b"] = StereoItem(rec_dic_b, self)
        self.data = d


class StereoItem(object):

    def __init__(self, initial_data, stereo_info):

        for key, value in initial_data.items():
            setattr(self, key, value)

        self.wd = {}
        self.content_cats = set()
        self.meta_cats = set()
        self.stereo_info = stereo_info
        self.commons = pywikibot.Site('commons', 'commons')

    def generate_descriptions(self):
        swedish = self.description["sv"]
        english = self.description["en"]
        sw_desc = "{{{{sv|{}}}}}".format(swedish)
        en_desc = "{{{{en|{}}}}}".format(english)
        return "{}\n{}".format(en_desc, sw_desc)

    def generate_source(self):
        template = '{{Musikverket cooperation project}}'
        info_link = '{{Musikverket-link|' + self.id_no + '}}'
        text = "Swedish Performing Arts Agency: {}".format(info_link)
        return "{}\n{}".format(text, template)

    def generate_date(self):
        date = None
        if self.image_date:
            date = helpers.stdDate(self.image_date)
        return date

    def generate_license(self):
        return "{{PD-old}}"

    def generate_collection(self):
        library = "Musik- och teaterbiblioteket"
        return "{}, {}".format(library, self.collection)

    def generate_dimensions(self):
        """18,3 x 11,6 cm or 16x25 cm"""
        parsed = None
        template = "{{{{Size|cm|{}|{}}}}}"
        if "x" in self.dimensions:
            split = self.dimensions.split("x")
            first = split[0].strip()
            second = split[1].strip().split(" ")[0]
            parsed = template.format(first, second)
        return parsed

    def generate_yearly_cat(self):
        if "talet" in self.image_date:
            year = self.image_date.split("-")[0]
            tentative_cat = "Theatre in the {}s".format(year)
            if self.stereo_info.category_exists(tentative_cat):
                self.content_cats.add(tentative_cat)
        else:
            tentative_cat = "{} in theatre".format(self.image_date)
            if self.stereo_info.category_exists(tentative_cat):
                self.content_cats.add(tentative_cat)

    def get_other_versions(self):
        filename = self.stereo_info.generate_filename(self)
        filename_no_number = filename[:-1]
        if self.number == "a":
            matching_ending = "b"
        elif self.number == "b":
            matching_ending = "a"
        matching_filename = filename_no_number + matching_ending
        fname = matching_filename + ".tif"
        return '<gallery mode=nolines widths="300px">\n{}\n</gallery>'.format(fname)


if __name__ == '__main__':
    StereoInfo.main()
