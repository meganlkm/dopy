#!/usr/bin/env python
#coding: utf-8
"""
This module simply sends request to the Digital Ocean API,
and returns their response as a dict.
"""

import os
import sys
import pprint
import requests
from json import dumps

API_ENDPOINT = 'https://api.digitalocean.com'

REQUEST_FUNCS ={
    'POST': requests.post,
    'DELETE': requests.delete,
    'PUT': requests.put,
    'GET': requests.get
}


class DoError(RuntimeError):
    pass


class ApiMixin(object):
    client_id = None
    api_key = None

    @property
    def droplets(self):
        return '/droplets'

    def droplets_url(self, droplet_id=None, action=None):
        url = self.droplets
        if droplet_id:
            url = '{0}/{1}'.format(url, droplet_id)
        if action:
            url = '{0}/{1}'.format(url, action)
        return url

    def request(self, url, method='GET', timeout=60, *args, **kwargs):
        try:
            response = REQUEST_FUNCS[method](url, timeout=timeout, **kwargs)
        except KeyError:
            raise DoError('Unsupported method {0}'.format(method))
        except Exception as e:
            raise e

        try:
            response_json = response.json()
        except ValueError:
            raise ValueError("The API server doesn't respond with a valid json")

        if response.status_code != requests.codes.ok:
            if response_json:
                if 'error_message' in response_json:
                    raise DoError(response_json['error_message'])
                elif 'message' in response_json:
                    raise DoError(response_json['message'])
            # The JSON reponse is bad, so raise an exception with the HTTP status
            response.raise_for_status()

        return response_json


class ApiV1Mixin(ApiMixin):

    @property
    def endpoint(self):
        return '{}/v1'.format(API_ENDPOINT)

    def prepare_request_params(self, params=None, *args, **kwargs):
        if params is None:
            params = dict()
        return {'params': params}

    def parse_response(self, response_json):
        if response_json.get('status') != 'OK':
            raise DoError(response_json['error_message'])
        return response_json

    def parse_droplets(self, response):
        return response['droplets']


class ApiV2Mixin(ApiMixin):

    @property
    def endpoint(self):
        return '{}/v2'.format(API_ENDPOINT)

    def prepare_request_params(self, method='GET', params=None,
                               headers=None, *args, **kwargs):
        if params is None:
            params = dict()

        request_params = {'headers': headers}
        param_key = 'data' if method == 'POST' else 'params'

        request_params['headers'] = dict() if headers is None else headers
        request_params[param_key] = params if method != 'POST' else dumps(params)

        request_params['headers']['Authorization'] = 'Bearer {0}'.format(self.api_key)
        request_params['headers']['Content-Type'] = 'application/json'

        return request_params

    def parse_response(self, response_json):
        if response_json.get('id') == 'not_found':
            raise DoError(response_json['message'])

        return response_json

    def parse_droplet(self, response):
        droplet = response['droplet']
        try:
            droplet[u'ip_address'] = droplet['networks']['v4'][0]['ip_address']
        except IndexError:
            droplet[u'ip_address'] = ''
        return droplet

    def parse_droplets(self, response):
        if 'droplets' in response:
            for droplet in response['droplets']:
                try:
                    droplet[u'ip_address'] = droplet['networks']['v4'][0]['ip_address']
                except IndexError:
                    droplet[u'ip_address'] = ''
        return response['droplets']


