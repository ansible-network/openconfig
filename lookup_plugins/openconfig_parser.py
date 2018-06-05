# (c) 2017, Ansible by Red Hat, inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.
#
from __future__ import absolute_import
__metaclass__ = type

DOCUMENTATION = '''
---
lookup: openconfig_parser
version_added: "2.5"
short_description: Parses config in json and convert it to xml config which can
be played using netconf to destination device.
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
import os
import re
import copy
import json
import collections
import yaml
import q

from ansible import constants as C
from ansible.plugins.action import ActionBase
from ansible.module_utils.network.common.utils import to_list
from ansible.module_utils.six import iteritems, string_types
from ansible.module_utils._text import to_bytes, to_text
from ansible.errors import AnsibleError, AnsibleUndefinedVariable, AnsibleFileNotFound
from ansible.module_utils.six.moves.urllib.parse import urlsplit
from collections import OrderedDict
from openconfig.schema_transform.base_netconf_transform  import SchemaTransformNetconfBase
from openconfig.schema_transform.iosxr_netconf_transform import IosxrSchemaTransformNetconf
from openconfig.schema_transform.junos_netconf_transform import JunosSchemaTransformNetconf
from openconfig.schema_transform.openconfig_nsmap_def import load_ns_map_from_module_args

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

def warning(msg):
    if C.ACTION_WARNINGS:
        display.warning(msg)

class LookupModule(LookupBase):

    def run(self, tmp=None, task_vars=None):
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        try:
           self._handle_template()
        except ValueError as exc:
           return dict(failed=True, msg=to_text(exc))

        try:
            src = self._task.args.get('src')
            output_file = self._task.args.get('output')
        except KeyError as exc:
            return {'failed': True, 'msg': 'missing required argument: %s' % exc}

        #Optional Arguments Handling
        try:
            xpath_map_data = self._handle_xpath_map()
        except ValueError as exc:
            return dict(failed=True, msg=to_text(exc))

        try:
            ns_map_data = self._handle_ns_map()
        except ValueError as exc:
            return dict(failed=True, msg=to_text(exc))

        self.facts = {}
        play_context = copy.deepcopy(self._play_context)
        play_context.network_os = self._get_network_os(task_vars)
        load_ns_map_from_module_args(ns_map_data)
        q("network_os=%s connection=%s \n" % (play_context.network_os, play_context.connection))

        # Load appropriate low level config generator bases on network_os
        # and connection type

        if play_context.connection == 'netconf':
           base_schematrans = SchemaTransformNetconfBase()
           config_xml_base = base_schematrans.openconfig_to_netconf(src, xpath_map_data)

        if play_context.network_os == 'iosxr':
           iosxr_schematrans = IosxrSchemaTransformNetconf()
           config_xml_final = iosxr_schematrans.openconfig_to_netconf(config_xml_base, xpath_map_data)

        if play_context.network_os == 'junos':
            junos_schematrans = JunosSchemaTransformNetconf()
            config_xml_final = junos_schematrans.openconfig_to_netconf(config_xml_base, xpath_map_data)

        with open(output_file, 'w') as f:
            f.write(config_xml_final)

        #self.ds.update(task_vars)
        result['ansible_facts'] = self.facts
        return config_xml_final

    def _get_working_path(self):
        cwd = self._loader.get_basedir()
        if self._task._role is not None:
            cwd = self._task._role._role_path
        return cwd

    def _handle_template(self):
        src = self._task.args.get('src')
        working_path = self._get_working_path()

        if os.path.isabs(src) or urlsplit('src').scheme:
            source = src
        else:
            source = self._loader.path_dwim_relative(working_path, 'templates', src)
            if not source:
                source = self._loader.path_dwim_relative(working_path, src)

        if not os.path.exists(source):
            raise ValueError('path specified in src not found')

        try:
            with open(source, 'r') as f:
                template_data = to_text(f.read())
        except IOError:
            return dict(failed=True, msg='unable to load src file')

        # Create a template search path in the following order:
        # [working_path, self_role_path, dependent_role_paths, dirname(source)]
        searchpath = [working_path]
        if self._task._role is not None:
            searchpath.append(self._task._role._role_path)
            if hasattr(self._task, "_block:"):
                dep_chain = self._task._block.get_dep_chain()
                if dep_chain is not None:
                    for role in dep_chain:
                        searchpath.append(role._role_path)
        searchpath.append(os.path.dirname(source))
        self._templar.environment.loader.searchpath = searchpath
        self._task.args['src'] = self._templar.template(template_data,
                convert_data=False)

    def _get_network_os(self, task_vars):
        if 'network_os' in self._task.args and self._task.args['network_os']:
            display.vvvv('Getting network OS from task argument')
            network_os = self._task.args['network_os']
        elif self._play_context.network_os:
            display.vvvv('Getting network OS from inventory')
            network_os = self._play_context.network_os
        elif 'network_os' in task_vars.get('ansible_facts', {}) and task_vars['ansible_facts']['network_os']:
            display.vvvv('Getting network OS from fact')
            network_os = task_vars['ansible_facts']['network_os']
        else:
            raise AnsibleError('ansible_network_os must be specified on this host to use platform agnostic modules')

        return network_os

    def _handle_xpath_map(self):
        try:
            xpath_map_src = self._task.args.get('xpath_map')
        except Exception as exc:
            display.vvvv('No xpath_map is specified')
            return dict(failed=False, msg="No xpath map is specified")

        if xpath_map_src == None:
            return

        working_path = self._get_working_path()

        if os.path.isabs(xpath_map_src) or urlsplit('xpath_map_src').scheme:
            xpath_map_file = xpath_map_src
        else:
            xpath_map_file = self._loader.path_dwim_relative(working_path, 'templates', xpath_map_src)
            if not xpath_map_file:
                xpath_map_file = self._loader.path_dwim_relative(working_path, xpath_map_src)

        if not os.path.exists(xpath_map_file):
            raise ValueError('path specified in xpath_map not found')

        try:
            with open(xpath_map_file, 'r') as f:
                xpath_map_data = yaml.load(f)
                q(xpath_map_data)
                return (xpath_map_data)
        except IOError:
            return dict(failed=True, msg='unable to load xpath_map file')

    def _handle_ns_map(self):
        try:
            ns_map_src = self._task.args.get('ns_map')
        except Exception as exc:
            display.vvvv('No ns_map is specified')
            return dict(failed=False, msg="No ns map is specified")

        if ns_map_src == None:
            return

        working_path = self._get_working_path()

        if os.path.isabs(ns_map_src) or urlsplit('ns_map_src').scheme:
            ns_map_file = ns_map_src
        else:
            ns_map_file = self._loader.path_dwim_relative(working_path,
                    'templates', ns_map_src)
            if not ns_map_file:
                ns_map_file = self._loader.path_dwim_relative(working_path, ns_map_src)

        if not os.path.exists(ns_map_file):
            raise ValueError('path specified in ns_map not found')

        try:
            with open(ns_map_file, 'r') as f:
                ns_map_data = yaml.load(f)
                q(ns_map_data)
                return (ns_map_data)
        except IOError:
            return dict(failed=True, msg='unable to load ns_map file')

