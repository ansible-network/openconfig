#!/usr/bin/python
#
# Copyright: Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = """
---
module: openconfig_config
version_added: "2.7"
author: "Deepak Agrawal (@dagrawal)"
short_description: Manage openconfig compatible devices
description:
  - This module program destination device with configurations
    (desired state) provided in a given schema format. It queries devices
    for given schema, validates confiigs and play them on device if there
    is any differeence between desired state and current state.
options:
    data:
      description: configurations in YAML Dict format.
      required: true
    schema:
      description: Schema that is used to form the confguations in data
                   option.
      required: true

version_added: "2.7"
notes:
  - This module support only netconf connection
"""

EXAMPLES = """
- name: Enable interface
  openconfig_config:
    data:
        interfaces:
            interface:
                -name: 'GigabitEthernet 0/0/0/0'
                 enabled: True
    schema:
       - openconfig-interfaces
"""

RETURN = """
"""
import re
import q
import sys
import os
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.network.common.netconf import NetconfConnection
from ansible.module_utils.network.netconf.netconf import dispatch
from ansible.module_utils._text import to_bytes
try:
    from ncclient.xml_ import to_xml
    HAS_NCCLIENT = True
except ImportError:
    HAS_NCCLIENT = False

try:
    from lxml import etree
    HAS_XML = True
except ImportError:
    HAS_XML = False

try:
    from lxml.etree import tostring
except ImportError:
    from xml.etree.ElementTree import tostring

try:
    import jxmlease
    HAS_JXMLEASE = True
except ImportError:
    HAS_JXMLEASE = False

_EDIT_OPS = frozenset(['merge', 'create', 'replace', 'delete'])

BASE_1_0 = "{urn:ietf:params:xml:ns:netconf:base:1.0}"

class Config(object):

    def __init__(self, module):
        self._module = module
        self._schema_cache = None
        self._config = None
        self._schema = {}
        self._data_model = None

    def get_all_schemas(self):
        content = '''
          <filter>
            <netconf-state xmlns="urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring">
              <schemas>
                <schema>
                    <identifier/>
                </schema>
              </schemas>
            </netconf-state>
          </filter>
        '''
        xml_request = '<%s>%s</%s>' %('get', content, 'get')
        response = dispatch(self._module, xml_request)
        res = tostring(response)
        if not HAS_JXMLEASE:
            module.fail_json(msg='jxmlease is required to store response in json format'
                                 'but does not appear to be installed. '
                                 'It can be installed using `pip install jxmlease`')
            return False

        res_json = jxmlease.parse(res)
        self._schema_cache = res_json["data"]["netconf-state"]["schemas"]["schema"]
        return True

    def get_schema(self, schema_key):
        if self._schema_cache == None:
            self.get_all_schemas()

        found = False
        # Search for schema in schema supported by device
        for index, schema_list in enumerate(self._schema_cache):
            q (index, to_bytes(schema_list["identifier"], errors='surrogate_or_strict'), schema_key)
            if to_bytes(schema_key) == to_bytes(schema_list["identifier"], errors='surrogate_or_strict'):
                self._schema["identifier"] = schema_key
                self._schema["namespace"] = self._schema_cache[index]["namespace"]
                self._schema["format"] = self._schema_cache[index]["format"]
                found = True
                break

        if found:
           content = ("<identifier> %s </identifier>" % (self._schema["identifier"]))
           xmlns = "urn:ietf:params:xml:ns:yang:ietf-netconf-monitoring"
           xml_request = '<%s xmlns="%s"> %s </%s>' %('get-schema',
                   xmlns, content, 'get-schema')
           response = dispatch(self._module, xml_request)
           res = tostring(response)
           res_json = jxmlease.parse(res)
           data_json = res_json["rpc-reply"]["data"]
           q(data_json)
        
        return found, data_json

class OpenConfig(object):
    def __init__(self, module, data, schema):
        self._module = module
        self._data = data
        self._schema = schema

    def create_config(self):
        config = Config(self._module)
        for schema in self._schema:
           found, data_model = config.get_schema(schema)
           if found:
             self._data_model = data_model
           else:
             #TODO raise exception
             self._data_model = None


def main():
    """main entry point for module execution
    """
    argument_spec = dict(
        data=dict(required=True, type='dict'),
        schema=dict(required=True, type='list'),
    )
    module = AnsibleModule(argument_spec=argument_spec,
                           supports_check_mode=True)

    p = module.params
    op = OpenConfig(module, p['data'], p['schema'])
    op.create_config()

    warnings = list()
    result = dict(changed=False, warnings=warnings)
    module.exit_json(**result)


if __name__ == '__main__':
    main()
