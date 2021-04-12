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
#
# Routes to first version of reservoir API endpoints.

from django.urls import path
from rest_framework.documentation import include_docs_urls, get_schema_view
from . import api

urlpatterns = [
    path('docs/', include_docs_urls(title='Reservoir API V1')),
    path('delete/', api.delete, name='v1_delete'),
    path('health/', api.health, name='v1_health'),
    path('new_token/', api.new_token, name='v1_new_token'),
    # path('register/', api.register, name='v1_register'),
    path('revise/<int:model_id>/', api.revise, name='v1_revise_model'),
    path('search/building_id/<path:building_id>/', api.search_building_id, name='v1_search_building_id'),
    path('download/building_id/<path:building_id>/', api.download_building_id, name='v1_download_building_id'),
    path('download/batch/building_id/', api.download_batch_building_id, name='v1_download_batch_building_id'),
    path('upload/', api.upload, name='v1_upload'),
]
