FROM python:3.9 
WORKDIR /app

COPY App.py .
COPY Licitacion.py .
COPY Utils.py .

COPY requirements.txt .

RUN pip install -r requirements.txt
CMD ["python", "App.py", "--config", "config.ini"]