class DoManager(object):

    def __init__(self, client_id, api_key, api_version=1):
        if api_version == 1:
            self.api = ApiV1Mixin()
        elif api_version == 2:
            self.api = ApiV2Mixin()
        else:
            raise DoError('Invalid API Version')

        self.api.client_id = client_id
        self.api.api_key = api_key
        self.api_version = int(api_version)

    def request(self, path, *args, **kwargs):
        request_params = self.api.prepare_request_params(*args, **kwargs)
        response = self.api.request(self.gen_url(path), **request_params)
        return self.api.parse_response(response)

    def gen_url(self, path):
        if not path.startswith('/'):
            path = '/{}'.format(path)
        return self.api.endpoint + path

    def all_active_droplets(self):
        response = self.request(self.api.droplets_url())
        return self.api.parse_droplets(response)

    def show_droplet(self, droplet_id):
        response = self.request(self.api.droplets_url(droplet_id))
        return self.api.parse_droplet(response)

    def new_droplet(self, name, size_id, image_id, region_id,
                    ssh_key_ids=None, virtio=True, private_networking=False,
                    backups_enabled=False, user_data=None, ipv6=False):
        if self.api_version == 2:
            params = {
                'name': str(name),
                'size': str(size_id),
                'image': str(image_id),
                'region': str(region_id),
                'virtio': str(virtio).lower(),
                'ipv6': str(ipv6).lower(),
                'private_networking': str(private_networking).lower(),
                'backups': str(backups_enabled).lower(),
            }
            if ssh_key_ids:
                # Need to be an array in v2
                if isinstance(ssh_key_ids, basestring):
                    ssh_key_ids = [ssh_key_ids]

                if type(ssh_key_ids) == list:
                    for index in range(len(ssh_key_ids)):
                        ssh_key_ids[index] = str(ssh_key_ids[index])

                params['ssh_keys'] = ssh_key_ids

            if user_data:
                params['user_data'] = user_data

            response = self.request('/droplets', params=params, method='POST')
            created_id = response['droplet']['id']
            response = self.show_droplet(created_id)
            return response
        else:
            params = {
                'name': str(name),
                'size_id': str(size_id),
                'image_id': str(image_id),
                'region_id': str(region_id),
                'virtio': str(virtio).lower(),
                'private_networking': str(private_networking).lower(),
                'backups_enabled': str(backups_enabled).lower(),
            }
            if ssh_key_ids:
                # Need to be a comma separated string
                if type(ssh_key_ids) == list:
                    ssh_key_ids = ','.join(ssh_key_ids)
                params['ssh_key_ids'] = ssh_key_ids

            response = self.request('/droplets/new', params=params)
            return response['droplet']

    def droplet_v2_action(self, droplet_id, droplet_type, params=None):
        if params is None:
            params = {}
        params['type'] = droplet_type
        response = self.request('/droplets/%s/actions' % droplet_id, params=params, method='POST')
        return response

    def reboot_droplet(self, droplet_id):
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'reboot')
        else:
            response = self.request('/droplets/%s/reboot/' % droplet_id)
        response.pop('status', None)
        return response

    def power_cycle_droplet(self, droplet_id):
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'power_cycle')
        else:
            response = self.request('/droplets/%s/power_cycle/' % droplet_id)
        response.pop('status', None)
        return response

    def shutdown_droplet(self, droplet_id):
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'shutdown')
        else:
            response = self.request('/droplets/%s/shutdown/' % droplet_id)
        response.pop('status', None)
        return response

    def power_off_droplet(self, droplet_id):
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'power_off')
        else:
            response = self.request('/droplets/%s/power_off/' % droplet_id)
        response.pop('status', None)
        return response

    def power_on_droplet(self, droplet_id):
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'power_on')
        else:
            response = self.request('/droplets/%s/power_on/' % droplet_id)
        response.pop('status', None)
        return response

    def password_reset_droplet(self, droplet_id):
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'password_reset')
        else:
            response = self.request('/droplets/%s/password_reset/' % droplet_id)
        response.pop('status', None)
        return response

    def resize_droplet(self, droplet_id, size_id):
        if self.api_version == 2:
            params = {'size': size_id}
            response = self.droplet_v2_action(droplet_id, 'resize', params)
        else:
            params = {'size_id': size_id}
            response = self.request('/droplets/%s/resize/' % droplet_id, params)
        response.pop('status', None)
        return response

    def snapshot_droplet(self, droplet_id, name):
        params = {'name': name}
        if self.api_version == 2:
            response = self.droplet_v2_action(droplet_id, 'snapshot', params)
        else:
            response = self.request('/droplets/%s/snapshot/' % droplet_id, params)
        response.pop('status', None)
        return response

    def restore_droplet(self, droplet_id, image_id):
        if self.api_version == 2:
            params = {'image': image_id}
            response = self.droplet_v2_action(droplet_id, 'restore', params)
        else:
            params = {'image_id': image_id}
            response = self.request('/droplets/%s/restore/' % droplet_id, params)
        response.pop('status', None)
        return response

    def rebuild_droplet(self, droplet_id, image_id):
        if self.api_version == 2:
            params = {'image': image_id}
            json = self.droplet_v2_action(droplet_id, 'rebuild', params)
        else:
            params = {'image_id': image_id}
            json = self.request('/droplets/%s/rebuild/' % droplet_id, params)
        json.pop('status', None)
        return json

    def enable_backups_droplet(self, droplet_id):
        if self.api_version == 2:
            json = self.droplet_v2_action(droplet_id, 'enable_backups')
        else:
            json = self.request('/droplets/%s/enable_backups/' % droplet_id)
        json.pop('status', None)
        return json

    def disable_backups_droplet(self, droplet_id):
        if self.api_version == 2:
            json = self.droplet_v2_action(droplet_id, 'disable_backups')
        else:
            json = self.request('/droplets/%s/disable_backups/' % droplet_id)
        json.pop('status', None)
        return json

    def rename_droplet(self, droplet_id, name):
        params = {'name': name}
        if self.api_version == 2:
            json = self.droplet_v2_action(droplet_id, 'rename', params)
        else:
            json = self.request('/droplets/%s/rename/' % droplet_id, params)
        json.pop('status', None)
        return json

    def destroy_droplet(self, droplet_id, scrub_data=True):
        if self.api_version == 2:
            json = self.request('/droplets/%s' % droplet_id, method='DELETE')
        else:
            params = {'scrub_data': '1' if scrub_data else '0'}
            json = self.request('/droplets/%s/destroy/' % droplet_id, params)
        json.pop('status', None)
        return json

