# vim: tabstop=4 shiftwidth=4 softtabstop=4

#   Copyright 2012 OpenStack LLC.
#
#   Licensed under the Apache License, Version 2.0 (the "License"); you may
#   not use this file except in compliance with the License. You may obtain
#   a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#   WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#   License for the specific language governing permissions and limitations
#   under the License.

import datetime
import json
import uuid

from lxml import etree
import webob

from cinder import context
from cinder import db
from cinder import test
from cinder.tests.api import fakes
from cinder import volume


def fake_volume_get(*args, **kwargs):
    return {
        'id': 'fake',
        'host': 'host001',
        'status': 'available',
        'size': 5,
        'availability_zone': 'somewhere',
        'created_at': datetime.datetime.now(),
        'attach_status': None,
        'display_name': 'anothervolume',
        'display_description': 'Just another volume!',
        'volume_type_id': None,
        'snapshot_id': None,
        'project_id': 'fake',
        'migration_status': None,
        '_name_id': 'fake2',
    }


def fake_volume_get_all(*args, **kwargs):
    return [fake_volume_get()]


def app():
    # no auth, just let environ['cinder.context'] pass through
    api = fakes.router.APIRouter()
    mapper = fakes.urlmap.URLMap()
    mapper['/v2'] = api
    return mapper


class VolumeHostAttributeTest(test.TestCase):

    def setUp(self):
        super(VolumeHostAttributeTest, self).setUp()
        self.stubs.Set(volume.API, 'get', fake_volume_get)
        self.stubs.Set(volume.API, 'get_all', fake_volume_get_all)
        self.stubs.Set(db, 'volume_get', fake_volume_get)

        self.UUID = uuid.uuid4()

    def test_get_volume_allowed(self):
        ctx = context.RequestContext('admin', 'fake', True)
        req = webob.Request.blank('/v2/fake/volumes/%s' % self.UUID)
        req.method = 'GET'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = json.loads(res.body)['volume']
        self.assertEqual(vol['os-vol-host-attr:host'], 'host001')

    def test_get_volume_unallowed(self):
        ctx = context.RequestContext('non-admin', 'fake', False)
        req = webob.Request.blank('/v2/fake/volumes/%s' % self.UUID)
        req.method = 'GET'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = json.loads(res.body)['volume']
        self.assertNotIn('os-vol-host-attr:host', vol)

    def test_list_detail_volumes_allowed(self):
        ctx = context.RequestContext('admin', 'fake', True)
        req = webob.Request.blank('/v2/fake/volumes/detail')
        req.method = 'GET'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = json.loads(res.body)['volumes']
        self.assertEqual(vol[0]['os-vol-host-attr:host'], 'host001')

    def test_list_detail_volumes_unallowed(self):
        ctx = context.RequestContext('non-admin', 'fake', False)
        req = webob.Request.blank('/v2/fake/volumes/detail')
        req.method = 'GET'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = json.loads(res.body)['volumes']
        self.assertNotIn('os-vol-host-attr:host', vol[0])

    def test_list_simple_volumes_no_host(self):
        ctx = context.RequestContext('admin', 'fake', True)
        req = webob.Request.blank('/v2/fake/volumes')
        req.method = 'GET'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = json.loads(res.body)['volumes']
        self.assertNotIn('os-vol-host-attr:host', vol[0])

    def test_get_volume_xml(self):
        ctx = context.RequestContext('admin', 'fake', True)
        req = webob.Request.blank('/v2/fake/volumes/%s' % self.UUID)
        req.method = 'GET'
        req.accept = 'application/xml'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = etree.XML(res.body)
        host_key = ('{http://docs.openstack.org/volume/ext/'
                    'volume_host_attribute/api/v1}host')
        self.assertEqual(vol.get(host_key), 'host001')

    def test_list_volumes_detail_xml(self):
        ctx = context.RequestContext('admin', 'fake', True)
        req = webob.Request.blank('/v2/fake/volumes/detail')
        req.method = 'GET'
        req.accept = 'application/xml'
        req.environ['cinder.context'] = ctx
        res = req.get_response(app())
        vol = list(etree.XML(res.body))[0]
        host_key = ('{http://docs.openstack.org/volume/ext/'
                    'volume_host_attribute/api/v1}host')
        self.assertEqual(vol.get(host_key), 'host001')
