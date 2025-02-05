import shutil
import re
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi import  Query
from typing import Optional
from fastapi.responses import FileResponse
from pydantic import BaseModel
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
from fastapi.responses import PlainTextResponse
import pandas as pd
import os
import logging
import asyncio
import aiofiles
#from FastApi.additional_functions.pdf_maker import generate_pdf
from FastApi.additional_functions.pdf_maker import PDFReport
from FastApi.additional_functions.cleand_df import AI_drop_col_csv
from FastApi.additional_functions.preprocess_data import preprocess_data
from FastApi.additional_functions.preprocced_func import check_map_columns
from FastApi.AI_instruments.one_agent_main import AI_generation_plots_summary
from FastApi.AI_instruments.final_sum import final_gen
from pathlib import Path
from FastApi.additional_functions.dataset_main_info import extract_main_info
from concurrent.futures import ThreadPoolExecutor

from langchain_openai import ChatOpenAI
from langchain_experimental.agents import create_pandas_dataframe_agent

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5000",  # Local frontend during development
    "http://127.0.0.1:5000",  # Alternative local URL
    "https://simplydepostag.wpengine.com/",  # Deployed frontend
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging to write to a file
# Pricing rates (per 1,000 tokens)
INPUT_COST_PER_1K_TOKENS = 0.0025  # for 1000 GPT-4о input
OUTPUT_COST_PER_1K_TOKENS = 0.01  # for 1000 GPT-4о output
log_file_path = "preprocess_log.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor()

def user_uuid():
    import uuid
    user_folder = str(uuid.uuid4())
    return user_folder

async def convert_excel_to_csv(excel_file_path): 
    try:
        loop = asyncio.get_event_loop()
        # Load Excel file asynchronously
        df = await loop.run_in_executor(executor, pd.read_excel, excel_file_path)
        csv_file_path = os.path.splitext(excel_file_path)[0] + ".csv"
        # Save DataFrame as CSV
        await loop.run_in_executor(executor, lambda: df.to_csv(csv_file_path, index=False))
        os.remove(excel_file_path)
        return csv_file_path
    except Exception as e:
        raise ValueError(f"Error converting Excel to CSV: {str(e)}")

async def clean_directories(user_id):

    plots_folder = f'FastApi/src/plots/{user_id}'
    summary_folder = f'FastApi/src/summary/{user_id}'
    pdf_folder = f'FastApi/src/pdfs/{user_id}'
    uploads_folder = f'FastApi/src/uploads/{user_id}'
    chat_folder = f'FastApi/src/files/{user_id}'
    loop = asyncio.get_event_loop()

    if os.path.exists(plots_folder):
        await loop.run_in_executor(executor, shutil.rmtree, plots_folder)
    if os.path.exists(summary_folder):
        await loop.run_in_executor(executor, shutil.rmtree, summary_folder)
    if os.path.exists(pdf_folder):
        await loop.run_in_executor(executor, shutil.rmtree, pdf_folder)
    if os.path.exists(uploads_folder):
        await loop.run_in_executor(executor, shutil.rmtree, uploads_folder)
    if os.path.exists(chat_folder):
        await loop.run_in_executor(executor, shutil.rmtree, chat_folder)
    logger.info(f"Deleted user folder: {user_id}")

# Define a BaseModel for the JSON payload
class FormData(BaseModel):
    q1: str
    q2: str
    q3: str
    q4: str

