FROM python:3.9 
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY App.py .
COPY Licitacion.py .
COPY Utils.py .

CMD ["python", "App.py", "--config", "/config/config.ini"]
