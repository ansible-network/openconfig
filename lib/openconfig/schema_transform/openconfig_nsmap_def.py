OPENCONFIG_NS_MAP = {}

def load_ns_map_from_module_args(ns_map_data):
    ns_map_dict_list = ns_map_data['openconfig_ns_map']
    for items in ns_map_dict_list:
        for key in items:
            for (ns_map_key, ns_map_val) in items[key].items():
               if ns_map_key == 'None':
                  new_ns_map = {None: ns_map_val}
                  OPENCONFIG_NS_MAP[key] = new_ns_map
               else:
                  OPENCONFIG_NS_MAP[key] = items[key]


