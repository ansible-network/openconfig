#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Red Hat
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'network'}


DOCUMENTATION = '''
---
module: openconfigparser
short_description: Parses JSON openconfig based configs into xml which ansible
can play
description:
     Parses JSON openconfig based configs into xml which ansible can play
version_added: "2.5"
options:
  src:
    source file with openconfig in json. This file can have vars in jinja2 template
    required: true
  output:
    output will be file in xml format which can be used using netconf_*
    modules
    required: true
  ns_map:
    optional mapping of openconfig model tags with xml namespaces
    required: false
  xpath_map:
    optional mapping of openconfig model to desired model (e.g. device native
            xml )
    required: false
author:
  - Deepak Agrawal
'''

EXAMPLES = '''
- openconfig_parser:
    src: bgp.json
    output: bgp.xml
    xpath_map: templates/junos_open_to_native_map.yml
'''
