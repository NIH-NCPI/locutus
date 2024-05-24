
FROM python:3.10-alpine
#WORKDIR .
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0
#ENV PORT=8080
COPY src  ./src
COPY pyproject.toml . 
COPY README.md .
RUN pip install . 

# Cloud Run expects 8080, need to figure out how to change that
EXPOSE 8080 
CMD ["flask", "run"] 
