import pandas as pd
import logging
logger = logging.getLogger(__name__)
import re
from FastApi.AI_instruments.AI_df_preprocced import file_columns_to_drop
def AI_drop_col_csv(file_path: str, df_path: str, path_for_drop_col_list: str):
    try:
        try:
            file_columns_to_drop(file_path, path_for_drop_col_list)
        except Exception as e:
            logger.error(f"Error in file_columns_to_drop: {e}")
            #print(f"Error in file_columns_to_drop: {e}")
        
        with open(path_for_drop_col_list, 'r') as file:
            content = file.read()

        code_blocks = re.findall(r'```python(.*?)```', content, re.DOTALL)

        lst = []
        for i, code_block in enumerate(code_blocks, start=1):
            #print(f"Found columns to drop block {i}...\n")

            lst = [code_block]
            drop_columns_lst = lst[0]

            columns_to_drop = eval(drop_columns_lst.strip())


        try:
            encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
            for encoding in encodings:
                try:
                    df = pd.read_csv(file_path, encoding=encoding, low_memory=False) 
                    df = df.copy()
                    break  # Exit loop once successful
                except UnicodeDecodeError:
                    logger.error(f"Failed to decode df AI with: {e}")
                    raise Exception(f"Failed to decode df AI with: {encoding}")
            

        except Exception as e:
            print(f'Error in df reading - cleand_df: {e}')
        
        try:
            df_dropped = df.drop(columns=columns_to_drop, errors='ignore')
            logger.info(f"AI droped columns: {columns_to_drop}")
            df_dropped.to_csv(f'{df_path}/AI_cleaned.csv')
            #print(df_dropped.head(2))
        except Exception as e:
            logger.error(f'Error in columns df AI drop: {e}')
            #print(f'Error in columns df AI drop: {e}')    
        
        #exec(code_block)
        return f'{df_path}/AI_cleaned.csv'    
            
    except Exception as e:
            logger.error(f'Error in main df AI drop: {e}')
            #print(f"An error occurred: {e}")