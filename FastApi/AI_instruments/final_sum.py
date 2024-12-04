from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

def final_agent_gen(file_path):
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
        verbose=False,
        allow_dangerous_code=True
    )
    result = agent_executor.invoke(
        {
            "input": """Analyze my dataset according to the following rules:
- Block named "Data Analysis" - 4 points - should be a detailed answer on data analysis -For example, the most valuable customer, the most profitable store or staff, etc.. 
For example, the difference in product sales in different periods of time. The answer should be as detailed as possible.
pay attention to time periods if they are available, and to customers, sales if data is available.
- It should be a voluminous answer disclosing the data to the maximum!
-  Block named "Achievements and Suggestions for Growth" - (3 points) - based on the data obtained, there should be advice on how to improve the business
- + point out the negative aspects (3 points) of the data, such as products that are not selling well or stores that are not bringing in enough product, etc.
- answer should be only in txt format
- in block "Achievements and Suggestions for Growth" do not use numbering of paragraphs, only with a dash."""
        }
    )

    return result

def final_gen(file_path):
    agent_answer = final_agent_gen(file_path) 
    final_answer = agent_answer.get("output")

    with open('FastApi/src/final_gen.txt', 'w') as file:
        file.write(final_answer)