#regions==========================================
    def all_regions(self):
        json = self.request('/regions/')
        return json['regions']

#images==========================================
    def all_images(self, filter='global'):
        params = {'filter': filter}
        json = self.request('/images/', params)
        return json['images']

    def image_v2_action(self, image_id, image_type, params=None):
        if params is None:
            params = {}
        params['type'] = image_type
        json = self.request('/images/%s/actions' % image_id, params=params, method='POST')
        return json

    def show_image(self, image_id):
        params = {'image_id': image_id}
        json = self.request('/images/%s' % image_id)
        return json['image']

    def destroy_image(self, image_id):
        if self.api_version == 2:
            self.request('/images/%s' % image_id, method='DELETE')
        else:
            self.request('/images/%s/destroy' % image_id)
        return True

    def transfer_image(self, image_id, region_id):
        if self.api_version == 2:
            params = {'region': region_id}
            json = self.image_v2_action(image_id, 'transfer', params)
        else:
            params = {'region_id': region_id}
            json = self.request('/images/%s/transfer' % image_id, params)
        json.pop('status', None)
        return json

#ssh_keys=========================================
    def all_ssh_keys(self):
        if self.api_version == 2:
            json = self.request('/account/keys')
        else:
            json = self.request('/ssh_keys/')
        return json['ssh_keys']

    def new_ssh_key(self, name, pub_key):
        if self.api_version == 2:
            params = {'name': name, 'public_key': pub_key}
            json = self.request('/account/keys', params, method='POST')
        else:
            params = {'name': name, 'ssh_pub_key': pub_key}
            json = self.request('/ssh_keys/new/', params)
        return json['ssh_key']

    def show_ssh_key(self, key_id):
        if self.api_version == 2:
            json = self.request('/account/keys/%s/' % key_id)
        else:
            json = self.request('/ssh_keys/%s/' % key_id)
        return json['ssh_key']

    def edit_ssh_key(self, key_id, name, pub_key):
        if self.api_version == 2:
            params = {'name': name} # v2 API doesn't allow to change key body now
            json = self.request('/account/keys/%s/' % key_id, params, method='PUT')
        else:
            params = {'name': name, 'ssh_pub_key': pub_key}  # the doc needs to be improved
            json = self.request('/ssh_keys/%s/edit/' % key_id, params)
        return json['ssh_key']

    def destroy_ssh_key(self, key_id):
        if self.api_version == 2:
            self.request('/account/keys/%s' % key_id, method='DELETE')
        else:
            self.request('/ssh_keys/%s/destroy/' % key_id)
        return True

