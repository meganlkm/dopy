#!/usr/bin/env python
#coding: utf-8
"""
This module simply sends request to the Digital Ocean API,
and returns their response as a dict.
"""

import os
import sys
import pprint


if __name__ == '__main__':
    # default to version 2
    if os.environ.get('DO_API_VERSION') == '1':
        from dopy.api.v1 import DoManager
        client_id = os.environ['DO_CLIENT_ID']
        api_key = os.environ['DO_API_KEY']
        do = DoManager(client_id, api_key, 1)
    else:
        from dopy.api.v2 import DoManager
        api_token = os.environ.get('DO_API_TOKEN') or os.environ['DO_API_KEY']
        do = DoManager(None, api_token, 2)

    fname = sys.argv[1]
    pprint.pprint(getattr(do, fname)(*sys.argv[2:]))
