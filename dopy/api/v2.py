#!/usr/bin/env python
#coding: utf-8
"""
This module simply sends request to the Digital Ocean API,
and returns their response as a dict.
"""

from requests import codes, RequestException
from dopy import API_TOKEN, API_ENDPOINT
from dopy import common as c
from dopy.exceptions import DoError

REQUEST_METHODS = {
    'POST': c.post_request,
    'PUT': c.put_request,
    'DELETE': c.delete_request,
    'GET': c.get_request,
}


class ApiRequest(object):

    def __init__(self, uri=None, headers=None, params=None,
                 timeout=60, method='GET'):
        self.set_url(uri)
        self.set_headers(headers)
        self.params = params
        self.timeout = timeout
        self.method = method
        self.response = None
        self._verify_method()

    def set_headers(self, headers):
        self.headers = {} if not isinstance(headers, dict) else headers
        self.headers['Authorization'] = "Bearer %s" % API_TOKEN

    def set_url(self, uri):
        if uri is None:
            uri = '/'
        if not uri.startswith('/'):
            uri = '/' + uri
        self.url = '{}/v2{}'.format(API_ENDPOINT, uri)

    def _verify_method(self):
        if self.method not in REQUEST_METHODS.keys():
            raise DoError('Unsupported method %s' % self.method)

    def _verify_status_code(self):
        if self.response.status_code != codes.ok:
            try:
                if 'error_message' in self.response:
                    raise DoError(self.response['error_message'])
                elif 'message' in self.response:
                    raise DoError(self.response['message'])
            except:
                # The JSON reponse is bad, so raise an exception with the HTTP status
                self.response.raise_for_status()

    def _verify_response_id(self):
        response = self.response.json()
        if response.get('id') == 'not_found':
            raise DoError(response['message'])

    def run(self):
        try:
            self.response = REQUEST_METHODS[self.method](self.url, self.params, self.headers, self.timeout)
        except ValueError:
            raise ValueError("The API server doesn't respond with a valid json")
        except RequestException as e:
            raise RuntimeError(e)

        self._verify_status_code()
        self._verify_response_id()
        return self.response.json()


class DoApiV2Base(object):

    def request(self, path, params={}, method='GET'):
        api = ApiRequest(path, params=params, method=method)
        return api.run()

    @classmethod
    def get_endpoint(cls, pathlist=None, trailing_slash=False):
        if pathlist is None:
            pathlist = []
        pathlist.insert(0, cls.endpoint)
        if trailing_slash:
            pathlist.append('')
        return '/'.join(pathlist)


