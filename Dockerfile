FROM python:3.9

ADD . /harald
WORKDIR /harald

RUN pip install suncalc

CMD python automatisirung.py

