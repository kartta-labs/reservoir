from django.contrib import auth
from django.contrib.auth.models import User
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject

import logging

logger = logging.getLogger(__name__)

class DevXEmailMiddleware(MiddlewareMixin):
    """ Extract the authenticated user via X-EMAIL header.

    The main application runs behinds a proxy that sets the X-EMAIL header to 
    the email of the authenticated user. In dev mode, we may not want to run behind
    a proxy. This middleware adds a default email to X-EMAIL header of the request
    to emulate the behaviour of the proxy.
    """
    def process_request(self, request):

        # Skip appending dummy user for requests for API calls
        if 'api' in request.path:
            logger.info('Skipping HTTP_X_EMAIL debug append for incoming API requests, revert to token auth.')
            return
            
        if 'HTTP_X_EMAIL' not in request.META:
            logger.warning('Appending developer@example.com to X-EMAIL header - this should only happen in debug mode.')
            request.META['HTTP_X_EMAIL'] = "developer@example.com"

def get_or_create_authenticated_user(request):
    email = request.META.pop('HTTP_X_EMAIL', None)
    if not email:
        logger.debug('No email found in header.')
        return None
    if not User.objects.filter(email=email).exists():
        logger.debug('Found {} in email header.'.format(email))
        user = User.objects.create_user(email, email, email)
        user.save()
    return User.objects.get(email=email)

def get_user(request):
    if not hasattr(request, '_cached_user'):
        request._cached_user = get_or_create_authenticated_user(request)
    return request._cached_user

class OAuthProxyAuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The OAuth Proxy authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'main.OAuthProxyAuthenticationMiddleware'."
        )

        request.user = SimpleLazyObject(lambda: get_user(request))
