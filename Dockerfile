# Dockerfile
FROM ubuntu:14.04

RUN apt-get update
RUN apt-get install -yq software-properties-common python-software-properties
RUN add-apt-repository ppa:jonathonf/python-3.6
RUN add-apt-repository ppa:no1wantdthisname/ppa

RUN apt-get update
RUN apt-get install -yq \
	python3.6 \
	python-setuptools \
	python-dev \
	build-essential \
	git \
	python3-pip \
	libpng-dev \
	libfreetype6-dev \
	libfreetype6 \
	pkg-config \
	python3-tk

COPY requirements.txt /project/requirements.txt
WORKDIR /project
RUN pip3 install -r requirements.txt

COPY . /project

EXPOSE 8000

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]

# docker build -t toniukan/group_project_vk .
# docker run -p 80:8000 -it --rm toniukan/group_project_vk