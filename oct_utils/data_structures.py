import hashlib
from io import StringIO

import numpy as np
import pandas as pd

from oct_utils.conventions import controls_alias_hack

POSTERIOR_POLE_TABLE_NAME = "posterior_pole_data"

class PosteriorPoleData:
    table_name: str = POSTERIOR_POLE_TABLE_NAME
    alias: str = ""
    laterality:  str = ""
    age_at_test: float = -1
    total_volume: float = -1
    pp_map: pd.DataFrame  | None = None
    weights: pd.DataFrame | None = None
    interpolated_map: pd.DataFrame | None = None
    choroid_ok: bool = True
    filename: str | None = None
    filename_md5: str | None = None
    avg_thickness: float | None = None
    wtd_avg_thickness: float | None = None

    def __init__(self, alias="", laterality="", age_at_test=-1):
        self.alias = alias
        self.laterality = laterality
        self.age_at_test = age_at_test
        self.pp_map  = pd.DataFrame(np.full((8, 8), np.nan))
        self.weights = pd.DataFrame(np.full((8, 8), 100.0, dtype=float))


    def __str__(self):
        retstr = f"alias: {self.alias}\n"
        retstr += f"file name: {self.filename}\n"
        retstr += f"file md5: {self.filename_md5}\n"
        retstr += f"laterality: {self.laterality}\n"
        retstr += f"age at test: {self.age_at_test}\n"
        retstr += f"total macular volume: {self.total_volume}\n"
        retstr += f"posterior pole map:\n"
        retstr += f"{self.pp_map}\n"
        retstr += f"weights:\n"
        retstr += f"{self.weights}\n"
        if self.interpolated_map is not None:
            retstr += f"interpolated map:\n"
            retstr += f"{self.interpolated_map}\n"

        return retstr

    def pd_dataframe_store(self, oct_df: pd.DataFrame, fussy: bool = True, xml_dir_path: str | None = None):
        """
        Appends the current instance's data to an existing pandas dataframe.
        """
        if fussy:
            if self.filename is None or self.filename_md5 is None or xml_dir_path is None:
                raise ValueError("Fussy, filename,  xml_dir_path and filename_md5 must be specified")


        # Serialize DataFrames to JSON strings
        pp_map_json = self.pp_map.to_json() if self.pp_map is not None else None
        interpolated_map_json = self.interpolated_map.to_json() if self.interpolated_map is not None else None

        fnm = self.filename
        # 'calculated'  because it can be checked against the value stored in db or some such
        # (not implemented here yet)
        calculated_md5 = hashlib.md5(open(f"{xml_dir_path}/{fnm}",'rb').read()).hexdigest()

        update_fields = {'alias': self.alias,
                         'eye': self.laterality,
                         'age_acquired': self.age_at_test,
                         'file_name': self.filename,
                         'file_md5': calculated_md5,
                         'total_volume': self.total_volume,
                         'choroid_ok': self.choroid_ok,
                         'pp_map': pp_map_json,
                         'interpolated_map': interpolated_map_json
                         }
        if not set(update_fields.keys()).issubset(set(oct_df.columns)):
            raise ValueError("Dictionary keys do not match dataframe columns")

        new_row = {col: update_fields.get(col, None) for col in oct_df.columns}

        oct_df.loc[len(oct_df)] = new_row  # Append row in place using loc


    def pd_df_store_minimal(self, oct_df: pd.DataFrame):
        """
        Appends the current instance's data to an existing pandas dataframe.
        """
        update_fields = {'alias': self.alias,
                         'eye': self.laterality,
                         'age_acquired': self.age_at_test,
                         'file_name': self.filename,
                         'file_md5': self.filename_md5,
                         'avg_thickness': self.avg_thickness,
                         'wtd_avg_thickness': self.wtd_avg_thickness
                         }

        if not set(update_fields.keys()).issubset(set(oct_df.columns)):
            raise ValueError("Dictionary keys do not match dataframe columns")

        new_row = {col: update_fields.get(col, None) for col in oct_df.columns}

        oct_df.loc[len(oct_df)] = new_row  # Append row in place using loc

    def pd_dataframe_read(self, oct_df: pd.DataFrame, index: int, fussy: bool = True, xml_dir_path: str | None = None):
        """
        Reads data from a pandas dataframe row and populates the current instance's attributes.
        """
        if index not in oct_df.index:
            raise ValueError(f"Index {index} not found in dataframe")

        row = oct_df.loc[index]

        # Populate basic attributes
        self.alias = row['alias']
        if "control" in self.alias.lower(): controls_alias_hack(self)
        self.laterality = row['eye']
        self.age_at_test = row['age_acquired']
        self.filename = row['file_name']
        self.filename_md5 = row['file_md5']
        self.total_volume = row['total_volume']
        self.choroid_ok = row['choroid_ok']

        # Deserialize DataFrames from JSON strings
        self.pp_map = pd.read_json(StringIO(row['pp_map'])) if pd.notna(row['pp_map']) else None
        self.interpolated_map = pd.read_json(StringIO(row['interpolated_map'])) if pd.notna(row['interpolated_map']) else None

        # MD5 verification in fussy mode
        if fussy:
            if self.filename is None or self.filename_md5 is None or xml_dir_path is None:
                raise ValueError("Fussy mode requires filename, filename_md5, and xml_dir_path")
            dir_path = f"{xml_dir_path}/{self.alias.replace(" ", "_")}/{self.laterality}"
            calculated_md5 = hashlib.md5(open(f"{dir_path}/{self.filename}", 'rb').read()).hexdigest()

            if calculated_md5 != self.filename_md5:
                raise ValueError(f"MD5 mismatch for {self.filename}: expected {self.filename_md5}, got {calculated_md5}")
