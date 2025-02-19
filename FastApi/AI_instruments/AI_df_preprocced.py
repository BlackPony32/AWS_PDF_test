from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from dotenv import load_dotenv
import pandas as pd
import re
import tiktoken
import os
import logging
log_file_path = "preprocess_log.log"
logger = logging.getLogger(__name__)
# Load environment variables
load_dotenv()

# Pricing rates (per 1,000 tokens)
INPUT_COST_PER_1K_TOKENS = 0.0025  # for 1000 GPT-4о input
OUTPUT_COST_PER_1K_TOKENS = 0.01  # for 1000 GPT-4о output

# Helper function to count tokens
def count_tokens(text: str, model: str = "gpt-4o") -> int:
    """Count the number of tokens in a text using tiktoken."""
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

# Helper function to calculate cost
def calculate_cost(input_tokens: int, output_tokens: int) -> float:
    """Calculate the cost of the request and response in dollars."""
    input_cost = (input_tokens / 1000) * INPUT_COST_PER_1K_TOKENS
    output_cost = (output_tokens / 1000) * OUTPUT_COST_PER_1K_TOKENS
    total_cost = input_cost + output_cost
    return total_cost

def find_col_to_drop(file_path):
    prompt = """
    Analyze this report
    Write columns that would be great to drop.
    It should follow some rules:
    1) Data in the column should be useless for data visualization.
    2) Keep in mind that the choice should be deliberate (if the columns data are similar in meaning, leave the more understandable for the business).
    3) All this is done to create the most valuable visualizations.
    4) The final answer should contain a list of columns.
    5) Do NOT drop State or Zip if they exist.
    Example output:
    ```python
    ['REP_NUM', 'CUSTOMER', 'ADDRESS']
    ```
    """
    
    # Try different encodings to read the CSV file
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding)
            break
        except UnicodeDecodeError:
            print(f"Failed decode with: {encoding}")
    
    try:
        # Initialize the LLM
        llm = ChatOpenAI(model="gpt-4o", temperature=0)
        
        # Create the agent
        agent_executor = create_pandas_dataframe_agent(
            llm,
            df,
            agent_type="tool-calling",
            verbose=True,
            allow_dangerous_code=True
        )

        input_tokens = count_tokens(prompt)

        result = agent_executor.invoke({"input": prompt})

        output = result.get("output", "")
        output_tokens = count_tokens(output)
        total_cost = calculate_cost(input_tokens, output_tokens)
        
        # Print the cost
        logger.info(f"Input tokens AI df: {input_tokens}")
        logger.info(f"Output tokens AI df: {output_tokens}")
        logger.info(f"Total cost AI df: ${total_cost:.4f}")
        #print(f"Input tokens: {input_tokens}")
        #print(f"Output tokens: {output_tokens}")
        #print(f"Total cost: ${total_cost:.4f}")
        
        return {"output": output, "cost": total_cost}
    
    except Exception as e:
        logger.error(f"Error executing LLM: {e}")
        return {"output": "Can not answer on it", "cost": 0.0}

def file_columns_to_drop(file_path: str, path_for_drop_col_list: str):
    try:
        # Get the agent's answer
        agent_answer = find_col_to_drop(file_path)
        final_answer = agent_answer.get("output")
        cost = agent_answer.get("cost", 0.0)
        
        # Write the final answer to a file
        with open(path_for_drop_col_list, 'w') as file:
            file.write(final_answer)
        
        logger.info(f"Columns to drop saved to {path_for_drop_col_list}")
        logger.info(f"Total cost of the operation: ${cost:.4f}")
    
    except Exception as e:
        logger.error(f"Error in file_columns_to_drop: {e}")