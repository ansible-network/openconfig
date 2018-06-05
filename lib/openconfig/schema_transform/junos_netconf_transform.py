from __future__ import (absolute_import, division, print_function)

from schema_transform.base_netconf_transform import SchemaTransformNetconfBase

try:
    from lxml import etree
    HAS_XML = True
except ImportError:
    HAS_XML = False

class JunosSchemaTransformNetconf(SchemaTransformNetconfBase):

    '''
    Function: openconfig_to_netconf
    Input: config in XML format (string)
    Output: Junos specific converted config (string)
    '''
    def openconfig_to_netconf(self, config, xpath_map=None):
        # Not able to test openconfig model with Junos
        ipv4_handled_config = self._handle_junos_native_ipv4_address(config)
        final_rooted_config = self._add_junos_root_config_tag(ipv4_handled_config)
  
        return (final_rooted_config)

    '''
    Junos needs ipv4 address of interface in <addr>/<mask> format
    Openconfig has tag - 
         address - subinterface/index/ipv4/address/config/ip
         mask    - subinterface/index/ipv4/address/config/prefix-length
    we already converted these tags via xpath_map to
         address - unit/family/address/inet/name
         mask    - unit/family/address/inet/mask
    This function will integrate addr and prefix to one and will remove
    extra mask tags to be compatibe with junos native xml schema
    '''
    def _handle_junos_native_ipv4_address(self, xml_config):
        root = etree.fromstring(xml_config)
        search_addr_tag = './/'+'unit/family/inet/address/name'
        search_mask_tag = './/'+'unit/family/inet/address/mask'
        ipv4_addr_elem = []
        ipv4_mask_elem = []
        for ipv4_addr_tag in root.findall(search_addr_tag):
            ipv4_addr_elem.append(ipv4_addr_tag)
    
        for ipv4_mask_tag in root.findall(search_mask_tag):
            ipv4_mask_elem.append(ipv4_mask_tag)
    
        for i in range(len(ipv4_addr_elem)):
            ipv4_addr_elem[i].text = ipv4_addr_elem[i].text+'/'+ipv4_mask_elem[i].text
            ipv4_mask_elem[i].getparent().remove(ipv4_mask_elem[i])

        return etree.tostring(root, pretty_print=True)

    def _add_junos_root_config_tag(self, xml_config):
        root = etree.Element('config')
        subroot = etree.fromstring(xml_config)
        
        root.insert(0, subroot)
        return etree.tostring(root, pretty_print=True)

