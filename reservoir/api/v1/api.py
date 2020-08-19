import logging

from django.http import HttpResponse
from rest_framework import status
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated

logger = logging.getLogger(__name__)

@api_view(['GET'])
def health(request):
    logger.debug('Health Check')
    logger.debug('request.META: {}'.format(request.META))
    return HttpResponse(status=status.HTTP_200_OK)


