
FROM python:3.11-alpine

# Install system dependencies
RUN apt-get update && apt-get install -y git

#WORKDIR .
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0
#ENV PORT=8080
COPY src  ./src
COPY pyproject.toml . 
COPY README.md .
RUN pip install . 

# Install github packages that do not conform to the toml file 
COPY requirements.txt .
# install git to enable installing the github package in the requirements
# file then uninstall it as it is no longer necessary 
RUN apt-get update && apt-get install -y git && \
    pip install --no-cache-dir -r requirements.txt && \
    apt-get remove -y git && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*


# Cloud Run expects 8080, need to figure out how to change that
EXPOSE 8080 
CMD ["flask", "run"] 
