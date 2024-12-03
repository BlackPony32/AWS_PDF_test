# Use an official Python runtime as a base image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file into the container
COPY /requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

ENV PATH="/usr/local/lib/python3.10/site-packages/kaleido/executable:$PATH"

# Copy the application code into the container
COPY . .

# Expose the port Flask will run on
EXPOSE 5000

# Command to run the Flask app
CMD ["python", "app.py"]  # Adjust this if your entry file is different
