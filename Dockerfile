
FROM python:3.10-alpine
WORKDIR /src
ENV FLASK_APP=src/app.py
ENV FLASK_RUN_HOST=0.0.0.0
COPY src  ./src
COPY db ./db
COPY pyproject.toml . 
COPY README.md .
RUN pip install . 
EXPOSE 8080 
CMD ["flask", "run", "-p", "8080"]
