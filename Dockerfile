# Copyright 2020 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

FROM python:3

ENV PYTHONUNBUFFERED 1
ENV RESERVOIR_STATIC_ROOT "/var/www/reservoir"
ENV PROJECT_NAME "reservoir"
ENV APPLICATION_NAME "reservoir"

RUN apt-get update
RUN apt-get upgrade -y
RUN apt-get install -y \
        postgresql \
        postgresql-contrib \
        apache2 \
        apache2-dev \
        python3-dev 

RUN mkdir -p "/${PROJECT_NAME}"
COPY . "/${PROJECT_NAME}"
WORKDIR "/${PROJECT_NAME}"
ADD . "/${PROJECT_NAME}"

RUN pip3 install -r "/${PROJECT_NAME}/requirements.txt" -r "/${PROJECT_NAME}/third_party/3dmr/requirements.txt"


# Set up the hosted static files.
RUN echo "${RESERVOIR_STATIC_ROOT}"
RUN mkdir -p "${RESERVOIR_STATIC_ROOT}"

# This will use the env RESERVOIR_STATIC_ROOT var to place static files in /var/www/reservoir
RUN python3 manage.py collectstatic

RUN chown -R :www-data "${RESERVOIR_STATIC_ROOT}"
RUN chmod -R 0776 "${RESERVOIR_STATIC_ROOT}"
# Directory inherits rights of group owner of directory.
RUN chmod g+s "${RESERVOIR_STATIC_ROOT}"

RUN chown -R :www-data "/${PROJECT_NAME}/${APPLICATION_NAME}"
RUN chmod -R 0776 "/${PROJECT_NAME}/${APPLICATION_NAME}"
RUN chmod a+x "/${PROJECT_NAME}/${APPLICATION_NAME}/wsgi.py"

# Copy the apache2 config to sites-available
COPY ./reservoir.apache2.conf /etc/apache2/sites-available/000-default.conf
