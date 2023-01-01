# Use official Debian based Python 3.9-slim-buster image
FROM python:3.9-slim-buster

# Expose default Flask listening port 5000
EXPOSE 5000

# Set the working directory if it does not exist
WORKDIR /VulnerableWebsite

# Install requirements from requirements.txt
COPY requirements.txt /VulnerableWebsite
RUN pip install -r requirements.txt

COPY . .

# Run server.py when the container launches
CMD python server.py