import importlib
import logging
import json
from zipfile import ZipFile, BadZipFile

from pywavefront import Wavefront

from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest, HttpResponseServerError
from rest_framework import serializers, status
from rest_framework.authtoken.models import Token
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import IsAuthenticated

from .database import delete_model

DEFAULT_MAX_CHAR_LENGTH = 128

# Must use dynamic imports from 3dmr as valid python modules cannot start with a number.
ModelExtractor = getattr(
    importlib.import_module('third_party.3dmr.mainapp.model_extractor'),
    'ModelExtractor')

database = importlib.import_module('third_party.3dmr.mainapp.database')
models = importlib.import_module('third_party.3dmr.mainapp.models')
Model = getattr(models, 'Model')
User = getattr(models, 'User')

logger = logging.getLogger(__name__)

LICENSE_CHOICES = [
    (0, 'Creative Commons CC0 1.0 Universal Public Domain Dedication'),
    (1, 'Creative Commons Attribution 4.0 Internal license')
]

class ModelFileField(serializers.FileField):
    def to_internal_value(self, value):
        try:
            zip_file = ZipFile(value)
            logger.debug('inspecting zip file.')
            found_objs = 0 # files with the .obj extension found
            for name in zip_file.namelist():
                logger.debug('Found file with name: {}'.format(name))
                if name.endswith('.obj'):
                    found_objs += 1
            if found_objs != 1:
                logger.debug('No .obj file in upload.')
                raise serializers.ValidationError('No single .obj file found in your uploaded zip file.', code='invalid')

            with ModelExtractor(zip_file) as extracted_location:
                try:
                    scene = Wavefront(extracted_location['obj'])
                except:
                    logger.debug('Error parsing OBJ/MTL files.')
                    raise serializers.ValidationError('Error parsing OBJ/MTL files.', code='invalid')
        except BadZipFile:
            logger.debug('BadZipFile exception.')
            raise serializers.ValidationError('Uploaded file was not a valid zip file.', code='invalid')

        logger.debug('Custom zip validation successful.')
        return super().to_internal_value(value)

    
class ModelFileMetadataSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=DEFAULT_MAX_CHAR_LENGTH, default='')
    description = serializers.CharField(max_length=1028, default='')
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    categories = serializers.CharField(max_length=1028, default='')
    tags = serializers.DictField(child=serializers.CharField(), default={})
    origin = serializers.ListField(child=serializers.FloatField(), default=[0., 0., 0.])
    translation = serializers.ListField(child=serializers.FloatField(), default=[0., 0., 0.])
    rotation = serializers.FloatField(default=0.0)
    scale = serializers.FloatField(default=1.0)
    license = serializers.ChoiceField(LICENSE_CHOICES, allow_blank=True)

    
class ModelFileSerializer(serializers.Serializer):
    model_file = ModelFileField()
    # For accepting model metadata as a json blob.
    # This is a workaround as Django Rest Framework struggles with multi-part posts
    # and must accept the file upload as a form post. Internally we'll de-serialize
    # the json field with the ModelFileMetadataSerializer
    metadata = serializers.JSONField(required=False)

class UserSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=DEFAULT_MAX_CHAR_LENGTH)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(default='')
    
@api_view(['GET'])
def health(request):
    logger.debug('Health Check')
    logger.debug('request.META: {}'.format(request.META))
    return HttpResponse(status=status.HTTP_200_OK)


