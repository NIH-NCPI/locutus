
"""Abstraction of harmony exports. 

The real work here is done at the relevant model, however, those classes 
will call this the appropriate object's functions to get the correct 
column headers and format. 

"""
from enum import StrEnum 
from datetime import datetime 

import pdb


FTD_DATE_FORMAT = "%Y-%m-%d"

class HarmonyFormat(StrEnum):
    Whistle = "Whistle"
    FTD = "FTD"

class HarmonyOutputFormat(StrEnum):
    CSV = "CSV"
    JSON = "JSON"

def harmony_exporter(harmony_format=HarmonyFormat.Whistle, 
                output_format=HarmonyOutputFormat.JSON):
    if harmony_format==HarmonyFormat.Whistle:
        return WhistleHarmony(output_format=output_format)
    else:
        return FtdHarmony(output_format=output_format)

class HarmonyBase:
    # For any derived class that wants a different header, we'll
    # use the map to offset any differences
    _header_map = {}
    _header_base = [
        "study_title",
        "study_name",
        "study_id",
        "dd_name",
        "dd_id",
        "version",
        "source_text",
        "source_description",
        "source_domain",
        "parent_varname",
        "source_system",
        "mapping_relationship",
        "mapped_code",
        "mapped_display",
        "mapped_system", 
        "comment"
    ]
    def __init__(self, output_format):
        self.output_format = output_format 
        self.data = [] 
    
    def header(self):
        return [self._header_map[col] if col in self._header_map else col for col in self._header_base]

    def init_data(self):
        # use default column names unless there is a special mapping for it
        # in _header_map 
        if self.output_format == HarmonyOutputFormat.CSV:
            if len(self.data) == 0:
                self.data.append(self.header())
                return self.data[0]


        # for JSON files, we'll merge them into the objects 
        # as properties so no header needed

    def add_row(self, 
        study_title="", 
        study_name="",
        study_id="",
        dd_name="",
        dd_id="",
        version="",
        source_text="",
        source_description="",
        source_domain="",
        parent_varname="",
        source_system="",
        mapping_relationship="",
        mapped_code="",
        mapped_display="",
        mapped_system="",
        comment=""
    ):
        rows_to_return = []

        if self.output_format == HarmonyOutputFormat.CSV:
            if len(self.data) == 0:
                row = self.init_data()
                if row is not None:
                    rows_to_return.append(row)
            row = []

            for col in self._header_base:
                row.append(locals()[col])
            self.data.append(row)
            rows_to_return.append(row)

        else:
            row = {}
            for col in self._header_base:
                if col in self._header_map:
                    row[self._header_map[col]] = locals()[col]
                else:
                    row[col] = locals()[col]

            self.data.append(row)
            rows_to_return.append(row)

        return rows_to_return 

class WhistleHarmony(HarmonyBase):
    _header_map = {
        "source_text":"local code",
        "source_description":"text",
        "source_domain": "table_name",
        "parent_varname": "parent_varname",
        "source_system":"local code system",
        "mapped_code":"code",
        "mapped_display":"display",
        "mapped_system":"code system"
    }

    def __init__(self, output_format):
        super().__init__(output_format)

class FtdHarmony(HarmonyBase):
    # No need for header map for this one
    def __init__(self, output_format):
        super().__init__(output_format)


def basic_date(t=None):
    if t is None:
        t = datetime.now()
    return t.strftime(FTD_DATE_FORMAT)