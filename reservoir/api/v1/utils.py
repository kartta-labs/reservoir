import importlib
import logging

logger = logging.getLogger(__name__)

mainapp_models = importlib.import_module('third_party.3dmr.mainapp.models')
mainapp_model = getattr(mainapp_models, 'Model')
mainapp_latest_model = getattr(mainapp_models, 'LatestModel')


def build_revision_options(model, model_file, validated_data, author):
    """Build an options dictionary given client supplied validated metdata,
    |validated_data|. |model| is an instance of 3dmr.mainapp.models.Model.
    """

    options = {
        'revision': True,
        'model_id': model.model_id,
        'model_file': model_file
    }

    if validated_data.get('title') and validated_data.get('title') != model.title:
        options['title'] = validated_data.get('title')

    if validated_data.get('latitude') and validated_data.get('longitude'):
        if validated_data.get('latitude') != model.location.latitude or \
           validated_data.get('longitude') != model.location.longitude:
            options['latitude'] = validated_data.get('latitude')
            options['longitude'] = validated_data.get('longitude')

    if validated_data.get('tags'):
        options['tags'] = validated_data.get('tags')

    if validated_data.get('origin'):
        options['origin'] = validated_data.get('origin')

    if validated_data.get('translation'):
        options['translation'] = validated_data.get('translation')

    if validated_data.get('rotation'):
        options['rotation'] = validated_data.get('rotation')

    if validated_data.get('scale'):
        options['scale'] = validated_data.get('scale')

    if validated_data.get('license'):
        options['license'] = validated_data.get('license')

    options['author'] = author

    return options

def get_latest_model_by_model_id(model_id):
    query_set = mainapp_model.objects.filter(model_id=model_id).latest('revision', 'id')

    if not query_set:
        return None

    return query_set.first()
