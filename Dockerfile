FROM python:3.8

WORKDIR /opt
# Download get-pip.py
RUN wget https://bootstrap.pypa.io/get-pip.py
RUN python get-pip.py
RUN pip install --upgrade pip

# git clone을 도커에서 수행해야
RUN git clone https://github.com/ideyedi/awx-open-api.git ./application

WORKDIR /opt/application
RUN pip install --no-cache-dir -r requirements.txt
CMD ["uvicorn", "app.main:app", "--port=8080", "--host=0.0.0.0", "--reload"]
