FROM ubuntu:18.04

MAINTAINER Zach Di Giovanni "zdigiovanni@my.bcit.ca"

RUN apt-get update -y && apt-get install -y python3-dev python3-pip

COPY ./requirements /app/requirements.txt

WORKDIR /app

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python3" ]

CMD [ "app.py" ]