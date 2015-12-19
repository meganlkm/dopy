# -*- coding: utf-8 -*-
import os

__version__ = '0.3.7a'
__license__ = 'MIT'


# default to version 2
API_VERSION = int(os.environ.get('DO_API_VERSION', 2))
CLIENT_ID = os.environ.get('DO_CLIENT_ID', None)
API_KEY = os.environ.get('DO_API_KEY', None)
API_TOKEN = os.environ.get('DO_API_TOKEN', None)

API_ENDPOINT = 'https://api.digitalocean.com'
