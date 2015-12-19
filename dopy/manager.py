#!/usr/bin/env python
#coding: utf-8
"""
This module simply sends request to the Digital Ocean API,
and returns their response as a dict.
"""

import sys
import pprint
from dopy import API_VERSION


if __name__ == '__main__':
    if API_VERSION == 1:
        from dopy.api.v1 import DoManager
        from dopy import CLIENT_ID, API_KEY
        do = DoManager(CLIENT_ID, API_KEY, 1)
        fname = sys.argv[1]
        pprint.pprint(getattr(do, fname)(*sys.argv[2:]))
    else:
        from dopy.api.v2 import DoManager
        do = DoManager()
        fname = sys.argv[1]

        try:
            pprint.pprint(do.retro_execution(fname, *sys.argv[2:]))
        except:
            pprint.pprint(getattr(do, fname)(*sys.argv[2:]))
