import pandas as pd
import numpy as np
import logging
import os

# Set up logging
logging.basicConfig(filename='preprocess_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def preprocess_data(file_path, user_folder):
    """
    Preprocess the input CSV or Excel file:
    - Loads CSV or converts Excel to CSV.
    - Removes columns with 75% or more missing, None, or 0 values.
    - Removes columns where all values are identical.
    - Logs the preprocessing steps and actions performed.

    Parameters:
    file_path (str): Path to the input file (CSV or Excel).

    Returns:
    dict: Dictionary with details of actions performed and the path to the cleaned file.
    """
    actions_performed = []

    try:
        try:
            df = pd.read_csv(file_path, encoding= 'utf-8', low_memory=False)  # First attempt with default encoding
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='ISO-8859-1', low_memory=False)  # Retry with Latin-1 encoding
        actions_performed.append("Loaded CSV file")
        # Step 1: Remove columns with 75% or more missing, None, or 0 values
        threshold = 0.75 * len(df)
        columns_to_drop = [col for col in df.columns if df[col].isnull().sum()  >= threshold]
        
        if columns_to_drop:
            df.drop(columns=columns_to_drop, inplace=True)
            try:
                if "CHAIN" in df.columns:
                    df.drop(columns=["CHAIN"], inplace=True)
                    actions_performed.append("CHAIN column was dropped.")
                else:
                    actions_performed.append("There is no CHAIN column.")

            except ValueError:
                actions_performed.append("There is no CHAIN column")
            actions_performed.append(f"Dropped columns with >= 75% missing or invalid values: {columns_to_drop}")
        else:
            actions_performed.append("No columns dropped due to missing or invalid values")

        # Step 2: Remove columns where all values are identical
        identical_columns = [col for col in df.columns if df[col].nunique() <= 1]
        
        if identical_columns:
            df.drop(columns=identical_columns, inplace=True)
            actions_performed.append(f"Dropped columns with all identical values: {identical_columns}")
        else:
            actions_performed.append("No columns dropped due to identical values")

        # Step 3: Remove duplicate columns
        original_columns = df.columns
        df = df.loc[:, ~df.columns.duplicated()]
        if len(original_columns) != len(df.columns):
            actions_performed.append(f"Removed duplicate columns. Columns reduced from {len(original_columns)} to {len(df.columns)}")

        # Save the cleaned data to a new CSV file
        cleaned_file_path = f'FastApi/src/uploads/{user_folder}/cleaned_data.csv'
        df.to_csv(cleaned_file_path, index=False)
        actions_performed.append(f"Saved cleaned data to {cleaned_file_path}")

        # Log all actions performed
        logging.info(f"Preprocessing complete. Actions performed: {', '.join(actions_performed)}")

        return {"actions": actions_performed, "file_path": cleaned_file_path}

    except Exception as e:
        logging.error(f"Error during preprocessing: {e}")
        raise ValueError(f"Error during preprocessing: {e}")

#preprocess_data("uploads\GNGR_20240420 .csv")