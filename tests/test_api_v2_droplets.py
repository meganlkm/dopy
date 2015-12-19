from unittest import TestCase
from dopy.api.v2 import DoApiDroplets


class DoApiDropletsTest(TestCase):

    def test_get_endpoint(self):
        """test_api_v2_droplets.DoApiDropletsTest.test_get_endpoint"""
        api = DoApiDroplets()
        self.assertEqual('/droplets', api.get_endpoint())
        self.assertEqual('/droplets/', api.get_endpoint(trailing_slash=True))
        self.assertEqual('/droplets/one/two/three', api.get_endpoint(['one', 'two', 'three']))
        self.assertEqual('/droplets/one/', api.get_endpoint(['one'], trailing_slash=True))
