from __future__ import (absolute_import, division, print_function)

import json
from schema_transform.openconfig_nsmap_def import OPENCONFIG_NS_MAP 
from collections import OrderedDict
from schema_transform.base_openconfig_xpath_transform import base_openconfig_xpath_map_transform_fn
import q

try:
    from lxml import etree
    HAS_XML = True
except ImportError:
    HAS_XML = False

class SchemaTransformNetconfBase(object):

    '''
    Base Class for all common conversion for supported connection type
    All platform independent code should reside in base class
    '''

    '''
    Converts openconfig to XML which netconf can understand
    config should be passed as raw string (python 3 ?)
    '''
    def openconfig_to_netconf(self, config, xpath_map_data=None):
        json_py_obj = json.loads(config, object_pairs_hook=OrderedDict)
        root = etree.Element("config")
        config_xml = self._json_to_xml(json_py_obj, root)
        config_xml_str = etree.tostring(root, pretty_print=True)
        if xpath_map_data is not None:
            return base_openconfig_xpath_map_transform_fn(config_xml_str, xpath_map_data)
        else:
            return config_xml_str

    def _json_to_xml(self, json_obj, root):
        json_obj_type = type(json_obj)

        if json_obj_type is list:
            for sub_elem in json_obj:
                self._json_to_xml(sub_elem, root)

        # if json_obj_type is dict:
        if (json_obj_type is OrderedDict) or (json_obj_type is dict):
            for tag_name in json_obj:
                sub_obj = json_obj[tag_name]

                if OPENCONFIG_NS_MAP.has_key(tag_name):
                    container_ele = etree.SubElement(root, tag_name,
                        nsmap=OPENCONFIG_NS_MAP[tag_name])
                else:
                    container_ele = etree.SubElement(root, tag_name)

                if (type(sub_obj) is int) or (type(sub_obj) is str) or \
                   (type(sub_obj) is unicode):
                    ns_tag = container_ele.nsmap
                    for keys in ns_tag:
                        if keys is not None:
                            prefix = keys
                            q(ns_tag)
                        else:
                            prefix = None
                    if prefix is not None:
                       container_ele.text = prefix+":"+str(sub_obj)
                    else:
                       container_ele.text = str(sub_obj)

                else:
                    self._json_to_xml(sub_obj, container_ele)


