FROM python:3.6
RUN mkdir -p /var/wikiclient /usr/local/etc/wikiclient/
COPY ./ /var/wikiclient
RUN pip3 install --upgrade pip && pip3 install /var/wikiclient
WORKDIR /var/wikiclient