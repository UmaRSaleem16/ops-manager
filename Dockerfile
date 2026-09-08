FROM python:3.8

LABEL maintainer="PABLO CISNEROS <pcisnerp@gmail.com>"

RUN apt-get update && \
    apt-get install -y libsasl2-dev libldap2-dev libssl-dev libsnmp-dev apt-utils iputils-ping && \
    rm -rf /var/lib/apt/lists/*

COPY ./ /
WORKDIR /

RUN pip install -r requirements.txt

EXPOSE 5000
CMD ["flask", "run", "--host=0.0.0.0"]
