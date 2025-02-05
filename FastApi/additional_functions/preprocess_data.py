import pandas as pd
import numpy as np
import logging
import os

# Set up logging
logging.basicConfig(filename='preprocess_log.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

def sanitize_column_names_and_values(user_folder1:str, file_path: str, threshold: int = 32) -> pd.DataFrame:
    """
    Reads a CSV file, shortens column names and values, and dynamically shortens unique values 
    for each column while ensuring a consistent format.

    Args:
        file_path (str): The path to the CSV file.
        threshold (int): The maximum length allowed for column names and values. Default is 25.

    Returns:
        pd.DataFrame: The DataFrame with sanitized column names and values.
    """
    # Read the CSV file
    df = pd.read_csv(file_path, index_col=0)

    # Sanitize column names
    def shorten_text(text, start_len=7, middle_start=10, middle_end=18, end_len=7):
        if isinstance(text, str) and len(text) > threshold:
            return f"{text[:start_len]}...{text[middle_start:middle_end]}...{text[-end_len:]}"
        return text

    df.columns = [shorten_text(col) for col in df.columns]

    # Sanitize values
    for col in df.columns:
        value_dict = {}  # Dictionary to track unique values
        start_len, middle_start, middle_end, end_len = 7, 11, 20, 9  # Initial formula

        def process_value(value):
            nonlocal start_len, middle_start, middle_end, end_len
            if value not in value_dict:
                if isinstance(value, str) and len(value) > threshold:
                    shortened = f"{value[:start_len]}...{value[middle_start:middle_end]}...{value[-end_len:]}"
                    value_dict[value] = shortened

                    # Increment formula for the next unique value
                    start_len += 1
                    middle_start += 1
                    middle_end += 1
                    end_len += 1
                else:
                    value_dict[value] = value  # Keep original for short values
            return value_dict[value]

        df[col] = df[col].apply(process_value)

    #cleaned_file_path = f'FastApi/src/uploads/{user_folder1}/AI_cleaned_f.csv' #NOTE if needed new df file
    #df.to_csv(cleaned_file_path, index=False)
    return df

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

        #test type preprocessing
        column_type_mapping = {
            "Customer ID": str,  # Convert to string
            "Product ID": str,   # Convert to string
            "sales": float,
            "Customer": str,
            "ITEM": str,
            "ZIP": str,
            "item code": str
        }
        try:
            for column, dtype in column_type_mapping.items():
                if column in df.columns:
                    df[column] = df[column].astype(str).str.rstrip(".0")
                    #print(df[column])
            # Preprocess the data
            df.drop(columns=['ITEM'], inplace=True)
        
        except Exception  as e:
            logging.error(f"Error during preprocessing type: {e}")
            
        try:
            df = sanitize_column_names_and_values(user_folder, file_path)    
        except Exception as e:
            logging.error(f"Error during make shorter columns(value) names: {e}")
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

#preprocess_data(r"FastApi\\src\uploads\\5c6ccb33-da82-454d-8767-a2cff0116263\\HCF Calculate GE Sales 20240930 (1).csv",'5c6ccb33-da82-454d-8767-a2cff0116263')