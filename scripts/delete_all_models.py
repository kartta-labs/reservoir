import importlib
import logging
import os
import shutil

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

    logger.info('Deleting all modle files on disk.')
    failed_paths = []
    for root, dirs, files in os.walk(MODEL_DIR):
        for dir_name in dirs:
            target_dir = os.path.join(root, dir_name)
            logger.info('Deleting {}'.format(target_dir))
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                failed_paths.append(target_dir)
                logger.error('Failed to delete {} for Reason: {}'.format(target_dir, e))


    if failed_paths:
        logger.error('Failed to delete all models on disk: {}'.format(failed_paths))
    else:
        logger.info('No failed deletions.')

    logger.info('Delete all models job completed.')
