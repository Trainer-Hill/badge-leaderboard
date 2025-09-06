FROM python:3.11-slim
COPY requirements.txt /
RUN pip3 install --upgrade pip
RUN pip3 install --no-cache-dir -r /requirements.txt
COPY . /app
WORKDIR /app/src
EXPOSE 8000
ENV FLASK_ENV=production
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app:server", "-k", "gevent"]
