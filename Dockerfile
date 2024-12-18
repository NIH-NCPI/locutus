
FROM python:3.11-alpine

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
RUN apk update && \
    apk add --no-cache git && \
    pip install --no-cache-dir -r requirements.txt && \
    apk del git

# Cloud Run expects 8080, need to figure out how to change that
EXPOSE 8080 
CMD ["flask", "run"] 
