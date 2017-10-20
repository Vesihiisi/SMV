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
IMAGE_DIR = 'Helledays samling'
# stem for maintenance categories
BATCH_CAT = 'Media contributed by the Swedish Performing Arts Agency'
BATCH_DATE = '2017-10'  # branch for this particular batch upload
LOGFILE = "helleday.log"


class HellInfo(MakeBaseInfo):

    def linksearch_generator(self, url, namespace=None):
        raw_url = url
        default_protocol = 'http'

        protocol, _, url = url.partition('://')
        if not url:
            url = raw_url
            protocol = default_protocol

        if isinstance(namespace, list):
            namespace = '|'.join(namespace)

        g = pywikibot.data.api.ListGenerator(
            'exturlusage', euquery=url, site=self.commons,
            eunamespace=namespace, euprotocol=protocol, euprop='title|url')
        return g

    def category_exists(self, cat):
        if not cat.lower().startswith('category:'):
            cat = 'Category:{0}'.format(cat)

        if cat in self.category_cache:
            return cat

        exists = pywikibot.Page(self.commons, cat).exists()
        if exists:
            self.category_cache.append(cat)
        return exists

    def load_wd_value(self, qid, props, cache=None):
        if cache and qid in cache:
            return cache[qid]

        data = {}
        wd_item = pywikibot.ItemPage(self.wikidata, qid)
        wd_item.exists()  # load data
        for pid, label in props.items():
            value = None
            claims = wd_item.claims.get(pid)
            if claims:
                value = claims[0].getTarget()
            data[label] = value

        if cache:
            cache[qid] = data
        return data

    def __init__(self, **options):
        super(HellInfo, self).__init__(**options)
        self.batch_cat = "{}: {}".format(BATCH_CAT, BATCH_DATE)
        self.commons = pywikibot.Site('commons', 'commons')
        self.wikidata = pywikibot.Site('wikidata', 'wikidata')
        self.log = common.LogFile('', LOGFILE)
        self.photographer_cache = {}
        self.category_cache = []

    def load_data(self, in_file):
        return common.open_and_read_file(in_file, as_json=False)

    def generate_content_cats(self, item):
        item.generate_yearly_cat()
        item.generate_theatre_cat()
        item.generate_depicted_cat()
        item.generate_costume_cat()
        item.generate_portrait_cat()
        item.generate_photographer_cat()
        item.generate_play_cat()
        return [x for x in list(item.content_cats) if x is not None]

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

    def get_original_filename(self, item):
        filename = None
        path = IMAGE_DIR
        image_id = item.id_no
        for fname in listdir(path):
            if fname.startswith(image_id):
                filename = fname[:-4]
        return filename

    def load_mappings(self, update_mappings):
        depicted_file = os.path.join(MAPPINGS_DIR, 'depicted.json')
        depicted_page = 'User:Alicia_Fagerving_(WMSE)/sandbox3'
        photographer_file = os.path.join(MAPPINGS_DIR, 'photographers.json')
        photographer_page = 'User:Alicia_Fagerving_(WMSE)/sandbox2'
        play_file = os.path.join(MAPPINGS_DIR, 'plays.json')
        play_page = 'User:Alicia_Fagerving_WMSE/sandbox4'
        theatre_file = os.path.join(MAPPINGS_DIR, 'theatres.json')
        theatre_page = 'User:Alicia_Fagerving_(WMSE)/sandbox'
        helleday_file = os.path.join(MAPPINGS_DIR, 'linked_helleday.json')

        if update_mappings:
            print("Updating mappings...")
            self.mappings['photographers'] = self.get_photographer_mapping(
                photographer_page)
            self.mappings['theatres'] = self.get_theatre_mapping(theatre_page)
            self.mappings['depicted'] = self.get_depicted_mapping(
                depicted_page)
            self.mappings['plays'] = self.get_play_mapping(play_page)
            self.mappings['helleday_files'] = self.get_existing_helleday_files()
            common.open_and_write_file(
                theatre_file, self.mappings['theatres'], as_json=True)
            common.open_and_write_file(
                photographer_file, self.mappings['photographers'],
                as_json=True)
            common.open_and_write_file(
                depicted_file, self.mappings['depicted'], as_json=True)
            common.open_and_write_file(
                play_file, self.mappings['plays'], as_json=True)
            common.open_and_write_file(
                helleday_file, self.mappings['helleday_files'], as_json=True)
        else:
            self.mappings['photographers'] = common.open_and_read_file(
                photographer_file, as_json=True)
            self.mappings['theatres'] = common.open_and_read_file(
                theatre_file, as_json=True)
            self.mappings['depicted'] = common.open_and_read_file(
                depicted_file, as_json=True)
            self.mappings['plays'] = common.open_and_read_file(
                play_file, as_json=True)
            self.mappings['helleday_files'] = common.open_and_read_file(
                helleday_file, as_json=True)

        pywikibot.output('Loaded all mappings')

    def get_theatre_mapping(self, theatre_page):
        theatres = {}
        page = pywikibot.Page(self.commons, theatre_page)
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

    def get_photographer_mapping(self, photographer_page):
        page = pywikibot.Page(self.commons, photographer_page)
        data = listscraper.parseEntries(
            page.text,
            row_t='User:André Costa (WMSE)/mapping-row',
            default_params={'name': '', 'wikidata': '', 'frequency': ''})

        # load data on page
        photographer_ids = {}
        for entry in data:
            if entry['wikidata'] and entry['name']:
                wikidata = entry['wikidata'][0]
                name = entry['name'][0]
                if wikidata != '-':
                    photographer_ids[name] = wikidata

        # look up data on Wikidata
        photographer_props = {'P373': 'commonscat', 'P1472': 'creator'}
        photographers = {}
        for name, qid in photographer_ids.items():
            photographers[name] = self.load_wd_value(
                qid, photographer_props, self.photographer_cache)
        return photographers

    def get_play_mapping(self, play_page):
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

    def get_depicted_mapping(self, depicted_page):
        page = pywikibot.Page(self.commons, depicted_page)
        data = listscraper.parseEntries(
            page.text,
            row_t='User:André Costa (WMSE)/mapping-row',
            default_params={'name': '', 'wikidata': '', 'frequency': ''})

        # load data on page
        photographer_ids = {}
        for entry in data:
            if entry['wikidata'] and entry['name']:
                wikidata = entry['wikidata'][0]
                name = entry['name'][0]
                if wikidata != '-':
                    photographer_ids[name] = wikidata

        # look up data on Wikidata
        photographer_props = {'P373': 'commonscat'}
        photographers = {}
        for name, qid in photographer_ids.items():
            photographers[name] = self.load_wd_value(
                qid, photographer_props, self.photographer_cache)
            photographers[name]["wikidata"] = qid
        return photographers

    def get_existing_helleday_files(self):
        existing = {}
        kmb_pattern = "http://urn.kb.se/resolve?urn=urn:nbn:se:statensmusikverk-"
        gen = self.linksearch_generator(kmb_pattern, namespace=6)
        for hit in gen:
            existing[hit['url']] = hit['title']
        return existing

    def make_info_template(self, item):
        template_name = 'Musikverket-image'
        template_data = OrderedDict()
        template_data['title'] = item.image_title
        template_data['description'] = item.generate_description()
        template_data['photographer'] = item.generate_photographer()
        template_data['depicted people'] = item.generate_depicted_people()
        template_data['dimensions'] = item.generate_dimensions()
        template_data['department'] = item.generate_collection()
        template_data['date'] = item.generate_date()
        template_data['permission'] = item.generate_license()
        template_data['ID'] = item.id_no
        template_data['source'] = item.generate_source()
        template_data['other versions'] = item.get_other_versions()
        return helpers.output_block_template(template_name, template_data, 0)

    def process_data(self, raw_data):
        d = {}
        dom = parseString(utils.character_cleanup(raw_data))
        records = dom.getElementsByTagName("DScribeRecord")
        tagDict = {'description': 'Description',
                   'creator': 'UserWrapped5',
                   'depicted': 'UserText1',
                   'ensemble': 'UserText4',
                   'dimensions': 'DimensionValue',
                   'id_no': 'RefNo',
                   'image_date': 'Date',
                   'image_title': 'Title',
                   'image_type': 'UserWrapped2',
                   'part': 'UserText5',
                   'gender': 'UserText7',
                   'premiere': 'UserPeriod2',
                   'related_auth': 'RelatedNameCode',
                   'show_title': 'UserText3',
                   'collection': 'NamedCollection',
                   'thumbnail': 'Thumbnail',
                   'url': 'URL',
                   'keywords': 'Keyword'}
        for record in records:
            rec_dic = {}
            for tag in tagDict:
                xml_tag = tagDict[tag]
                try:
                    if tag == 'depicted':
                        id_tag = tagDict["related_auth"]
                        gender_tag = tagDict["gender"]
                        content = []
                        for i, el in enumerate(record.getElementsByTagName(xml_tag)):
                            person = {}
                            person_name = el.firstChild.nodeValue.strip()
                            person_id = record.getElementsByTagName(
                                id_tag)[i].firstChild.nodeValue.strip()
                            person["gender"] = record.getElementsByTagName(
                                gender_tag)[i].firstChild.nodeValue.strip()
                            person["name"] = person_name
                            person["id_no"] = person_id
                            content.append(person)
                    else:
                        content = record.getElementsByTagName(
                            xml_tag)[0].firstChild.nodeValue.strip()
                except (AttributeError, IndexError):
                    content = ""
                rec_dic[tag] = content
            id_no = rec_dic["id_no"]
            d[id_no] = HellItem(rec_dic, self)

        path = IMAGE_DIR
        for fname in listdir(path):
            img_code = "_".join(fname.split("_")[:2])
            if img_code not in [x for x in d]:
                print("File exists, no xml entry:", fname)
        self.data = d


