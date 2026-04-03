import pandas as pd
import os

def load_csvs(data_folder: str = "data") -> dict:
    """
    Loads all CSVs from the data folder.
    Returns a dict like {"superstore": <DataFrame>, ...}
    """
    dataframes = {}

    if not os.path.exists(data_folder):
        print(f"[Loader] Folder '{data_folder}' not found.")
        return dataframes

    for filename in os.listdir(data_folder):
        if filename.endswith(".csv"):
            name = filename.replace(".csv", "")
            filepath = os.path.join(data_folder, filename)
            try:
                df = pd.read_csv(filepath, encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(filepath, encoding="latin1")
            
            dataframes[name] = df
            print(f"[Loader] Loaded '{filename}' — {df.shape[0]} rows, {df.shape[1]} columns")

    return dataframes


def get_dataframe_summary(dataframes: dict) -> str:
    """
    Returns a text summary of all loaded dataframes.
    Useful for giving the LLM context about what data is available.
    """
    summary_parts = []

    for name, df in dataframes.items():
        cols = ", ".join(df.columns.tolist())
        summary_parts.append(
            f"Dataset: '{name}'\n"
            f"Rows: {df.shape[0]} | Columns: {df.shape[1]}\n"
            f"Column names: {cols}\n"
            f"Sample values:\n{df.head(2).to_string(index=False)}"
        )

    return "\n\n".join(summary_parts)