FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app_ec2_ecs.py .

EXPOSE 80

CMD ["python3", "app_ec2_ecs.py"]