class DoManager(DoApiV2Base):

    def __init__(self):
        self.api_endpoint = API_ENDPOINT

    def retro_execution(self, method_name, *args, **kwargs):
        retrometh = {
            "all_active_droplets": DoApiDroplets().list,
            "new_droplet": DoApiDroplets().create,
            "show_droplet": DoApiDroplets().show_droplet,
            "droplet_v2_action": DoApiDroplets().droplet_v2_action,
            "reboot_droplet": DoApiDroplets().reboot_droplet,
            "power_cycle_droplet": DoApiDroplets().power_cycle_droplet,
            "shutdown_droplet": DoApiDroplets().shutdown_droplet,
            "power_off_droplet": DoApiDroplets().power_off_droplet,
            "power_on_droplet": DoApiDroplets().power_on_droplet,
            "password_reset_droplet": DoApiDroplets().password_reset_droplet,
            "resize_droplet": DoApiDroplets().resize_droplet,
            "snapshot_droplet": DoApiDroplets().snapshot_droplet,
            "restore_droplet": DoApiDroplets().restore_droplet,
            "rebuild_droplet": DoApiDroplets().rebuild_droplet,
            "enable_backups_droplet": DoApiDroplets().enable_backups_droplet,
            "disable_backups_droplet": DoApiDroplets().disable_backups_droplet,
            "rename_droplet": DoApiDroplets().rename_droplet,
            "destroy_droplet": DoApiDroplets().destroy_droplet,
            "populate_droplet_ips": DoApiDroplets().populate_droplet_ips,
            "all_domains": DoApiDomains().list,
            "new_domain": DoApiDomains().create,
            "show_domain": DoApiDomains().show,
        }
        return retrometh[method_name](*args, **kwargs)

    # regions==========================================
    def all_regions(self):
        json = self.request('/regions/')
        return json['regions']

    # images==========================================
    def all_images(self, filter='global'):
        params = {'filter': filter}
        json = self.request('/images/', params)
        return json['images']

    def private_images(self):
        json = self.request('/images?private=true')
        return json['images']

    def image_v2_action(self, image_id, image_type, params=None):
        if params is None:
            params = {}
        params['type'] = image_type
        json = self.request('/images/%s/actions' % image_id, params=params, method='POST')
        return json

    def show_image(self, image_id):
        json = self.request('/images/%s' % image_id)
        return json['image']

    def destroy_image(self, image_id):
        self.request('/images/%s' % image_id, method='DELETE')
        return True

    def transfer_image(self, image_id, region_id):
        params = {'region': region_id}
        json = self.image_v2_action(image_id, 'transfer', params)
        json.pop('status', None)
        return json

    # ssh_keys=========================================
    def all_ssh_keys(self):
        json = self.request('/account/keys')
        return json['ssh_keys']

    def new_ssh_key(self, name, pub_key):
        params = {'name': name, 'public_key': pub_key}
        json = self.request('/account/keys', params, method='POST')
        return json['ssh_key']

    def show_ssh_key(self, key_id):
        json = self.request('/account/keys/%s/' % key_id)
        return json['ssh_key']

    def edit_ssh_key(self, key_id, name, pub_key):
        # v2 API doesn't allow to change key body now
        params = {'name': name}
        json = self.request('/account/keys/%s/' % key_id, params, method='PUT')
        return json['ssh_key']

    def destroy_ssh_key(self, key_id):
        self.request('/account/keys/%s' % key_id, method='DELETE')
        return True

    # sizes============================================
    def sizes(self):
        json = self.request('/sizes/')
        return json['sizes']

    # events(actions in v2 API)========================
    def show_all_actions(self):
        json = self.request('/actions')
        return json['actions']

    def show_action(self, action_id):
        json = self.request('/actions/%s' % action_id)
        return json['action']

    def show_event(self, event_id):
        return self.show_action(event_id)


