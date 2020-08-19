#!/bin/bash
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


until psql $DATABASE_URL -c '\l'; do
    >&2 echo "Posgres is unavailable - sleeping."
    sleep 10s
done

mkdir -p /dreservoir/models
echo "model dir: ${RESERVOIR_MODEL_DIR}"
echo "RESERVOIR_PORT: ${RESERVOIR_PORT}"
echo "RESERVOIR_DC_HOST_PORT: ${RESERVOIR_DC_HOST_PORT}"
echo "RESERVOIR_STATIC_URL: ${RESERVOIR_STATIC_URL}"

python3 /dreservoir/manage.py makemigrations
python3 /dreservoir/manage.py makemigrations mainapp
python3 /dreservoir/manage.py migrate
python3 /dreservoir/manage.py runmodwsgi --port="${RESERVOIR_PORT}" --user=www-data --group=www-data \
        --server-root=/etc/mod_wsgi-express-8080 --error-log-format "%M" --log-to-terminal \
        --reload-on-changes
# python3 manage.py runserver 8080

exec "$@"
