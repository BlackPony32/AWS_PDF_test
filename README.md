
# One-Click AI-Powered Data Reporting API

## Overview

This is a  **FastAPI** -based API developed by **SimplyDepo** that automates data analysis and reporting. Upload Excel or CSV files (and PDFs in the future), and generate comprehensive data reports with AI-powered insights, visualizations, and plots — all in one click.

## Features

* **Seamless File Uploads** : Supports Excel and CSV uploads.
* **AI-Powered Analysis** : Automatically generates data summaries and insights.
* **Interactive Visualizations** : Produces plots and graphs for enhanced understanding.
* **PDF Reports (Coming Soon)** : Export your reports as shareable PDFs.
* **Fast & Scalable** : Built with FastAPI for speed and reliability.

## Documentation

Comprehensive documentation is available [here](https://vk0.gitbook.io/pdf-from-data-file-docs).

## Tech Stack

* **Backend** : FastAPI
* **Visualization** : Plotly / Matplotlib
* **AI Insights** : Powered by OpenAI
* **File Handling** : Pandas and Asyncio for large file support

## Getting Started

### Prerequisites

* Python 3.8 or later
* Virtual environment (optional, but recommended)

### Installation

1. Clone this repository:
   git clone https://github.com/BlackPony32/AWS_PDF_test.git
   cd https://github.com/BlackPony32/AWS_PDF_test.git
2. Create and activate a virtual environment:
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
3. Install dependencies:
   pip install -r requirements.txt

### Run the API

1. Start the FastAPI server
   uvicorn main:app --reload
2. Access the API documentation:
   * Swagger UI: [http://127.0.0.1:8000/docs]()
   * ReDoc: [http://127.0.0.1:8000/redoc]()

## API Endpoints

### Upload File

* **POST** `/upload`
  Upload an Excel or CSV file for analysis.

### Generate Report

* **GET** `/report`
  Generates an AI-powered data report with visualizations.

### Download Report (Coming Soon)

* **GET** `/download/{filename}`
  Download the generated report as a PDF.

## Future Enhancements

* Add support for PDF data extraction.
* Enable customizable report templates.
* Include advanced AI-driven predictive analytics.

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
