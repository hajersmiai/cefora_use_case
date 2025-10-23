
import pandas as pd
import os

class TaxonomyLoader:
    """
    Loads and merges multilingual Belgian skill taxonomies
    from an Excel file (with multiple worksheets).
    """

    def __init__(self, excel_path: str):
        if not os.path.exists(excel_path):
            raise FileNotFoundError(f"Taxonomy Excel not found: {excel_path}")
        self.excel_path = excel_path

    def load_all(self):
        # Read all sheets from Excel
        xls = pd.ExcelFile(self.excel_path)
        taxonomy_frames = []

        for sheet_name in xls.sheet_names:
            df = xls.parse(sheet_name)
            df["category"] = sheet_name.strip().lower()
            df = self._normalize_columns(df)
            taxonomy_frames.append(df)

        taxonomy_df = pd.concat(taxonomy_frames, ignore_index=True)
        taxonomy_df = taxonomy_df.drop_duplicates(subset=["skill_nl", "skill_fr", "skill_en"])
        taxonomy_df = taxonomy_df.dropna(subset=["skill_nl", "skill_fr"], how="all")

        print(f"✅ Loaded taxonomy: {len(taxonomy_df)} total standardized skills from {len(xls.sheet_names)} sheets.")
        return taxonomy_df

    def _normalize_columns(self, df):
        """
        Normalize inconsistent column names across different taxonomy sheets.
        Detects and renames NL / FR / EN columns for skills.
        """
        rename_map = {
            # Soft skills
            "SS NL": "skill_nl",
            "SS FR": "skill_fr",
            # Digital skills
            "DS NL": "skill_nl",
            "DS FR": "skill_fr",
            # Essential/Optional skills
            "Block_txt_NL": "skill_nl",
            "Block_txt_FR": "skill_fr",
            # Other skills
            "AI NL": "skill_nl",
            "AI FR": "skill_fr",
            # General fallback names
            "Skill NL": "skill_nl",
            "Skill FR": "skill_fr",
            "Skill EN": "skill_en"
        }

        df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        # Add missing columns safely
        for col in ["skill_nl", "skill_fr", "skill_en"]:
            if col not in df.columns:
                df[col] = None

        # Retain relevant columns
        df = df[["skill_nl", "skill_fr", "skill_en", "category"]]
        return df
