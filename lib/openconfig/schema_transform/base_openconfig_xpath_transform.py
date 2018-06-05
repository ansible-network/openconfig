import json
from collections import OrderedDict
import re

try:
    from lxml import etree, objectify
    HAS_XML = True
except ImportError:
    HAS_XML = False


def remove_namespaces(root):
    for node in root.iter():
        try:
           has_namespace = node.tag.startswith('{')
        except:
           continue
        if has_namespace:
           node.tag = node.tag.split('}', 1)[1]
    return root

def create_new_root(start_tag):
    return (etree.Element(start_tag))

def create_new_subtree(parent, tag_name, value=None, nsmap=None):
    sub_tree_element = etree.SubElement(parent, tag_name)
    if value:
        sub_tree_element.text = value
    return sub_tree_element

def find_parent(root, key_list):
    # Find longest prefix match for given xml hierarcy
    # Start search from end, end-1, end -2 ...
    keylen = len(key_list)
    if keylen == 1:
       # Hang this element from root
       return (root, 0)

    for i in reversed(range(keylen)):
        search_str = "/".join(key_list[0:i])
        search_key = './/'+search_str
        ele_found = root.find(search_key)
        if ele_found is not None:
           #print (ele_found.tag, i)
           return (ele_found, i)

    return (root)
           
def insert_node(root, key_list, value_list):
    # if there are multiple xmls tags are found in openconfig
    # we find parent only for first node and insert
    # all elements from same parent

    tokens = filter(None, key_list[0].split("/"))
    new_parent, index_found = find_parent(root, tokens)
    
    if not index_found:
       # hang from root
       create_new_subtree(root, tokens[0])
       return root
    
    index = 0
    for keys in key_list:
       new_sub_parent = new_parent
       for tok_index in range(index_found, len(tokens)):
           new_sub_parent = create_new_subtree(new_sub_parent, tokens[tok_index])
       if value_list:
          new_sub_parent.text = value_list[index]
       index = index+1

    return root

def transform(xml_src, xpath_map_data):
    root = etree.fromstring(xml_src)
    root = remove_namespaces(root)
    '''
    for node in root.iter():
       print node
    '''
    xpath_map_dict = xpath_map_data['xpath_map']
    pattern = re.compile("^[a-zA-Z0-9]+.*")

    for items in xpath_map_dict:
       for key in items:
          if key == 'config':
            # new root of the tree
            new_root = create_new_root(items[key])
            parent = new_root
          else:
            search_token  = './/'+key
            #print (search_token)
            new_key_list = []
            new_val_list = []
            for tag_find in root.findall(search_token):
                 #print(items[key])
                 new_key_list.append(items[key])
                 #print (tag_find.tag, tag_find.text, type(tag_find.text))
                 if pattern.match(tag_find.text):
                     #print ("leaf node")
                     new_val_list.append(tag_find.text)

            if new_key_list:
                insert_node(parent, new_key_list, new_val_list)
    
    return new_root

def base_openconfig_xpath_map_transform_fn(openconfig_xml, xpath_map_data):
    transformed_config_root = transform(openconfig_xml, xpath_map_data)
    transformed_config = etree.tostring(transformed_config_root,
            pretty_print=True)
    return transformed_config

# Driver code for standalone test
'''
def main():
    src = 'interface_openconfig.xml'
    with open(src, 'r') as f:
        xml_config = f.read()
        print ("type={}".format(type(xml_config)))
    xpath_map_file = 'junos_open_to_native_xpath_map.yml'
    with open(xpath_map_file, 'r') as f:
        xpath_map_data = yaml.load(f)

    new_root = transform(xml_config, xpath_map_data)
    transform_config = etree.tostring(new_root, pretty_print=True)
    print ("===============")
    print (transform_config)
'''
