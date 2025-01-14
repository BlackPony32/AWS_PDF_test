from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from dotenv import load_dotenv
import pandas as pd
import re
load_dotenv()

def find_col_to_drop(file_path):
    
    prompt = """
    Analyze this report
write column that whould be great to drop
it should follow some rules:
1) data in column and column name should be useless for data viz.
2) Keep in mind that the choice should be deliberate (if the columns are similar in meaning, leave the more understandable for the business)
3) all this is done to create the most valuable visualizations.
4) The final answer should contain a list of columns.
5) Do NOT drop State or ZIp if exists.
Example output:
```python
['REP_NUM', 'CUSTOMER', 'ADDRESS']
```
    """
    
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']  # список можливих енкодингів
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
        except UnicodeDecodeError:
            print(f"Failed decode with: {encoding}")
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    agent_executor = create_pandas_dataframe_agent(
        llm,
        df,
        agent_type="tool-calling",
        verbose=True,
        allow_dangerous_code=True
    )
    result = agent_executor.invoke(
        {
            "input": prompt
        }
    )

    return result

def file_columns_to_drop(file_path: str, path_for_drop_col_list):
    try:
        agent_answer = find_col_to_drop(file_path)
        final_answer = agent_answer.get("output")
    except Exception as e:
        print(f"Error in find_col_to_drop {e}")
    
    try:
        #print(final_answer)
        #print(final_sum_folder)
        #print(path_for_drop_col_list)
        with open(path_for_drop_col_list, 'w') as file:
            file.write(final_answer)
    except Exception as e:
        print(f"Error in writing path_for_drop_col_list: {e}")