class HellItem(object):

    def __init__(self, initial_data, hell_info):

        for key, value in initial_data.items():
            setattr(self, key, value)

        self.wd = {}  # store for relevant Wikidata identifiers
        self.content_cats = set()  # content relevant categories without prefix
        self.meta_cats = set()  # meta/maintenance proto categories
        self.hell_info = hell_info
        self.commons = pywikibot.Site('commons', 'commons')
        self.split_keywords()

    def generate_collection(self):
        library = "Musik- och teaterbiblioteket"
        return "{}, {}".format(library, self.collection)

    def generate_photographer(self):
        photographer_map = self.hell_info.mappings['photographers']
        photographer = None
        if self.creator and self.creator in photographer_map:
            creator = photographer_map[self.creator].get('creator')
            if creator:
                photographer = '{{Creator:%s}}' % creator
        return photographer or self.creator

    def generate_photographer_cat(self):
        photographer_map = self.hell_info.mappings['photographers']
        if self.creator and self.creator in photographer_map:
            self.content_cats.add(
                photographer_map[self.creator].get('commonscat'))

    def generate_depicted_people(self):
        depicted = " / ".join([utils.clean_name(x["name"])
                               for x in self.depicted])
        return depicted

    def generate_depicted_cat(self):
        depicted_map = self.hell_info.mappings['depicted']
        if self.depicted:
            for person in self.depicted:
                person_name = person["name"]
                if person_name in depicted_map:
                    self.content_cats.add(
                        depicted_map[person_name].get('commonscat'))

    def generate_yearly_cat(self):
        if self.image_date:
            if "-tal" in self.image_date:
                year = self.image_date.split("-")[0]
                tentative_cat = "Theatre in the {}s".format(year)
            else:
                tentative_cat = "{} in theatre".format(self.image_date)
            if self.hell_info.category_exists(tentative_cat):
                self.content_cats.add(tentative_cat)

    def generate_play_cat(self):
        play_map = self.hell_info.mappings['plays']
        if self.show_title and self.show_title in play_map:
            self.content_cats.add(play_map.get(self.show_title))

    def generate_portrait_cat(self):
        if "porträtt" in self.image_type.lower() and len(self.depicted) == 1:
            g = self.depicted[0]["gender"].lower()
            if g == "kvinna":
                gender = "women"
            elif g == "man":
                gender = "men"
            portrait_cat = "Portrait photographs of {}".format(gender)
            self.content_cats.add(portrait_cat)
        if self.image_type.lower() == "rollporträtt":
            self.content_cats.add("Theatrical costume in portraits")

    def generate_theatre_cat(self):
        general_cat = "Theatre of Sweden"
        theatre_map = self.hell_info.mappings['theatres']
        if self.ensemble and self.ensemble in theatre_map:
            cat = theatre_map.get(self.ensemble)
        else:
            cat = general_cat
        self.content_cats.add(cat)

    def generate_costume_cat(self):
        if "porträtt" in self.image_type.lower():
            if "scenkostymer" in self.keywords:
                self.content_cats.add("Theatrical costume in portraits")

    def generate_description(self):
        if not self.description.endswith("."):
            self.description += "."
        swedish = "{{{{sv|{}}}}}".format(self.description)
        return swedish

    def generate_source(self):
        template = '{{Musikverket cooperation project}}'
        info_link = '{{Musikverket-link|' + self.id_no + '}}'
        high_res_link = '[{} high resolution]'.format(self.url)
        text = "Swedish Performing Arts Agency: {}, {}".format(
            info_link, high_res_link)
        return "{}\n{}".format(text, template)

    def generate_license(self):
        template = "{{PD-old-70}}"
        return template

    def split_keywords(self):
        if self.keywords:
            self.keywords = [x.lower() for x in self.keywords.split(";")]
        else:
            self.keywords = []

    def generate_date(self):
        date = None
        if self.image_date:
            date = helpers.stdDate(self.image_date)
        return date

    def manually_parse_dimensions(self, dim_string):
        """18,3 x 11,6 cm or 16x25 cm"""
        parsed = None
        template = "{{{{Size|cm|{}|{}}}}}"
        if "x" in dim_string:
            split = dim_string.split("x")
            first = split[0].strip()
            second = split[1].strip().split(" ")[0]
            parsed = template.format(first, second)
        return parsed

    def generate_dimensions(self):
        keys = {
            'kabinettsporträtt': '{{Size|cm|12|16.5}}',
            'visitkort': '{{Size|cm|6.4|10.4}}'
        }
        if self.dimensions:
            dim_parsed = keys.get(self.dimensions.lower())
            if dim_parsed:
                return dim_parsed
            else:
                return self.manually_parse_dimensions(self.dimensions)

    def get_other_versions(self):
        gallery = None
        maybe_same = self.hell_info.mappings['helleday_files'].get(self.url)
        if maybe_same:
            gallery = '<gallery>\n{}\n</gallery>'.format(maybe_same)
            self.meta_cats.add('Media contributed by the Swedish Performing Arts Agency: with potential duplicates')
            return gallery


if __name__ == '__main__':
    HellInfo.main()