@app.post("/src/upload")
async def upload_file(
    file: UploadFile = File(...),
    q1: Optional[str] = Query(...),
    q2: Optional[str] = Query(...),
    q3: Optional[str] = Query(...),
    q4: Optional[str] = Query(...)
):
    user_folder = user_uuid()
    #test
    data_dict = {"q1": q1, "q2": q2, "q3": q3, "q4": q4}
    q4 = data_dict.get('q4')
    logger.info(f"got : {data_dict}")
    UPLOAD_FOLDER = f'FastApi/src/uploads/{user_folder}'
    PDF_FOLDER = f'FastApi/src/pdfs/{user_folder}'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PDF_FOLDER, exist_ok=True)

    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        logger.error("Invalid file format uploaded.")
        raise HTTPException(status_code=400, detail="Invalid file format. Only CSV, XLSX, and XLS are allowed.")

    real_name = file.filename
    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)
        logger.info(f"Uploaded file {file.filename} to {UPLOAD_FOLDER}")

    if file.filename.endswith(('.xlsx', '.xls')):
        try:
            file_path = await convert_excel_to_csv(file_path)
            logger.info(f"Converted Excel to CSV and loaded file: {file.filename}")
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while processing the file.")

    try:
        path = Path(file_path)
        filename = path.name
        page_numb = 5
        action = await asyncio.to_thread(preprocess_data, path, user_folder)
        logger.info(f"Data preprocessing for file: {filename} finished")

        cleaned_dataset_name = f"FastApi/src/uploads/{user_folder}/cleaned_data.csv" #NOTE changed name if needed
        
        try:
            file_path_for_ai_cleaning = f"FastApi/src/uploads/{user_folder}/cleaned_data.csv"
            path_for_drop_col_list = f"FastApi/src/uploads/{user_folder}/drop_col_list.txt"
            df_path = f"FastApi/src/uploads/{user_folder}"
            
            create_ai_cleaned_df = await asyncio.to_thread(AI_drop_col_csv, file_path_for_ai_cleaning, df_path, path_for_drop_col_list)
        except Exception as e:
            logger.error(f"AI data cleaning error: {e}")
        
        try:
            _df = await asyncio.to_thread(pd.read_csv, create_ai_cleaned_df, low_memory=False)
        except Exception as e:
            logger.error(f"AI data using error: {e}")
            _df = await asyncio.to_thread(pd.read_csv, cleaned_dataset_name, low_memory=False)
        
        data_dict = await asyncio.to_thread(extract_main_info, _df)

        try:
            result = await asyncio.to_thread(check_map_columns, user_folder)
            if result:
                page_numb = 4
        except Exception as e:
            logger.error(f"Preprocessed plot generation error: {e}")

        try:
            await asyncio.to_thread(AI_generation_plots_summary, data_dict, user_folder, page_numb)
            logger.info("Plot generation completed")
        except Exception as e:
            logger.error(f"Plot generation error: {e}")
        
        try:
            final_sum_folder = f"FastApi/src/uploads/{user_folder}/final_gen.txt"
            await asyncio.to_thread(final_gen, f"FastApi/src/uploads/{user_folder}/{filename}", final_sum_folder, q4)
            logger.info("Data final summary generated")
        except Exception as e:
            logger.error(f"Data final summary generation error: {e}")
        
        try:
            pdf = PDFReport(pdf_file_name=real_name, user_folder=user_folder)
            pdf_path = await asyncio.to_thread(pdf.create_pdf) 
            logger.info(f"Generated PDF at {pdf_path}")
        except Exception as e:
            logger.error(f"Generated PDF error: {e}")
        
        pdf_url = f"/download/{user_folder}/{os.path.basename(pdf_path)}"

        # Optionally clean directories
        # await clean_directories()
        download_pdf_url = f"FastApi/src/pdfs/{user_folder}/{os.path.basename(pdf_path)}"
        pdf_filename = os.path.basename(download_pdf_url)
        return JSONResponse(content={"message": "File processed successfully", "action": action, "download_pdf_url": pdf_url,
                                     "pdf_url" : download_pdf_url, "user_folder": user_folder,
                                     "pdf_filename": pdf_filename})

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while processing the file.")

@app.get("/download/")
async def download_pdf(pdf_url: str, user_folder: str, background_tasks: BackgroundTasks):
    file_path = os.path.join(pdf_url)

    if not os.path.exists(file_path):
        logger.error(f"File not found: {pdf_url}")
        raise HTTPException(status_code=404, detail="File not found.")
    
    filename = os.path.basename(file_path)
    logger.info(f"Downloading PDF: {filename}")
    
    # Schedule the cleanup task to run after the response is sent
    background_tasks.add_task(clean_directories, user_folder)

    return FileResponse(file_path, media_type='application/pdf', filename=filename)

@app.get("/logs/last/{num_lines}", response_class=PlainTextResponse)
async def get_last_n_log_lines(num_lines: int):
    try:
        # Open and read the log file
        LOG_FILE = "preprocess_log.log"
        with open(LOG_FILE, "r") as file:
            lines = file.readlines()

        if not lines:
            raise HTTPException(status_code=404, detail="Log file is empty.")

        # Get the last `num_lines` lines
        last_lines = lines[-num_lines:]
        return "".join(last_lines)

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Log file not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")


#______________AI chat block start______
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


import tiktoken

