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
module: net_openconfig
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
  net_openconfig:
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
from ansible.module_utils.basic import AnsibleModule
from lib.net_openconfig.openconfig import get_schema

class OpenConfig(object):
    def __init__(self, module, data, schema):
        self._module = module
        self._data = data
        self._schema = schema

    def create_config(self):
        for key, value in self._data.items():
            schema = get_schema(self._module, key)
        q(self._data, self._schema)


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
