import io

import pandas as pd
from fastapi import UploadFile


def read_df_from_file(file: UploadFile) -> pd.DataFrame:
    filename = file.filename or ""
    if filename.endswith(".csv"):
        return pd.read_csv(file.file)
    return pd.read_excel(file.file)


def read_df_from_bytes(content: bytes, filename: str) -> pd.DataFrame:
    if filename.endswith(".csv"):
        return pd.read_csv(io.BytesIO(content))
    return pd.read_excel(io.BytesIO(content))
