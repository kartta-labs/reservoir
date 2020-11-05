import importlib
import logging
import glob
import os
import shutil
import sys

mainapp_database = importlib.import_module('third_party.3dmr.mainapp.database')
mainapp_upload = getattr(mainapp_database, 'upload')
mainapp_models = importlib.import_module('third_party.3dmr.mainapp.models')
mainapp_model = getattr(mainapp_models, 'Model')
mainapp_location = getattr(mainapp_models, 'Location')
mainapp_change = getattr(mainapp_models, 'Change')
MODEL_DIR = getattr(importlib.import_module('third_party.3dmr.mainapp.utils'), 'MODEL_DIR')

logger = logging.getLogger(__name__)

def run(*args):
    """Will **DELETE ALL MODELS** in DB and on storage.

    This is dangerous and there is no going back. Use wisely.
    """
    logger.info('Deleting all models and data.')

    logger.info('Cearing database model entries.')
    mainapp_model.objects.all().delete()
    mainapp_location.objects.all().delete()
    mainapp_change.objects.all().delete()


    model_dir_glob = os.path.join(MODEL_DIR,'[0-9]*')
    logger.info('model_dir_glob = {}'.format(model_dir_glob))

    paths_to_delete = glob.glob(model_dir_glob)
    logger.info('Found {} paths to delete.'.format(len(paths_to_delete)))
    failed_paths = []
    for target_dir in paths_to_delete:
        try:
            logger.info('Deleting {}'.format(target_dir))
            shutil.rmtree(target_dir)
        except:
            e = sys.exc_info()[0]
            logger.error('Failed to delete {}, reason: {}'.format(target_dir, e))
            failed_paths.append(target_dir)

    if failed_paths:
        logger.error('Failed to delete all models on disk: {}'.format(failed_paths))
    else:
        logger.info('No failed deletions.')

    logger.info('Delete all models job completed.')
