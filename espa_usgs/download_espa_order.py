#!/usr/bin/env python

"""
Purpose: A simple python client that will download all available (completed) scenes for
         a user order(s).

Requires: Standard Python installation.

Version: 1.0

Changes:

20 June 2017: Woodstonelee added option to download checksum and error handling on bad urls
30 June 2016: Guy Serbin added support for Python 3.x and download progress indicators.
24 August 2016: Guy Serbin added:
1. The downloads will now tell you which file number of all available scenes is being downloaded.
2. Added a try/except clause for cases where the remote server closes the connection during a download.
23 September 2016: Converted to using the ESPA API proper rather than relying on the RSS feed

"""
import argparse
import base64
import os
import random
import shutil
import sys
import time
import json
import hashlib
from getpass import getpass

if sys.version_info[0] == 3:
    import urllib.request as ul
else:
    import urllib2 as ul


class Api(object):
    def __init__(self, username, password, host):
        self.host = host
        self.username = username
        self.password = password

    def api_request(self, endpoint, data=None):
        """
        Simple method to handle calls to a REST API that uses JSON

        args:
            endpoint - API endpoint URL
            data - Python dictionary to send as JSON to the API

        returns:
            Python dictionary representation of the API response
        """
        if data:
            data = json.dumps(data)

        if sys.version_info[0] == 3:
            request = ul.Request(self.host + endpoint, data=data.encode(),
                                 method='GET')
        else:
            request = ul.Request(self.host + endpoint, data=data)
            request.get_method = lambda: 'GET'

        instr = '{}:{}'.format(self.username, self.password).encode()
        base64string = base64.encodestring(instr).strip().decode()
        request.add_header("Authorization", "Basic {}".format(base64string))

        try:
            result = ul.urlopen(request)
        except ul.HTTPError as e:
            result = e

        resp = json.loads(result.read().decode())
        if isinstance(resp, dict):
            messages = resp.pop('messages', dict())
            if messages.get('errors'):
                raise Exception('{}'.format(messages.get('errors')))
            if messages.get('warnings'):
                print('WARNINGS: {}'.format(messages.get('warnings')))

        return resp

    def get_completed_scenes(self, orderid):
        filters = {'status': 'complete'}
        resp = self.api_request('/api/v1/item-status/{0}'.format(orderid),
                                data=filters)
        if orderid not in resp:
            raise Exception('Order ID {} not found'.format(orderid))
        urls = [_.get('product_dload_url') for _ in resp[orderid]]
        return urls

    def retrieve_all_orders(self, email):
        filters = {'status': 'complete'}
        all_orders = self.api_request('/api/v1/list-orders/{0}'.format(email or ''),
                                      data=filters)

        return all_orders

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


class Scene(object):

    def __init__(self, srcurl):
        self.srcurl = srcurl

        parts = self.srcurl.split("/")
        self.orderid = parts[4]
        self.filename = parts[-1]
        self.name = self.filename.split('.tar.gz')[0]

    def checksum(self):
        self.srcurl = str(self.srcurl).replace('.tar.gz', '.md5')
        self.filename = self.filename.replace('.tar.gz', '.md5')
        self.name = '%s MD5 checksum' % self.name
        return self


