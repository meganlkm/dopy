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

API_ENDPOINT = 'https://api.digitalocean.com/v1'


class DoError(RuntimeError):
    pass


class DoManager(object):

    def __init__(self, client_id, api_key, api_version=1):
        self.api_endpoint = API_ENDPOINT
        self.client_id = client_id
        self.api_key = api_key
        self.api_version = int(api_version)

    def all_active_droplets(self):
        json = self.request('/droplets/')
        return json['droplets']

    def new_droplet(self, name, size_id, image_id, region_id,
                    ssh_key_ids=None, virtio=True, private_networking=False,
                    backups_enabled=False, user_data=None, ipv6=False):
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

        json = self.request('/droplets/new', params=params)
        return json['droplet']

    def show_droplet(self, droplet_id):
        json = self.request('/droplets/%s' % droplet_id)
        return json['droplet']

    def reboot_droplet(self, droplet_id):
        json = self.request('/droplets/%s/reboot/' % droplet_id)
        json.pop('status', None)
        return json

    def power_cycle_droplet(self, droplet_id):
        json = self.request('/droplets/%s/power_cycle/' % droplet_id)
        json.pop('status', None)
        return json

    def shutdown_droplet(self, droplet_id):
        json = self.request('/droplets/%s/shutdown/' % droplet_id)
        json.pop('status', None)
        return json

    def power_off_droplet(self, droplet_id):
        json = self.request('/droplets/%s/power_off/' % droplet_id)
        json.pop('status', None)
        return json

    def power_on_droplet(self, droplet_id):
        json = self.request('/droplets/%s/power_on/' % droplet_id)
        json.pop('status', None)
        return json

    def password_reset_droplet(self, droplet_id):
        json = self.request('/droplets/%s/password_reset/' % droplet_id)
        json.pop('status', None)
        return json

    def resize_droplet(self, droplet_id, size_id):
        params = {'size_id': size_id}
        json = self.request('/droplets/%s/resize/' % droplet_id, params)
        json.pop('status', None)
        return json

    def snapshot_droplet(self, droplet_id, name):
        params = {'name': name}
        json = self.request('/droplets/%s/snapshot/' % droplet_id, params)
        json.pop('status', None)
        return json

    def restore_droplet(self, droplet_id, image_id):
        params = {'image_id': image_id}
        json = self.request('/droplets/%s/restore/' % droplet_id, params)
        json.pop('status', None)
        return json

    def rebuild_droplet(self, droplet_id, image_id):
        params = {'image_id': image_id}
        json = self.request('/droplets/%s/rebuild/' % droplet_id, params)
        json.pop('status', None)
        return json

    def enable_backups_droplet(self, droplet_id):
        json = self.request('/droplets/%s/enable_backups/' % droplet_id)
        json.pop('status', None)
        return json

    def disable_backups_droplet(self, droplet_id):
        json = self.request('/droplets/%s/disable_backups/' % droplet_id)
        json.pop('status', None)
        return json

    def rename_droplet(self, droplet_id, name):
        params = {'name': name}
        json = self.request('/droplets/%s/rename/' % droplet_id, params)
        json.pop('status', None)
        return json

    def destroy_droplet(self, droplet_id, scrub_data=True):
        params = {'scrub_data': '1' if scrub_data else '0'}
        json = self.request('/droplets/%s/destroy/' % droplet_id, params)
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
        params = {'filter': 'my_images'}
        json = self.request('/images/', params)
        return json['images']

    def show_image(self, image_id):
        params = {'image_id': image_id}
        json = self.request('/images/%s' % image_id)
        return json['image']

    def destroy_image(self, image_id):
        self.request('/images/%s/destroy' % image_id)
        return True

    def transfer_image(self, image_id, region_id):
        params = {'region_id': region_id}
        json = self.request('/images/%s/transfer' % image_id, params)
        json.pop('status', None)
        return json

    # ssh_keys=========================================
    def all_ssh_keys(self):
        json = self.request('/ssh_keys/')
        return json['ssh_keys']

    def new_ssh_key(self, name, pub_key):
        params = {'name': name, 'ssh_pub_key': pub_key}
        json = self.request('/ssh_keys/new/', params)
        return json['ssh_key']

    def show_ssh_key(self, key_id):
        json = self.request('/ssh_keys/%s/' % key_id)
        return json['ssh_key']

    def edit_ssh_key(self, key_id, name, pub_key):
        params = {'name': name, 'ssh_pub_key': pub_key}  # the doc needs to be improved
        json = self.request('/ssh_keys/%s/edit/' % key_id, params)
        return json['ssh_key']

    def destroy_ssh_key(self, key_id):
        self.request('/ssh_keys/%s/destroy/' % key_id)
        return True

    # sizes============================================
    def sizes(self):
        json = self.request('/sizes/')
        return json['sizes']

    # domains==========================================
    def all_domains(self):
        json = self.request('/domains/')
        return json['domains']

    def new_domain(self, name, ip):
        params = {'name': name, 'ip_address': ip}
        json = self.request('/domains/new/', params)
        return json['domain']

    def show_domain(self, domain_id):
        json = self.request('/domains/%s/' % domain_id)
        return json['domain']

    def destroy_domain(self, domain_id):
        self.request('/domains/%s/destroy/' % domain_id)
        return True

    def all_domain_records(self, domain_id):
        json = self.request('/domains/%s/records/' % domain_id)
        return json['records']

    def new_domain_record(self, domain_id, record_type, data, name=None,
                          priority=None, port=None, weight=None):
        params = {'data': data}
        params['record_type'] = record_type

        if name:
            params['name'] = name
        if priority:
            params['priority'] = priority
        if port:
            params['port'] = port
        if weight:
            params['weight'] = weight

        json = self.request('/domains/%s/records/new/' % domain_id, params)
        return json['record']

    def show_domain_record(self, domain_id, record_id):
        json = self.request('/domains/%s/records/%s' % (domain_id, record_id))
        return json['record']

    def edit_domain_record(self, domain_id, record_id, record_type, data,
                           name=None, priority=None, port=None, weight=None):
        params = {
            'record_type': record_type,
            'data': data,
        }

        if name:
            params['name'] = name
        if priority:
            params['priority'] = priority
        if port:
            params['port'] = port
        if weight:
            params['weight'] = weight
        json = self.request('/domains/%s/records/%s/edit/' % (domain_id, record_id), params)
        return json['record']

    def destroy_domain_record(self, domain_id, record_id):
        self.request('/domains/%s/records/%s/destroy/' % (domain_id, record_id))
        return True

    # events(actions in v2 API)========================
    def show_all_actions(self):
        # API v.1 haven't this functionality
        return False

    def show_action(self, action_id):
        return self.show_event(action_id)

    def show_event(self, event_id):
        json = self.request('/events/%s' % event_id)
        return json['event']

    # low_level========================================
    def request(self, path, params={}, method='GET'):
        if not path.startswith('/'):
            path = '/' + path
        url = self.api_endpoint + path

        params['client_id'] = self.client_id
        params['api_key'] = self.api_key
        resp = self.request_v1(url, params, method=method)
        return resp

    def request_v1(self, url, params={}, method='GET'):
        try:
            resp = requests.get(url, params=params, timeout=60)
            json = resp.json()
        except ValueError:  # requests.models.json.JSONDecodeError
            raise ValueError("The API server doesn't respond with a valid json")
        except requests.RequestException as e:  # errors from requests
            raise RuntimeError(e)

        if resp.status_code != requests.codes.ok:
            if json:
                if 'error_message' in json:
                    raise DoError(json['error_message'])
                elif 'message' in json:
                    raise DoError(json['message'])
            # The JSON reponse is bad, so raise an exception with the HTTP status
            resp.raise_for_status()
        if json.get('status') != 'OK':
            raise DoError(json['error_message'])

        return json


if __name__ == '__main__':
    client_id = os.environ['DO_CLIENT_ID']
    api_key = os.environ['DO_API_KEY']
    do = DoManager(client_id, api_key, 1)

    fname = sys.argv[1]

    # size_id: 66, image_id: 1601, region_id: 1
    pprint.pprint(getattr(do, fname)(*sys.argv[2:]))
