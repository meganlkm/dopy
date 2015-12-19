from unittest import TestCase
from dopy.api.v2 import DoApiDomains


class DoApiDomainsTest(TestCase):

    def test_get_endpoint(self):
        """test_api_v2_domains.DoApiDomainsTest.test_get_endpoint"""
        api = DoApiDomains()
        self.assertEqual('/domains', api.get_endpoint())
        self.assertEqual('/domains/', api.get_endpoint(trailing_slash=True))
        self.assertEqual('/domains/one/two/three', api.get_endpoint(['one', 'two', 'three']))
        self.assertEqual('/domains/one/', api.get_endpoint(['one'], trailing_slash=True))
