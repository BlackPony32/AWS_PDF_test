from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from dotenv import load_dotenv
import pandas as pd
load_dotenv()

def final_agent_gen(file_path, ai_task):
    if ai_task == 'positive_negative_trends':
        prompt = """Analyze my dataset according to the following guidelines:

"Data Analysis" Section (4 Points)

Provide a detailed and comprehensive analysis of the dataset. Focus on identifying key insights, such as:
The most valuable customer, the most profitable store or staff member, etc.
Variations in product sales across different time periods (if time-related data is available).
Significant trends or patterns in customer behavior, sales performance, or other relevant metrics.
Pay particular attention to data on time periods, customers, and sales if they are part of the dataset.
The analysis should be as thorough and detailed as possible, fully exploring the data.
"Achievements and Suggestions for Growth" Section (3 Points)

Based on the insights from the analysis, provide actionable advice on improving business performance.
Highlight successful areas or achievements, such as top-performing products, stores, or strategies.
Present your suggestions in a paragraph format with bullet points ("-"), not numbered lists.
Negative Aspects (2 Points)

Identify and discuss areas where the data shows room for improvement, such as:
Products with low sales performance.
Underperforming stores or staff.
Other inefficiencies or challenges revealed by the data.
Output Format: The response should be in plain text format, with clearly structured sections and no numbering in the "Achievements and Suggestions for Growth" section."""
    
    elif ai_task == 'negative_trends':
        prompt = """Analyze my dataset according to the following guidelines:
the two sections must have identical names, namely:
"Data Analysis" Section (4 Points)

Provide a detailed and comprehensive analysis of the dataset. Focus on identifying key insights, such as:
The most valuable customer, the most profitable store or staff member, etc.
Variations in product sales across different time periods (if time-related data is available).
Significant trends or patterns in customer behavior, sales performance, or other relevant metrics.
Pay particular attention to data on time periods, customers, and sales if they are part of the dataset.
The analysis should be as thorough and detailed as possible, fully exploring the data.
"Achievements and Suggestions for Growth" Section

Based on the insights from the analysis, provide actionable advice on improving business performance.
Highlight Negative Aspects (4-5 Points)
Present your suggestions in a paragraph format with bullet points ("-"), not numbered lists.

Identify and discuss areas where the data shows room for improvement, such as:
Products with low sales performance.
Underperforming stores or staff.
Other inefficiencies or challenges revealed by the data.
Output Format: The response should be in plain text format, with clearly structured sections and no numbering in the "Achievements and Suggestions for Growth" section."""
    
    else:
        prompt = """Analyze my dataset according to the following guidelines:

"Data Analysis" Section (4 Points)

Provide a detailed and comprehensive analysis of the dataset. Focus on identifying key insights, such as:
The most valuable customer, the most profitable store or staff member, etc.
Variations in product sales across different time periods (if time-related data is available).
Significant trends or patterns in customer behavior, sales performance, or other relevant metrics.
Pay particular attention to data on time periods, customers, and sales if they are part of the dataset.
The analysis should be as thorough and detailed as possible, fully exploring the data.
"Achievements and Suggestions for Growth" Section (5 Points)

Based on the insights from the analysis, provide actionable advice on improving business performance.
Highlight successful areas or achievements, such as top-performing products, stores, or strategies.
Present your suggestions in a paragraph format with bullet points ("-"), not numbered lists.

Output Format: The response should be in plain text format, with clearly structured sections and no numbering in the "Achievements and Suggestions for Growth" section."""
    
    
    
    
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

def final_gen(file_path, final_sum_folder, q4):
    agent_answer = final_agent_gen(file_path, q4) 
    final_answer = agent_answer.get("output")
    #print(final_answer)
    #print(final_sum_folder)
    with open(final_sum_folder, 'x') as file:
        file.write(final_answer)