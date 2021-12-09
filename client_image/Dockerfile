FROM python:3.8-slim-buster
WORKDIR /files
COPY . .
COPY ../config.toml .
RUN pip install -r requirements.txt

CMD ["python","./client.py"]