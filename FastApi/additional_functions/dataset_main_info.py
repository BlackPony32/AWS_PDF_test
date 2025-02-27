import pandas as pd
import io

def extract_main_info(df: pd.DataFrame) -> dict:
    # Capture .info() as a string using a buffer
    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()
    
    # Create dictionary to store all the extracted information
    data_summary = {
        'head': df.head().to_dict(),  # First 5 rows of the dataframe as a dictionary
        'describe': df.describe(include='all').to_dict(),  # Descriptive statistics of all columns
        'info': info_str,  # DataFrame info as a string
        'missing_values': df.isnull().sum().to_dict(),  # Count of missing values for each column
        'column_types': df.dtypes.to_dict(),  # Data types of each column
        'shape': df.shape  # Shape of the dataset (rows, columns)
    }
    
    return data_summary

# Example usage:
#df = pd.read_csv('FastApi/src/uploads/a2fc8600-e059-4c81-9dd6-bd2b467b32c2/AI_cleaned.csv')
#summary = extract_main_info(df)
#print(summary)
