FROM python:3.8-slim-buster
WORKDIR /files
COPY . .
RUN pip install -r requirements.txt

CMD ["python","./client.py"]