@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def upload(request):
    """Api endpoint to upload a model zip file.

    Example: 
    curl -i -X POST -F 'model_file=@/Some/path/to/models.zip' \
    -F 'latitude=38.1' -F 'longitude=2.1' -F 'license=0' -F 'tags=building_id=foo' \
    -H 'Authorization: Token [insert token here]' \
    http://localhost:8080/api/v1/upload/
    """

    logger.debug('{} requests file upload.'.format(request.user.username))
    
    try:
        serialized_model = ModelFileSerializer(data=request.data)
    except:
        import sys, traceback
        traceback.print_exc(file=sys.stdout)
        err_msg = 'Faild to validate model file upload request data.'
        logger.warning(err_msg)
        return HttpResponseBadRequest(err_msg)
    
    if serialized_model.is_valid():
        model_metadata = ModelFileMetadataSerializer(data=serialized_model.validated_data.get('metadata'))
    else:
        err_msg = 'Failed to validate model payload.'
        logger.warning(err_msg)
        return HttpResponseBadRequest(err_msg)

    if model_metadata.is_valid():
        logger.debug('Upload payload verified.')
        logger.debug('Validated meta data: {}'.format(model_metadata.validated_data))
        try:
            model = database.upload(serialized_model.validated_data.get('model_file'),
                                    {'title': model_metadata.validated_data.get('title'),
                                     'description': model_metadata.validated_data.get('description'),
                                     'latitude': model_metadata.validated_data.get('latitude'),
                                     'longitude': model_metadata.validated_data.get('longitude'),
                                     'categories': model_metadata.validated_data.get('categories'),
                                     'tags': model_metadata.validated_data.get('tags'),
                                     'origin': model_metadata.validated_data.get('origin'),
                                     'translation': model_metadata.validated_data.get('translation'),
                                     'rotation': model_metadata.validated_data.get('rotation'),
                                     'scale': model_metadata.validated_data.get('scale'),
                                     'license':model_metadata.validated_data.get('license', None),
                                     'author':request.user})
        except:
            err_msg = 'Failed to upload model.'
            logger.warning(err_msg)
            return HttpResponseServerError(err_msg)

    else:
        err_msg = 'Failed to validate upload_model payload.'
        logger.warning(err_msg)
        return HttpResponseBadRequest(err_msg)

    response_data = {
        "model_id": model.model_id,
        "author": model.author.username,
        "revision": model.revision,
        "upload_date": model.upload_date,
    }
    
    return JsonResponse(response_data, safe=False, status=status.HTTP_201_CREATED)



@api_view(['POST'])
@authentication_classes([TokenAuthentication])
@permission_classes([IsAuthenticated])
def delete(request):
    """API endpoint to delete a given model by ID.
    
    Example:
    curl -i -X POST -H 'Authorization: Token [insert token here]' \
    -H 'Content-Type: application/json'
    http://localhost:8080/api/v1/delete/
    -d '{"model_id": 12}'
    """

    try:
        data = json.loads(request.body)
        model_id = data['model_id']
    except:
        return HttpResponseBadRequest('Must provide model_id as json POST data.')
    
    logger.debug('{} requesets deletion of model id {}'.format(request.user.username, model_id))
    
    # There may be more than one revision associated with each model id.
    # However, each revision should belong to the original author.
    models = Model.objects.filter(model_id=model_id)
    for m in models:
        if request.user != m.author:
            return HttpResponseBadRequest('Must be author of the model to delete the model.')
    
    options = {
        'model_id': model_id,
    }
    
    if delete_model(options):
        logger.info('Deleted model id: {}'.format(data.get('model_id')))
    else:
        err_msg = 'Failed to delete model with id: {}'.format(data.get('model_id'))
        return HttpResponseServerError(err_msg)

    response_data = {
        'model_id': model_id,
        'status': 'deleted'
    }
    
    return JsonResponse(response_data,status=status.HTTP_202_ACCEPTED)

@api_view(['POST'])
def register(request):
    serialized = UserSerializer(data=request.data)
    
    if serialized.is_valid():
        logger.debug('data: {}'.format(serialized.data))
        user = User.objects.create_user(
            serialized.data.get('username'),
            serialized.data.get('password'),
            serialized.data.get('email')
        )

        user.save()

        token = Token.objects.get(user=user)

        response_data = {
            'username': serialized.data.get('username'),
            'email': serialized.data.get('email'),
            'token': token.key
        }

        logger.info('Created user: {} with token {}'.format(serialized.data.get('username'), token.key))
        
        return JsonResponse(response_data, status=status.HTTP_201_CREATED)
    else:
        logger.error('Failed to create user: {}'.format(serialized.data))
        return HttpResponseBadRequest(serialized._errors)