class LocalStorage(object):

    def __init__(self, basedir, verbose=False):
        self.basedir = basedir
        self.verbose = verbose

    def directory_path(self, scene):
        path = ''.join([self.basedir, os.sep, scene.orderid, os.sep])
        if not os.path.exists(path):
            os.makedirs(path)
            if self.verbose:
                print ("Created target_directory: %s " % path)
        return path

    def scene_path(self, scene):
        return ''.join([self.directory_path(scene), scene.filename])

    def tmp_scene_path(self, scene):
        return ''.join([self.directory_path(scene), scene.filename, '.part'])

    def is_stored(self, scene):
        return os.path.exists(self.scene_path(scene))

    def store(self, scene, checksum=False):
        if self.is_stored(scene):
            if self.verbose:
                print('Scene already exists on disk, skipping.')
            return

        download_directory = self.directory_path(scene)
        package_path = self._download(scene, download_directory)
        if checksum:
            checksum_path = self._download(scene.checksum(), download_directory)
            self._compare_checksum(package_path, checksum_path)

    def _download_bytes(self, first_byte, scene):
        req = ul.Request(scene.srcurl)
        req.headers['Range'] = 'bytes={}-'.format(first_byte)

        with open(self.tmp_scene_path(scene), 'ab') as target:
            source = ul.urlopen(req)
            shutil.copyfileobj(source, target)

        return os.path.getsize(self.tmp_scene_path(scene))

    def _download(self, scene, target):
        req = ul.Request(scene.srcurl)
        req.get_method = lambda: 'HEAD'

        try:
            head = ul.urlopen(req)
        except ul.HTTPError:
            print('Scene not reachable at {0:s}'.format(req.get_full_url()))
            return

        file_size = int(head.headers['Content-Length'])

        first_byte = 0
        if os.path.exists(self.tmp_scene_path(scene)):
            first_byte = os.path.getsize(self.tmp_scene_path(scene))

        if self.verbose:
            print ("Downloading %s, to: %s" % (scene.name, target))

        while first_byte < file_size:
            # Added try/except to keep the script from crashing if the remote host closes the connection.
            # Instead, it moves on to the next file.
            try:
                first_byte = self._download_bytes(first_byte, scene)
                time.sleep(random.randint(5, 30))
            except Exception as e:
                print(str(e))
                break

        if first_byte >= file_size:
            os.rename(self.tmp_scene_path(scene), self.scene_path(scene))
        return self.scene_path(scene)

    def _compare_checksum(self, filepath, checksum_path):
        remote_md5hash = open(checksum_path, 'r').read().split()[0].strip()
        local_md5hash = hashlib.md5(open(filepath, 'rb').read()).hexdigest()
        if local_md5hash != remote_md5hash:
            if self.verbose:
                print('Remote: %s Local: %s' % (remote_md5hash, local_md5hash))
            print('WARNING: Failed checksum verification: %s' % os.path.basename(filepath))
        else:
            if self.verbose:
                print('Checksum %s matches' % local_md5hash)


def main(username, email, order, target_directory, password=None, host=None, verbose=False, checksum=False):
    if not password:
        password = getpass('Password: ')
    if not host:
        host = 'https://espa.cr.usgs.gov'

    storage = LocalStorage(target_directory, verbose=verbose)

    with Api(username, password, host) as api:
        if order == 'ALL':
            orders = api.retrieve_all_orders(email)
        else:
            orders = [order]

        if verbose:
            print('Retrieving orders: {0}'.format(orders))

        for o in orders:
            scenes = api.get_completed_scenes(o)
            if len(scenes) < 1:
                print('No scenes in "completed" state for order {}'.format(o))

            for s in range(len(scenes)):
                print('File {0} of {1} for order: {2}'.format(s + 1, len(scenes), o))

                scene = Scene(scenes[s])
                storage.store(scene, checksum)


if __name__ == '__main__':
    epilog = ('ESPA Bulk Download Client Version 1.0.0. [Tested with Python 2.7]\n'
              'Retrieves all completed scenes for the user/order\n'
              'and places them into the target directory.\n'
              'Scenes are organized by order.\n\n'
              'It is safe to cancel and restart the client, as it will\n'
              'only download scenes one time (per directory)\n'
              ' \n'
              '*** Important ***\n'
              'If you intend to automate execution of this script,\n'
              'please take care to ensure only 1 instance runs at a time.\n'
              'Also please do not schedule execution more frequently than\n'
              'once per hour.\n'
              ' \n'
              '------------\n'
              'Examples:\n'
              '------------\n'
              'Linux/Mac: ./download_espa_order.py -e your_email@server.com -o ALL -d /some/directory/with/free/space\n\n'
              'Windows:   C:\python27\python download_espa_order.py -e your_email@server.com -o ALL -d C:\some\directory\with\\free\space'
              '\n ')

    parser = argparse.ArgumentParser(epilog=epilog, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument("-e", "--email",
                        required=False,
                        help="email address for the user that submitted the order)")

    parser.add_argument("-o", "--order",
                        required=False, default='ALL',
                        help="which order to download (use ALL for every order)")

    parser.add_argument("-d", "--target_directory",
                        required=True,
                        help="where to store the downloaded scenes")

    parser.add_argument("-u", "--username",
                        required=True,
                        help="EE/ESPA account username")

    parser.add_argument("-p", "--password",
                        required=False,
                        help="EE/ESPA account password")

    parser.add_argument("-v", "--verbose",
                        required=False,
                        action='store_true',
                        help="be vocal about process")

    parser.add_argument("-i", "--host",
                        required=False)

    parser.add_argument("-c", '--checksum',
                        required=False,
                        action='store_true',
                        help="download additional MD5 checksum files (will warn if binaries do not match)")

    parsed_args = parser.parse_args()

    try:
        main(**vars(parsed_args))
    except BaseException as error:
        print('ERROR: {}'.format(str(error)))

