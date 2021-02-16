import os
import logging
import mistune
import shutil

from django.db import transaction
from django.db.models import F
from django.contrib import messages

from sequences import get_next_value

from .models import Model, LatestModel, Change, Category, Location
from .utils import MODEL_DIR

from .markdown import markdown

logger = logging.getLogger(__name__)

def upload(model_file, options={}):
    try:
        with transaction.atomic():
            if options.get('revision', False):
                m = Model.objects.filter(model_id=options['model_id']).latest('revision', 'id')
                location = m.location
                if location is not None:
                    location.pk = None
                    location.id = None
                    location.save()

                # Shortcut to create a copy -> insert
                m.pk = None
                m.id = None

                m.author = options['author']
                m.location = location
                m.save()

                # Query expressions can only update not insert on the copy.
                # Which unfortunately requires two saves.
                m.revision = F('revision') + 1
                m.save()
                m.refresh_from_db()
            else:
                rendered_description = markdown(options['description'])

                latitude = options['latitude']
                longitude = options['longitude']

                if latitude and longitude:
                    location = Location(
                        latitude=latitude,
                        longitude=longitude
                    )
                    location.save()
                else:
                    location = None


                m = Model(
                    model_id=get_next_value('model_id'),
                    revision=1,
                    title=options['title'],
                    building_id=options.get('building_id'),
                    description=options['description'],
                    rendered_description=rendered_description,
                    tags=options['tags'],
                    location=location,
                    license=options['license'],
                    author=options['author'],
                    translation_x=-options['translation'][0],
                    translation_y=-options['translation'][1],
                    translation_z=-options['translation'][2],
                    rotation=options['rotation'],
                    scale=options['scale']
                )

                m.save()

                for category_name in options['categories']:
                    try:
                        category = Category.objects.get(name=category_name)
                    except:
                        category = Category(name=category_name)

                    category.save()
                    m.categories.add(category)

                m.save()

            change = Change(
                author=options['author'],
                model=m,
                typeof=1 if options.get('revision') else 0
            )

            change.save()

            filepath = '{}/{}/{}.zip'.format(MODEL_DIR, m.model_id, m.revision)
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            with open(filepath, 'wb+') as destination:
                for chunk in model_file.chunks():
                    destination.write(chunk)

            return m
    except:
        # We reach here when any of the following happens:
        # 1) Database constraint is violated
        # 2) File is not saved correctly to the specified directory
        # 3) Unknown

        # We should have verified everything to do with 1) earlier,
        # and notified the user if there was any error. Thus, it's
        # unlikely to be 1).

        # Thus, we can assume that 2) and 3) are server errors, and that
        # the user can do nothing about them. Thus, report this.
        logger.exception('Fatal server error when uploading model.')

        return None

# Edits the metadata of a model, returns True when successful, and False otherwise
def edit(options):
    try:
        with transaction.atomic():
            m = Model.objects.get(model_id=options['model_id'], revision=options['revision'])

            m.title = options['title']
            m.description = options['description']
            m.tags = options['tags']
            m.translation_x = options['translation'][0]
            m.translation_y = options['translation'][1]
            m.translation_z = options['translation'][2]
            m.rotation = options['rotation']
            m.scale = options['scale']
            m.license = options['license']

            rendered_description = markdown(options['description'])
            m.rendered_description = rendered_description

            if options.get('building_id'):
                m.building_id = options.get('building_id')

            m.categories.clear()
            for category_name in options['categories']:
                try:
                    category = Category.objects.get(name=category_name)
                except:
                    category = Category(name=category_name)

                category.save()
                m.categories.add(category)

            latitude = options['latitude']
            longitude = options['longitude']

            if latitude and longitude:
                if m.location:
                    m.location.latitude = latitude
                    m.location.longitude = longitude
                    m.location.save()
                else:
                    location = Location(
                        latitude=latitude,
                        longitude=longitude
                    )
                    location.save()
                    m.location = location
            elif m.location:
                location = m.location
                m.location = None
                location.delete()

            m.save()

            return True
    except:
        logger.exception('Fatal server error when editing metadata.')

        return False

# TODO: Add more verbose return values to pass to client. E.g., inform them of no model with model_id found.
def delete_model(options):
    logger.debug('MODEL_DIR: {}'.format(MODEL_DIR))
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
