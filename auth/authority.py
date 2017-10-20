#!/usr/bin/python
# -*- coding: utf-8  -*-
import argparse
import batchupload.common as common
import batchupload.helpers as helpers
from xml.dom.minidom import parseString
import utils
import os
import re
import json

MAPPINGS = "mappings"


class Person(object):

    def process_names(self):
        other_names = []
        if self.isPerson:
            self.data["clean"]["full_name"] = self.data["first"] + \
                " " + self.data["last"]
            self.data["clean"]["first"] = self.data["first"].split(" ")
            self.data["clean"]["last"] = self.data["last"]
        else:
            self.data["clean"]["full_name"] = self.data["corporate_name"]

        if self.data.get("parallell_name"):
            for n in helpers.flip_name(self.data.get("parallell_name")).split(";"):
                other_names.append(n)
        if self.data.get("not_preferred_name"):
            for n in helpers.flip_name(self.data.get("not_preferred_name")).split(";"):
                other_names.append(n)
        self.data["clean"]["other_names"] = other_names

    def attempt_exact_dates(self):
        raw = self.data["dates_places"].lower()
        pattern_born = re.compile("född [0-9]{4}-[0-9]{2}-[0-9]{2}")
        pattern_dead = re.compile("död [0-9]{4}-[0-9]{2}-[0-9]{2}")
        if pattern_born.findall(raw):
            self.data["clean"]["birth"] = helpers.isoDate(pattern_born.findall(raw)[
                0].split(" ")[1])
        if pattern_dead.findall(raw):
            self.data["clean"]["death"] = helpers.isoDate(pattern_dead.findall(raw)[
                0].split(" ")[1])

    def process_dates(self):
        if "-" in self.data["dates"]:
            birth = self.data["dates"].split("-")[0].strip()
            death = self.data["dates"].split("-")[1].strip()
            if "?" not in birth:
                self.data["clean"]["birth"] = birth
            if "?" not in death:
                self.data["clean"]["death"] = death
            self.attempt_exact_dates()

    def split_professions(self):
        professions = []
        delimiter = ","
        if ";" in self.data["profession"]:
            delimiter = ";"
        for prof in (self.data["profession"].split(delimiter)):
            prof_clean = prof.lower().strip()
            if prof_clean:
                professions.append(prof_clean)
        if professions:
            self.data["clean"]["professions"] = professions

    def process_gender(self):
        self.data["clean"]["gender"] = self.data["gender"].lower()

    def construct_url(self):
        base_url = "http://calmview.musikverk.se/CalmView/Record.aspx?src=CalmView.Persons&id={}"
        self.data["clean"]["url"] = base_url.format(self.data["id_no"])

    def process_id(self):
        self.data["clean"]["id_no"] = self.data["id_no"]

    def set_type(self):
        if self.data["corporate_name"]:
            self.data["clean"]["type"] = "organization"
            self.isPerson = False
        else:
            self.data["clean"]["type"] = "person"
            self.isPerson = True

    def __init__(self, raw_data):
        self.data = raw_data
        self.data["clean"] = {}
        self.set_type()
        self.construct_url()
        self.process_id()
        self.process_names()
        if self.data["clean"]["type"] == "person":
            self.split_professions()
            self.process_dates()
            self.process_gender()


def load_data(in_file):
    return common.open_and_read_file(in_file, as_json=False)


def xml_to_people(raw):
    raw = utils.character_cleanup(raw)
    people = []
    dom = parseString(raw)
    records = dom.getElementsByTagName("DScribeRecord")
    tags = {
        'last': 'Surname',
        'full': 'PersonName',
        'first': 'Forenames',
        'dates_places': 'DatesAndPlaces',
        'dates': 'Dates',
        'gender': 'Gender',
        'id_no': 'Code',
        'corporate_name': 'CorporateName',
        'profession': 'Epithet',
        'parallell_name': "ParallelEntry",
        'not_preferred_name': 'NonPreferredTerm'
    }
    for record in records:
        person = {}
        for tag in tags:
            lookup = tags[tag]
            try:
                content = record.getElementsByTagName(
                    lookup)[0].firstChild.nodeValue
            except (AttributeError, IndexError):
                content = ""
            person[tag] = content.strip()
        people.append(Person(person))
    return people


def people_to_file(people, filename):
    dump = []
    for person in people:
        dump.append({person.data["id_no"]: person.data["clean"]})
    with open(filename, 'w') as f:
        json.dump(dump, f, sort_keys=True,
                  indent=4,
                  ensure_ascii=False)


def main(arguments):
    raw_xml = load_data(arguments.in_file)
    people = xml_to_people(raw_xml)
    people_to_file(people, "authority.json")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--in_file", default="authority.xml")
    args = parser.parse_args()
    main(args)
