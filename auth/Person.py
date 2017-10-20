# -*- coding: utf-8 -*-
"""An object that represent a Wikidata item of a Swedish nature area."""
from WikidataItem import WikidataItem

import importer_utils as utils


class Person(WikidataItem):
    def add_statement(self, prop_name, value, quals=None, ref=None):
        return super().add_statement(prop_name, value, quals, self.source)

    def create_sources(self):
        url = self.raw_data.get("url")
        publication_date = "2017-10-06"
        retrieval_date = "2017-10-06"
        self.source = self.make_stated_in_ref("Q42160060",
                                              publication_date,
                                              url, retrieval_date)

    def set_id(self):
        id_no = self.raw_data.get("id_no")
        self.add_statement("musikverket_id", id_no)

    def set_dates(self):
        date_of_birth = self.raw_data.get("birth")
        if date_of_birth:
            dob = None
            dob_pwb = None
            if "-" in date_of_birth:
                dob = utils.date_to_dict(date_of_birth, "%Y-%m-%d")
            elif len(date_of_birth) == 4:
                dob = utils.date_to_dict(date_of_birth, "%Y")
            if dob:
                dob_pwb = self.make_pywikibot_item({"date_value": dob})
                self.add_statement("dob", dob_pwb)

        date_of_death = self.raw_data.get("death")
        if date_of_death:
            dod = None
            dod_pwb = None
            if "-" in date_of_death:
                dod = utils.date_to_dict(date_of_death, "%Y-%m-%d")
            elif len(date_of_death) == 4:
                dod = utils.date_to_dict(date_of_death, "%Y")
            if dod:
                dod_pwb = self.make_pywikibot_item({"date_value": dod})
                self.add_statement("dod", dod_pwb)

    def set_is(self):
        this_is = self.raw_data.get("type")
        if this_is == "person":
            self.add_statement("is", "Q5")
        elif this_is == "organization":
            self.add_statement("is", "Q43229")

    def set_gender(self):
        gender = self.raw_data.get("gender")
        if gender:
            if gender == "kvinna":
                wd_gender = "Q6581072"
            elif gender == "man":
                wd_gender = "Q6581097"
            self.add_statement("gender", wd_gender)

    def match_professions(self):
        prof = self.raw_data.get("professions")
        if prof:
            for p in prof:
                attempt = self.professions.get(p)
                if attempt:
                    self.add_statement("profession", attempt)

    def match_last_name(self):
        l_name = self.raw_data.get("last")
        if l_name:
            attempt = [x for x in self.last if x["itemLabel"] == l_name]
            if len(attempt) == 1:
                self.add_statement(
                    "last_name", attempt[0]["item"].split("/")[-1])

    def match_first_names(self):
        f_names = self.raw_data.get("first")
        if f_names:
            for f in f_names:
                attempt = [x for x in self.first if x["itemLabel"] == f]
                if len(attempt) == 1:
                    self.add_statement(
                        "first_name", attempt[0]["item"].split("/")[-1])

    def match_wikidata(self):
        attempt = self.existing.get(self.raw_data["id_no"])
        if attempt:
            self.associate_wd_item(attempt)

    def set_labels(self):
        self.add_label("sv", utils.remove_multiple_spaces(self.raw_data["full_name"].strip()))
        if self.raw_data.get("other_names"):
            for n in self.raw_data["other_names"]:
                if "(" in n:
                    n = utils.get_rid_of_brackets(n)
                self.add_label("sv", utils.remove_multiple_spaces(n.strip()))

    def __init__(self, raw_data, repository, data_files, existing):
        WikidataItem.__init__(self, raw_data, repository, data_files, existing)
        self.first = data_files["first"]
        self.last = data_files["last"]
        self.professions = data_files["professions"]
        self.create_sources()
        self.set_id()
        self.set_is()
        self.set_gender()
        self.match_wikidata()
        self.match_first_names()
        self.match_last_name()
        self.match_professions()
        self.set_dates()
        self.set_labels()
        print(self.wd_item["labels"])
