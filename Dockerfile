FROM python:3.11
COPY requirements.txt /
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r /requirements.txt
COPY . /app
WORKDIR /app/src
EXPOSE 8000
CMD ["gunicorn", "--worker-tmp-dir", "/dev/shm", "--timeout", "120", "app:server"]
