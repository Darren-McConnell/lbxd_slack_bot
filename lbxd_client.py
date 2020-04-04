import hashlib
import hmac
import requests
import time
import uuid

import pdb

BASE_URL = 'https://api.letterboxd.com/api/v0/'


class LbxdClient(object):
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret
        self.session = self._create_session()

    def _create_session(self):
        session = requests.Session()
        session.params.update({'apikey': self.key})
        session.headers.update({'Accept': 'application/json',
                                'Content-Type': 'application/json'})
        return session

    def request(self, method, path, params=None):
        url = requests.compat.urljoin(BASE_URL, path)
        return self.session.request(
                method=method, url=url, params=params,
                auth=Auth(self.key, self.secret))

    def get_member_activity(self, member_id, **params):
        path = f'member/{member_id}/activity'
        return self.request('GET', path, params=params)


class Auth(requests.auth.AuthBase):
    def __init__(self, key, secret):
        self.key = key
        self.secret = secret

    def __call__(self, request):
        pdb.set_trace()
        stamp = {'nonce': str(uuid.uuid4()), 'timestamp': int(time.time())}
        request.prepare_url(request.url, stamp)
        signature = self._get_signature(
                self.secret, request.method,
                request.url, getattr(request, 'body', None))
        request.prepare_url(request.url, {'signature': signature})
        request.headers['Authorization'] = (f'Signature {signature}')
        return request

    @staticmethod
    def _get_signature(secret, method, url, body):
        salted = f'{method}\u0000{url}\u0000{body if body else ""}'
        signature = hmac.new(
                key=secret.encode(),
                msg=salted.encode(),
                digestmod=hashlib.sha256)
        return signature.hexdigest()