class DoApiDroplets(DoApiV2Base):

    endpoint = '/droplets'

    def list(self):
        json = self.request(self.get_endpoint(trailing_slash=True))
        for index in range(len(json['droplets'])):
            self.populate_droplet_ips(json['droplets'][index])
        return json['droplets']

    def create(self, name, size_id, image_id, region_id,
               ssh_key_ids=None, virtio=True, private_networking=False,
               backups_enabled=False, user_data=None, ipv6=False):
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

            if isinstance(ssh_key_ids, list):
                for index in range(len(ssh_key_ids)):
                    ssh_key_ids[index] = str(ssh_key_ids[index])

            params['ssh_keys'] = ssh_key_ids

        if user_data:
            params['user_data'] = user_data

        json = self.request(self.get_endpoint(), params=params, method='POST')
        created_id = json['droplet']['id']
        json = self.show_droplet(created_id)
        return json

    def show_droplet(self, droplet_id):
        json = self.request(self.get_endpoint([droplet_id]))
        self.populate_droplet_ips(json['droplet'])
        return json['droplet']

    def droplet_v2_action(self, droplet_id, droplet_type, params=None):
        if params is None:
            params = {}
        params['type'] = droplet_type
        return self.request(self.get_endpoint([droplet_id, 'actions']), params=params, method='POST')

    def reboot_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'reboot')
        json.pop('status', None)
        return json

    def power_cycle_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'power_cycle')
        json.pop('status', None)
        return json

    def shutdown_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'shutdown')
        json.pop('status', None)
        return json

    def power_off_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'power_off')
        json.pop('status', None)
        return json

    def power_on_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'power_on')
        json.pop('status', None)
        return json

    def password_reset_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'password_reset')
        json.pop('status', None)
        return json

    def resize_droplet(self, droplet_id, size_id):
        params = {'size': size_id}
        json = self.droplet_v2_action(droplet_id, 'resize', params)
        json.pop('status', None)
        return json

    def snapshot_droplet(self, droplet_id, name):
        params = {'name': name}
        json = self.droplet_v2_action(droplet_id, 'snapshot', params)
        json.pop('status', None)
        return json

    def restore_droplet(self, droplet_id, image_id):
        params = {'image': image_id}
        json = self.droplet_v2_action(droplet_id, 'restore', params)
        json.pop('status', None)
        return json

    def rebuild_droplet(self, droplet_id, image_id):
        params = {'image': image_id}
        json = self.droplet_v2_action(droplet_id, 'rebuild', params)
        json.pop('status', None)
        return json

    def enable_backups_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'enable_backups')
        json.pop('status', None)
        return json

    def disable_backups_droplet(self, droplet_id):
        json = self.droplet_v2_action(droplet_id, 'disable_backups')
        json.pop('status', None)
        return json

    def rename_droplet(self, droplet_id, name):
        params = {'name': name}
        json = self.droplet_v2_action(droplet_id, 'rename', params)
        json.pop('status', None)
        return json

    def destroy_droplet(self, droplet_id, scrub_data=True):
        json = self.request(self.get_endpoint([droplet_id]), method='DELETE')
        json.pop('status', None)
        return json

    def populate_droplet_ips(self, droplet):
        droplet[u'ip_address'] = ''
        for networkIndex in range(len(droplet['networks']['v4'])):
            network = droplet['networks']['v4'][networkIndex]
            if network['type'] == 'public':
                droplet[u'ip_address'] = network['ip_address']
            if network['type'] == 'private':
                droplet[u'private_ip_address'] = network['ip_address']


class DoApiDomains(DoApiV2Base):

    endpoint = '/domains'

    def list(self):
        json = self.request(self.get_endpoint(trailing_slash=True))
        return json['domains']

    def create(self, name, ip):
        json = self.request(self.get_endpoint(), method='POST',
                            params={'name': name, 'ip_address': ip})
        return json['domain']

    def show(self, domain_id):
        json = self.request(self.get_endpoint([domain_id], trailing_slash=True))
        return json['domain']

    def destroy_domain(self, domain_id):
        self.request(self.get_endpoint([domain_id]), method='DELETE')
        # TODO
        return True

    def all_domain_records(self, domain_id):
        json = self.request('/domains/%s/records/' % domain_id)
        return json['domain_records']

    def new_domain_record(self, domain_id, record_type, data, name=None,
                          priority=None, port=None, weight=None):
        params = {'data': data}
        params['type'] = record_type

        if name:
            params['name'] = name
        if priority:
            params['priority'] = priority
        if port:
            params['port'] = port
        if weight:
            params['weight'] = weight

        json = self.request('/domains/%s/records/' % domain_id, params, method='POST')
        return json['domain_record']

    def show_domain_record(self, domain_id, record_id):
        json = self.request('/domains/%s/records/%s' % (domain_id, record_id))
        return json['domain_record']

    def edit_domain_record(self, domain_id, record_id, record_type, data,
                           name=None, priority=None, port=None, weight=None):
        # API v.2 allows only record name change
        params = {'name': name}
        json = self.request('/domains/%s/records/%s' % (domain_id, record_id), params, method='PUT')
        return json['domain_record']

    def destroy_domain_record(self, domain_id, record_id):
        self.request('/domains/%s/records/%s' % (domain_id, record_id), method='DELETE')
        return True
