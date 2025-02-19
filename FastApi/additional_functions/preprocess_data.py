import pandas as pd
import numpy as np
import logging
import os

logging.basicConfig(filename='preprocess_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_column_names_and_values(df: pd.DataFrame, threshold: int = 32) -> pd.DataFrame:
    """
    Shortens column names and values to ensure they are below a length threshold.

    Args:
        df (pd.DataFrame): Input DataFrame.
        threshold (int): Maximum allowed length. Default is 32.

    Returns:
        pd.DataFrame: DataFrame with sanitized names/values.
    """
    def shorten_text(text, threshold):
        if isinstance(text, str) and len(text) > threshold:
            part_len = (threshold - 5) // 2
            return f"{text[:part_len]}...{text[-part_len:]}" if part_len > 0 else text[:threshold]
        return text

    # Shorten column names
    df.columns = [shorten_text(col, threshold) for col in df.columns]

    # Shorten values
    for col in df.columns:
        unique_values = df[col].unique()
        value_map = {}
        for val in unique_values:
            shortened = shorten_text(val, threshold)
            value_map[val] = shortened
        df[col] = df[col].map(value_map)

    return df

def preprocess_data(file_path, user_folder):
    actions_performed = []
    try:
        # Load data
        try:
            df = pd.read_csv(file_path, encoding='utf-8', low_memory=False)
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='ISO-8859-1', low_memory=False)
        actions_performed.append("Loaded CSV file")

        # Drop all-NaN columns/rows
        df = df.dropna(axis=1, how='all')
        actions_performed.append("Dropped columns with all NaN values")
        df = df.dropna(how='all')
        actions_performed.append("Dropped rows with all NaN values")

        # Step 1: Remove columns with ≥75% missing/0 values
        threshold_rows = 0.75 * len(df)
        columns_to_drop = []
        for col in df.columns:
            if pd.api.types.is_numeric_dtype(df[col]):
                invalid = (df[col].isna() | (df[col] == 0)).sum()
            else:
                invalid = df[col].isna().sum()
            if invalid >= threshold_rows:
                columns_to_drop.append(col)
        
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            actions_performed.append(f"Dropped columns: {columns_to_drop}")
        
        # Step 2: Remove identical columns
        identical_cols = [col for col in df.columns if df[col].nunique() <= 1]
        if identical_cols:
            df.drop(columns=identical_cols, inplace=True)
            actions_performed.append(f"Dropped identical columns: {identical_cols}")

        # Step 3: Remove duplicate columns
        df = df.loc[:, ~df.columns.duplicated()]
        actions_performed.append("Removed duplicate columns")

        # Column type handling
        type_mapping = {"Customer ID": str, "Product ID": str, "ZIP": str}
        for col, dtype in type_mapping.items():
            if col in df.columns:
                df[col] = df[col].astype(dtype).str.replace(r'\.0$', '', regex=True)

        # Drop specific columns
        for col in ["CHAIN", "ITEM"]:
            if col in df.columns:
                df.drop(columns=col, inplace=True)
                actions_performed.append(f"Dropped {col}")

        # Sanitize names/values
        df = sanitize_column_names_and_values(df)

        # Save cleaned data
        cleaned_path = f'FastApi/src/uploads/{user_folder}/cleaned_data.csv'
        df.to_csv(cleaned_path, index=False)
        actions_performed.append(f"Saved cleaned data to {cleaned_path}")

        logging.info(f"Actions: {', '.join(actions_performed)}")
        return {"actions": actions_performed, "file_path": cleaned_path}

    except Exception as e:
        logging.error(f"Error: {e}")
        raise ValueError(f"Preprocessing error: {e}")