#sizes============================================
    def sizes(self):
        json = self.request('/sizes/')
        return json['sizes']

#domains==========================================
    def all_domains(self):
        json = self.request('/domains/')
        return json['domains']

    def new_domain(self, name, ip):
        params = {
                'name': name,
                'ip_address': ip
            }
        if self.api_version == 2:
            json = self.request('/domains', params=params, method='POST')
        else:
            json = self.request('/domains/new/', params)
        return json['domain']

    def show_domain(self, domain_id):
        json = self.request('/domains/%s/' % domain_id)
        return json['domain']

    def destroy_domain(self, domain_id):
        if self.api_version == 2:
            self.request('/domains/%s' % domain_id, method='DELETE')
        else:
            self.request('/domains/%s/destroy/' % domain_id)
        return True

    def all_domain_records(self, domain_id):
        json = self.request('/domains/%s/records/' % domain_id)
        if self.api_version == 2:
            return json['domain_records']
        return json['records']

    def new_domain_record(self, domain_id, record_type, data, name=None, priority=None, port=None, weight=None):
        params = {'data': data}

        if self.api_version == 2:
            params['type'] = record_type
        else:
            params['record_type'] = record_type

        if name: params['name'] = name
        if priority: params['priority'] = priority
        if port: params['port'] = port
        if weight: params['weight'] = weight

        if self.api_version == 2:
            json = self.request('/domains/%s/records/' % domain_id, params, method='POST')
            return json['domain_record']
        else:
            json = self.request('/domains/%s/records/new/' % domain_id, params)
            return json['record']

    def show_domain_record(self, domain_id, record_id):
        json = self.request('/domains/%s/records/%s' % (domain_id, record_id))
        if self.api_version == 2:
            return json['domain_record']
        return json['record']

    def edit_domain_record(self, domain_id, record_id, record_type, data, name=None, priority=None, port=None, weight=None):
        if self.api_version == 2:
            params = {'name': name} # API v.2 allows only record name change
            json = self.request('/domains/%s/records/%s' % (domain_id, record_id), params, method='PUT')
            return json['domain_record']

        params = {
            'record_type': record_type,
            'data': data,
        }

        if name: params['name'] = name
        if priority: params['priority'] = priority
        if port: params['port'] = port
        if weight: params['weight'] = weight
        json = self.request('/domains/%s/records/%s/edit/' % (domain_id, record_id), params)
        return json['record']

    def destroy_domain_record(self, domain_id, record_id):
        if self.api_version == 2:
            self.request('/domains/%s/records/%s' % (domain_id, record_id), method='DELETE')
        else:
            self.request('/domains/%s/records/%s/destroy/' % (domain_id, record_id))
        return True

#events(actions in v2 API)========================
    def show_all_actions(self):
        if self.api_version == 2:
            json = self.request('/actions')
            return json['actions']
        return False # API v.1 haven't this functionality

    def show_action(self, action_id):
        if self.api_version == 2:
            json = self.request('/actions/%s' % event_id)
            return json['action']
        return show_event(self, action_id)

    def show_event(self, event_id):
        if self.api_version == 2:
            return show_action(self, event_id)
        json = self.request('/events/%s' % event_id)
        return json['event']


if __name__ == '__main__':
    api_version = os.environ.get('DO_API_VERSION')
    api_key = os.environ.get('DO_API_TOKEN') or os.environ.get('DO_API_KEY')
    client_id = os.environ.get('DO_CLIENT_ID')

    print api_key

    if not all([api_version, api_key]):
        print 'Required DO environment variables are not set.'
        sys.exit(1)

    do = DoManager(client_id, api_key, int(api_version))

    print do.api.endpoint
    # print do.api.droplets_url(234234)

    fname = sys.argv[1]
    print fname
    # size_id: 66, image_id: 1601, region_id: 1
    pprint.pprint(getattr(do, fname)(*sys.argv[2:]))
