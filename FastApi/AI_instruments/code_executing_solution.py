import re
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os
import kaleido
# Ensure folders exist

    
def extract_and_execute_code(file_path, user_folder):
    """
    Extracts Python code blocks from a file and executes them.
    :param file_path: Path to the text file containing Python code blocks.
    """
    plots_FOLDER = f'FastApi/src/plots/{user_folder}'
    summary_FOLDER = f'FastApi/src/summary/{user_folder}'
    if not os.path.exists(plots_FOLDER):
        os.makedirs(plots_FOLDER)
    if not os.path.exists(summary_FOLDER):
        os.makedirs(summary_FOLDER)

    try:
        new_lines = [
    f"user_folder = '{user_folder}'",
    f"plots_dir = f'FastApi/src/plots/{user_folder}'",
    f"sum_dir = f'FastApi/src/summary/{user_folder}'",
    "def df_func(user_folder):",
    "    df = None  # Initialize df to None to avoid UnboundLocalError",
    "    try:",
    "        encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']",
    "        for encoding in encodings:",
    "            try:",
    "                df = pd.read_csv(f'FastApi/src/uploads/{user_folder}/cleaned_data.csv', encoding=encoding, low_memory=False)",
    "                break  # Exit loop once successful",
    "            except UnicodeDecodeError:",
    "                raise Exception(f\"Failed to decode with: {encoding}\")",
    "        #print(df.head())",
    "        ",
    "        if df is None:",
    "            print(\"Failed to read the file with any encoding.\")",
    "        return df  # Will return None if no encoding works",
    "",
    "    except Exception as e:",
    "        raise Exception(f\"Error while reading file: {e}\")",
    "        return None  # Return None if there was another error outside of decoding",
    "",
    "df = df_func(user_folder)",
    "if df is None:",
    "    try:",
    "        df = pd.read_csv(f'FastApi/src/uploads/{user_folder}/cleaned_data.csv', low_memory=False)",
    "        #print(df.head())",
    "    except Exception as e:",
    "        raise Exception(f\"Error while reading file 2: {e}\")",
    "#print(df.head)"
]
    except Exception as e:
        pass

    # Read the original file content
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Insert the new lines between the 5th and 6th lines (index 4 and 5)
    lines[4:4] = [line + '\n' for line in new_lines]

    # Write the modified content back to the file
    with open(file_path, 'w') as file:
        file.writelines(lines)
    
    
    try:
        # Read the content of the file
        with open(file_path, 'r') as file:
            content = file.read()

        # Regex pattern to extract code blocks between ```python and ```
        code_blocks = re.findall(r'```python(.*?)```', content, re.DOTALL)

        ## For each extracted code block, execute it
        for i, code_block in enumerate(code_blocks, start=1):
           print(f"Executing code block {i}...\n")
        #   try:
        #       encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']  # список можливих енкодингів
        #       for encoding in encodings:
        #           try:
        #               #global df
        #               df = pd.read_csv(f'FastApi\\src\\uploads\\{user_folder}\\cleaned_data.csv', encoding=encoding,engine='python')
        #           except UnicodeDecodeError:
        #               print(f"Failed decode with: {encoding}")
        #   except Exception as e:
        #       print(e)
        #   #print(df.head())
           exec(code_block)
           print(f"Code block {i} executed successfully!\n")
    except Exception as e:
        print(f"An error occurred: {e}")

# Usage
#extract_and_execute_code('Summary.txt', "a6133afa-9b82-11ef-9769-70665514def7")
