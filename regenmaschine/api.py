"""
File: api.py
Author: Aaron Bach
Email: bachya1208@gmail.com
Github: https://github.com/bachya/regenmaschine
"""

# -*- coding: utf-8 -*-

import logging

import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning

import regenmaschine.exceptions as exceptions
import regenmaschine.remote_status_codes as rsc

DEFAULT_TIMEOUT = 10
LOGGER = logging.getLogger(__name__)


class Response(object):  # pylint: disable=too-few-public-methods
    """ A simpler response class """

    def __init__(self, requests_response_object):
        """ Initialize! """
        self.body = requests_response_object.json()
        self.cookies = requests_response_object.cookies
        self.error = None
        self.object = requests_response_object
        self.request_url = requests_response_object.request.url
        self.successful = requests_response_object.ok

    def raise_for_status(self):
        """ Encapsulation that works with local and remote errors """

        # First, check for exceptions from the local API (which seems
        # to utilize HTTP response codes correctly):
        self.object.raise_for_status()

        # The remote API is odd: it returns error codes in the body correctly,
        # but always seems to return a status of 200. If that happens, catch it
        # and set the correct code based on the API docs before moving on:
        # response = Response(_response)
        remote_error_code = self.body.get('errorType')
        if remote_error_code and remote_error_code != 0:
            self.successful = False
            if remote_error_code in rsc.CODES.keys():
                self.error = rsc.CODES[remote_error_code]
            else:
                self.error = rsc.CODES[99]

        if not self.successful:
            raise requests.exceptions.HTTPError(
                '{} for url: {}'.format(self.error, self.request_url))



class BaseAPI(object):  # pylint: disable=too-few-public-methods
    """ Base class for interacting with the RainMachine API """

    def __init__(  # pylint: disable=too-many-arguments
            self,
            url,
            using_remote_api,
            access_token=None,
            cookies=None,
            session=None,
            timeout=DEFAULT_TIMEOUT,
            verify_ssl=True):
        """ Initialize! """
        self.url = url
        self.access_token = access_token
        self.cookies = cookies
        self.timeout = timeout
        self.session = session
        self.using_remote_api = using_remote_api
        self.verify_ssl = verify_ssl

    def _request(self, method, api_endpoint, **kwargs):
        """ Generic request method """
        kwargs.setdefault('headers', {})['Content-Type'] = 'application/json'
        if self.access_token:
            kwargs.setdefault('params', {})['access_token'] = self.access_token

        if not self.verify_ssl:
            # RainMachine uses a self-signed certificate for the local device;
            # in that case, the easiest thing to do is turn off and disable
            # warnings; if SSL is desired, the remote API should be used.
            # http://bit.ly/2rScDjk
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        resp = method(
            '{}/{}'.format(self.url, api_endpoint),
            cookies=requests.cookies.cookiejar_from_dict(self.cookies),
            verify=self.verify_ssl,
            **kwargs)

        # The requests object is great, but we need a little extra sugar when
        # checking for errors from the remote API, so we use a custom wrapper:
        response = Response(resp)
        response.raise_for_status()
        return response

    def _session_request(self, url, method, params=None, data=None, **kwargs):
        """ Wrapper for session-based requests """
        kwargs.setdefault('allow_redirects', True)
        return self.session.request(
            method=method, url=url, params=params, data=data, **kwargs)

    def _session_get(self, url, params=None, **kwargs):
        """ Session-based GET request """
        return self._session_request(url, 'get', params=params, **kwargs)

    def _session_post(self, url, data=None, **kwargs):
        """ Session-based GET request """
        return self._session_request(url, 'post', data=data, **kwargs)

    def _get(self, api_endpoint, **kwargs):
        """ Generic GET request """
        return self._request(self._session_get if self.session else
                             requests.get, api_endpoint, **kwargs)

    def _post(self, api_endpoint, **kwargs):
        """ Generic GET request """
        return self._request(self._session_post if self.session else
                             requests.post, api_endpoint, **kwargs)


def broken_remote_api(function):
    """ Decorator to define API calls that are broken in the remote API """

    def decorator(self, *args, **kwargs):
        """ Decorate! """
        if self.using_remote_api:
            raise exceptions.BrokenAPICall(
                '{}() currently broken in remote API'.format(
                    function.__name__))
        else:
            return function(self, *args, **kwargs)

    return decorator
