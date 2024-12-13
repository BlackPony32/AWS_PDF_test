import shutil
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
from FastApi.additional_functions.preprocess_data import preprocess_data
from FastApi.additional_functions.preprocced_func import check_map_columns
from FastApi.AI_instruments.one_agent_main import AI_generation_plots_summary
from FastApi.AI_instruments.final_sum import final_gen
from pathlib import Path
from FastApi.additional_functions.dataset_main_info import extract_main_info
from concurrent.futures import ThreadPoolExecutor

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
    loop = asyncio.get_event_loop()

    if os.path.exists(plots_folder):
        await loop.run_in_executor(executor, shutil.rmtree, plots_folder)
    if os.path.exists(summary_folder):
        await loop.run_in_executor(executor, shutil.rmtree, summary_folder)
    if os.path.exists(pdf_folder):
        await loop.run_in_executor(executor, shutil.rmtree, pdf_folder)
    if os.path.exists(uploads_folder):
        await loop.run_in_executor(executor, shutil.rmtree, uploads_folder)
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

        cleaned_dataset_name = f"FastApi/src/uploads/{user_folder}/cleaned_data.csv"
        _df = await asyncio.to_thread(pd.read_csv, cleaned_dataset_name, low_memory=False)
        data_dict = await asyncio.to_thread(extract_main_info, _df)

        try:
            result = await asyncio.to_thread(check_map_columns, user_folder)
            if result:
                page_numb = 4
        except Exception as e:
            logger.error(f"Preprocced plot generation error: {e}")

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
