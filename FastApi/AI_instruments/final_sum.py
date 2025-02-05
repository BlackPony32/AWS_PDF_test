from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent
from dotenv import load_dotenv
import pandas as pd
import tiktoken
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

def final_agent_gen(file_path: str, ai_task: str):
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
    
    # Try different encodings to read the CSV file
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
            break
        except UnicodeDecodeError as e:
            logger.error(f"Failed decode with: {e}")
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
        
        # Count input tokens
        input_tokens = count_tokens(prompt)
        
        # Invoke the agent
        result = agent_executor.invoke({"input": prompt})
        
        # Extract the output
        output = result.get("output", "")
        
        # Count output tokens
        output_tokens = count_tokens(output)
        
        # Calculate the cost
        total_cost = calculate_cost(input_tokens, output_tokens)
        
        # Print the cost
        logger.info(f"Input tokens final some: {input_tokens}")
        logger.info(f"Output tokens final some: {output_tokens}")
        logger.info(f"Total cost final some: ${total_cost:.4f}")
        #print(f"Input tokens: {input_tokens}")
        #print(f"Output tokens: {output_tokens}")
        #print(f"Total cost: ${total_cost:.4f}")
        
        return {"output": output, "cost": total_cost}
    
    except Exception as e:
        logger.error(f"Error executing LLM: {e}")
        return {"output": "Can not answer on it", "cost": 0.0}

def final_gen(file_path: str, final_sum_folder: str, q4: str):
    try:
        # Get the agent's answer
        agent_answer = final_agent_gen(file_path, q4)
        final_answer = agent_answer.get("output")
        cost = agent_answer.get("cost", 0.0)
        
        # Write the final answer to a file
        with open(final_sum_folder, 'w') as file:
            file.write(final_answer)
        
        #logger.info(f"Total cost final some: ${total_cost:.4f}")
        logger.info(f"Final answer saved to {final_sum_folder}")
        logger.info(f"Total cost of the operation: ${cost:.4f}")
    
    except Exception as e:
        logger.error(f"Error in final_gen: {e}")