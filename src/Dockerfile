FROM python:3.9 
WORKDIR /app

RUN apt-get update && apt-get -y install cron nano bash

COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY crontab /etc/crontab
RUN chmod 0644 /etc/crontab

RUN /usr/bin/crontab -u root /etc/crontab

COPY App.py .
COPY Licitacion.py .
COPY Utils.py .

CMD ["cron", "-f"]