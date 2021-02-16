import importlib
import logging
import os
import shutil

from django.db import transaction


logger = logging.getLogger(__name__)

MODEL_DIR = getattr(importlib.import_module('third_party.3dmr.mainapp.utils'), 'MODEL_DIR')

def get_model_path(model_id, revision):
    return "{}/{}/{}.zip".format(MODEL_DIR, model_id, revision)