# AI chat block
async def chat_with_file(prompt: str, file_path: str):
    # Try different encodings to read the CSV file
    encodings = ['utf-8', 'latin1', 'iso-8859-1', 'cp1252']
    for encoding in encodings:
        try:
            df = pd.read_csv(file_path, encoding=encoding, low_memory=False)
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
        print(f"Input tokens: {input_tokens}")
        print(f"Output tokens: {output_tokens}")
        print(f"Total cost: ${total_cost:.4f}")
        
        return {"output": output, "cost": total_cost}
    
    except Exception as e:
        print("error executing llm:", e)
        return {"output": "Can not answer on it", "cost": 0.0}

# Pydantic models for request validation
class ChatRequest(BaseModel):
    prompt: str

# Endpoint to start chat with AI
@app.post('/chat_with_ai_start')
async def chat_with_ai_start(file: UploadFile = File(...)):
    # Data file transfer and processing
    _user_uuid = user_uuid()
    FILES_FOLDER = f'FastApi/src/files/{_user_uuid}'
    os.makedirs(FILES_FOLDER, exist_ok=True)

    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        logger.error("Invalid file format uploaded.")
        raise HTTPException(status_code=400, detail="Invalid file format. Only CSV, XLSX, and XLS are allowed.")

    real_name = file.filename
    file_path = os.path.join(FILES_FOLDER, file.filename)
    async with aiofiles.open(file_path, "wb") as buffer:
        content = await file.read()
        await buffer.write(content)
        logger.info(f"Uploaded file {file.filename} for chat to {FILES_FOLDER}")

    if file.filename.endswith(('.xlsx', '.xls')):
        try:
            file_path = await convert_excel_to_csv(file_path)
            logger.info(f"Converted Excel to CSV and loaded file: {file.filename}")
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise HTTPException(status_code=500, detail="An error occurred while processing the file.")
    
    # Create a recommendation supporting questions
    prompt = """
        Thoroughly analyze the file you receive, and you need to identify the most useful recommendations for your business.
        The result of the answer should be 4 questions that the user needs to ask the file.
        - Do not answer them.
        - The answer should be structured - only questions in the format of a Python dictionary. 
        Example output:
        ```python
        {
            "question_1": "What are the sales trends by channel and fulfillment?",
            "question_2": "Which products or categories have high cancellations?",
            "question_3": "How do shipping levels affect order status?",
            "question_4": "Which regions drive revenue and demand?",
        }```
    """
    
    response = await chat_with_file(prompt, file_path)
    answer = response.get('output')
    
    # Save the answer to a file
    first_answer_file = f'FastApi/src/files/{_user_uuid}/answer.txt'
    with open(first_answer_file, 'w') as file:
        file.write(answer)
    
    # Extract questions from the answer
    try:
        with open(first_answer_file, 'r') as file:
            content = file.read()
        code_blocks = re.findall(r'```python(.*?)```', content, re.DOTALL)  # TODO: Add exception handling

        if code_blocks:
            answer_dict = eval(code_blocks[0].strip())  # Use `eval` only if the source is trusted
        else:
            answer_dict = {}
    except Exception as e:
        print("Error is", e)
        answer_dict = {}
    
    # Extract questions from the dictionary
    question_1 = answer_dict.get('question_1', "No question generated")
    question_2 = answer_dict.get('question_2', "No question generated")
    question_3 = answer_dict.get('question_3', "No question generated")
    question_4 = answer_dict.get('question_4', "No question generated")
    
    return JSONResponse(content={
        "message": "File processed successfully",
        "user_uuid": _user_uuid,
        "file_path": file_path,
        "question_1": question_1,
        "question_2": question_2,
        "question_3": question_3,
        "question_4": question_4
    })

# Endpoint to ask AI
@app.post("/Ask_ai")
async def ask_ai(request: ChatRequest, file_path: str):
    prompt = request.prompt
    system_prompt = f"""
    Answer on my business question according to these rules:
    - Answer should be well structured in text format,
    - Do not use date visualization or write Python code in your answers,
    - Keep your answers concise and well formatted,
    The question is: {prompt}
    """
    
    try:
        response = await chat_with_file(system_prompt, file_path)
        answer = response.get('output')
        cost = response.get('cost', 0.0)
    except Exception as e:
        print("error executing llm:", e)
        answer = "Can not answer on it"
        cost = 0.0
    
    return {"response": answer, "prompt": prompt, "cost": cost}

@app.get("/clean_chat/")
async def download_pdf(user_folder: str, background_tasks: BackgroundTasks):
    
    # Schedule the cleanup task to run after the response is sent
    background_tasks.add_task(clean_directories, user_folder)

    return {"response": "Chat is cleaned successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
