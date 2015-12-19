import json
import requests
from six import wraps


class MockResponse(object):
    def __init__(self, method=None, url=None, params=None, headers=None,
                 timeout=None, data=None):
        self.url = url
        self.method = method
        self.params = params
        self.headers = headers
        self.timeout = timeout
        self.data = data
        self.status_code = 200
        self.id = '12345'
        self.droplets = []
        self.domains = []
        self.domain = {}

    def json(self):
        return self.__dict__


def _compile_request_args(params, headers, timeout):
    kwargs = {
        'headers': {} if headers is None else headers,
        'params': {} if params is None else params,
        'timeout': int(timeout)
    }
    kwargs['headers']['Content-Type'] = 'application/json'
    return kwargs


def paginated(func):
    @wraps(func)
    def wrapper(url, headers=None, params=None, timeout=60):
        nxt = url
        out = {}

        while nxt is not None:
            result = func(nxt, headers, params, 'GET')
            nxt = None

            if isinstance(result, dict):
                for key, value in result.items():
                    if key in out and isinstance(out[key], list):
                        out[key].extend(value)
                    else:
                        out[key] = value

                if 'links' in result \
                        and 'pages' in result['links'] \
                        and 'next' in result['links']['pages']:
                    nxt = result['links']['pages']['next']

        return out
    return wrapper


def post_request(url, params=None, headers=None, timeout=60):
    kwargs = _compile_request_args(params, headers, timeout)
    kwargs['data'] = json.dumps(kwargs['params'])
    del(kwargs['params'])
    # return requests.post(url, **kwargs)
    return MockResponse('POST', url, **kwargs)


def put_request(url, params=None, headers=None, timeout=60):
    kwargs = _compile_request_args(params, headers, timeout)
    # return requests.put(url, **kwargs)
    return MockResponse('PUT', url, **kwargs)


def delete_request(url, params=None, headers=None, timeout=60):
    kwargs = _compile_request_args(params, headers, timeout)
    # resp = requests.delete(url, **kwargs)
    # resp.json = {'status': resp.status_code}
    # return resp
    return MockResponse('DELETE', url, **kwargs)


# @paginated
def get_request(url, params=None, headers=None, timeout=60):
    kwargs = _compile_request_args(params, headers, timeout)
    return requests.get(url, **kwargs)
    # return MockResponse('GET', url, **kwargs)
