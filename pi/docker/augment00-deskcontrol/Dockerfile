FROM paulharter/augment00-python:latest

RUN apt-get install -y python-imaging

RUN mkdir -p /opt/augment00

RUN cd /opt/augment00 && git clone https://github.com/blip2/deskcontrol.git

RUN pip install -r /opt/augment00/deskcontrol/requirments.txt

WORKDIR /opt/augment00

CMD ["python", "deskcontrol/controller.py"]







