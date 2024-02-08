FROM python:3.12

#COPY . /app

RUN apt-get update && \
    apt-get upgrade && \
	apt-get install -y screen && \
	pip install --upgrade pip && \
    pip install flask requests

WORKDIR /app
CMD ["python", "app.py"]
