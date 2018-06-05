from __future__ import (absolute_import, division, print_function)

from schema_transform.base_netconf_transform import SchemaTransformNetconfBase

class IosxrSchemaTransformNetconf(SchemaTransformNetconfBase):
    '''
    Function: openconfig_to_netconf
    Input: config in XML format (string)
    Output: IOSXR specific converted config (string)
    '''
    def openconfig_to_netconf(self, config, xpath_map=None):
        # No XR specific need transform required with tested model
        # of openconfig-interface and openconfig-bgp (ipv4-unicast)
        return (config)

