FROM python:3.13.0a2-slim-bullseye
RUN apt-get update \
    && apt-get install -y --no-install-recommends --no-install-suggests \
    build-essential pkg-config default-libmysqlclient-dev \
    && pip install --no-cache-dir --upgrade pip

WORKDIR /app
COPY ./requirements.txt /app/
RUN pip install --no-cache-dir --requirement /app/requirements.txt
COPY . /app/
RUN mkdir -p -v /app/temp && mkdir /app/tempmaps

EXPOSE 8080

CMD [ "python3", "gateway.py" ]