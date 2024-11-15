import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from starlette.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import BackgroundTasks
import pandas as pd
import os
import logging
import asyncio
import aiofiles
#from FastApi.additional_functions.pdf_maker import generate_pdf
from FastApi.additional_functions.pdf_maker import PDF
from FastApi.additional_functions.preprocess_data import preprocess_data
from FastApi.AI_instruments.one_agent_main import AI_generation_plots_summary
from FastApi.AI_instruments.final_sum import final_gen
from pathlib import Path
from FastApi.additional_functions.dataset_main_info import extract_main_info
from concurrent.futures import ThreadPoolExecutor

app = FastAPI()

# Configure CORS
origins = [
    "http://localhost:5000",
    "http://127.0.0.1:5000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
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
    user_folder = str(uuid.uuid1())
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
    loop = asyncio.get_event_loop()

    if os.path.exists(plots_folder):
        await loop.run_in_executor(executor, shutil.rmtree, plots_folder)
    if os.path.exists(summary_folder):
        await loop.run_in_executor(executor, shutil.rmtree, summary_folder)
    if os.path.exists(pdf_folder):
        await loop.run_in_executor(executor, shutil.rmtree, pdf_folder)
    logger.info(f"Deleted user folder: {user_id}")

@app.post("/src/upload")
async def upload_file(file: UploadFile = File(...)):
    user_folder = user_uuid()
    UPLOAD_FOLDER = f'FastApi/src/uploads/{user_folder}'
    PDF_FOLDER = f'FastApi/src/pdfs/{user_folder}'
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(PDF_FOLDER, exist_ok=True)

    if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
        logger.error("Invalid file format uploaded.")
        raise HTTPException(status_code=400, detail="Invalid file format. Only CSV, XLSX, and XLS are allowed.")

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
        action = await asyncio.to_thread(preprocess_data, path, user_folder)
        logger.info(f"Data preprocessing for file: {filename} finished")

        cleaned_dataset_name = f"FastApi/src/uploads/{user_folder}/cleaned_data.csv"
        _df = await asyncio.to_thread(pd.read_csv, cleaned_dataset_name, low_memory=False)
        data_dict = await asyncio.to_thread(extract_main_info, _df)

        try:
            await asyncio.to_thread(AI_generation_plots_summary, data_dict, user_folder)
            logger.info("Plot generation completed")
        except Exception as e:
            logger.error(f"Plot generation error: {e}")
        
        try:
            await asyncio.to_thread(final_gen, f"FastApi/src/uploads/{user_folder}/{filename}")
            logger.info("Data summary generated")
        except Exception as e:
            logger.error(f"Data summary generation error: {e}")
        
        pdf = PDF(formated_file_name=filename, user_folder=user_folder)
        pdf_path = await asyncio.to_thread(pdf.create_pdf) 
        logger.info(f"Generated PDF at {pdf_path}")

        pdf_url = f"/download/{user_folder}/{os.path.basename(pdf_path)}"

        # Optionally clean directories
        # await clean_directories()
        download_pdf_url = f"FastApi/src/pdfs/{user_folder}/{os.path.basename(pdf_path)}"
        pdf_filename = os.path.basename(download_pdf_url)
        return JSONResponse(content={"message": "File processed successfully", "action": action, "pdf_url": pdf_url,
                                     "download_pdf_url" : download_pdf_url, "user_folder": user_folder,
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
