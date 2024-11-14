from flask import Flask, render_template, request, jsonify, send_file, session
import requests
from io import BytesIO

app = Flask(__name__)
app.secret_key = "your_secret_key"  # Set a secret key for session management
fastapi_url = "http://0.0.0.0:8000"  # FastAPI server URL

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files['file']
    if file and (file.filename.endswith('.csv') or file.filename.endswith(('.xlsx', '.xls'))):
        response = requests.post(
            f"{fastapi_url}/src/upload",
            files={'file': (file.filename, file, file.content_type)}
        )
        if response.status_code == 200:
            json_data = response.json()
            pdf_url = json_data.get("download_pdf_url")
            user_folder = json_data.get("user_folder")
            pdf_filename = json_data.get("pdf_filename")  # Extract the file name

            # Store pdf_url in session
            session['user_folder'] = user_folder
            session['pdf_url'] = pdf_url
            session['pdf_filename'] = pdf_filename
            return jsonify({"message": "File processed successfully!", "pdf_url": pdf_url, "pdf_filename": pdf_filename})
        else:
            error_detail = response.json().get("detail", "Unknown error")
            return jsonify({"message": "File upload failed.", "error": error_detail}), response.status_code
    return jsonify({"message": "Invalid file format. Only CSV and Excel files are allowed."}), 400

@app.route('/download', methods=['GET'])
def download_pdf():
    user_folder = session.get('user_folder')
    pdf_url = session.get('pdf_url')  # Retrieve pdf_url from session
    pdf_filename = session.get('pdf_filename')
    #print(pdf_url[0])
    if pdf_url:
        response = requests.get(f"{fastapi_url}/download/", params={"pdf_url": pdf_url, "user_folder": user_folder})
        
        if response.status_code == 200:
            return send_file(BytesIO(response.content), 
                             download_name=pdf_filename, 
                             mimetype='application/pdf', 
                             as_attachment=True)
    
    return "Failed to download PDF", 404

if __name__ == '__main__':
    app.run(port=5000)
