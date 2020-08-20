import importlib
import logging
import os
import shutil

from django.db import transaction


logger = logging.getLogger(__name__)

# TODO: Add more verbose return values to pass to client. E.g., inform them of no model with model_id found.
def delete_model(options):
    MODEL_DIR = getattr(importlib.import_module('third_party.3dmr.mainapp.utils'), 'MODEL_DIR')
    logger.debug('MODEL_DIR: {}'.format(MODEL_DIR))
    Model = getattr(importlib.import_module('third_party.3dmr.mainapp.models'), 'Model')
    try:
        model_id = options['model_id']
        
        with transaction.atomic():
            # Delete the database entry
            logger.info('Deleting model with ID: {}'.format(model_id))

            # Each model may have more than one entry due to revisions. Delete them all.
            ret = Model.objects.filter(model_id=model_id)

            if not ret:
                msg = 'No model found with model_id: {}'.format(model_id)
                logger.info(msg)
                return False
                
            ret = Model.objects.filter(model_id=model_id).delete()
            logger.debug('Found Models: {}'.format(ret))

            # Delete the data on disk
            model_dir = os.path.join(MODEL_DIR, str(model_id))
            logger.info('Deleting models in db with entries: {}'.format(model_dir))
            
            if os.path.isdir(model_dir):
                shutil.rmtree(model_dir)
            else:
                logger.info('Delete requested for model id {} but model path {} does not exist.'.format(model_id, model_dir))
            return True
    except:
        logger.exception('Failed to delete model with id: {}'.format(model_id))
        
    return False
