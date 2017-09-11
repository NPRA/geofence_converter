FROM python:2.7

MAINTAINER Asbjørn Alexander Fellinghaug "asbjorn.fellinghaug@webstep.no"

RUN mkdir -p /code
WORKDIR /code

# This hack avoids rebuild / downloading / installing 
# all python dependecies for each docker build
COPY requirements.txt /code
ENV PIP_TIMEOUT=60
ENV PIP_DISABLE_PIP_VERSION_CHECK=true
RUN pip install --no-cache-dir -r requirements.txt

COPY *.py /code/

# Add python qpid
RUN mkdir -p /code/libs
COPY libs/qpid-python /code/libs/qpid-python

ENV PYTHONPATH /code/libs/qpid-python:$PYTHONPATH