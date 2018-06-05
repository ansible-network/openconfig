# Problem Statement

There is a requirement of a ventor agnostic data-model for configuration and operational data for controlling networking devices. All network configurations should be able to modelled in this language and should be communicated to destination device either in chosen native data-model or a tranform function should be provided to convert to defined data-model of vendor device.

# Solution Approach
- openconfig data-model is selected as vendor-neutral data-model to express network configurations
- Few vendors understand openconfig data-model as it is so no transformation is required to control these devices
- For vendors who do not talk in openconfig, a tranformation path is provided

# Example usage
- Define your configs in openconfig model in a file and keep it in valid path as any other ansible template file
- This openconfig template file supports jinja2 directives so you can define variable which can be declared per
  host or group as per requirements
- use new module provided as part of this role 'openconfig_parser' to parse the configs in openconfig or native
  vendor model. 
- Conversion schema from openconfig to vendor native format should be provided by argument 'xpath_map' to above role
- use 'netconf_config' module to play configs produced to destination device

# new module

module: openconfig_parser                                                                                                                  
description: Parses JSON openconfig based configs into openconfig xml or native OS format                                                                                                                                    
version_added: "2.5"                                                                                                                        
options:                                                                                                                                    
   - src:                                                                                                                                      
       source file with openconfig in json. This file can have vars in jinja2 template                                                         
       required: true                                                                                                                          
   - output:                                                                                                                                   
       output will be file in xml format which can be used using netconf_* modules                                                                                                                                 
       required: true                                                                                                                          
   - xpath_map:                                                                                                                                
       optional mapping of openconfig model to desired model (e.g. device native xml )                                                                                                                           
       required: false                                                                                                                         
                                                                                                                                     
EXAMPLES = '''                                                                                                                              
- openconfig_parser:                                                                                                                       
    src: bgp.json                                                                                                                           
    output: bgp.xml                                                                                                                         
    xpath_map: templates/junos_open_to_native_map.yml  
    
 ## open-config model tested
 
 Following models are tested. Not all options are tested for each model. selective options tested can be found at below location
  - Interface - templates/interface_openconfig.json
  - Bgp - templates/bgp_edit_config.json 
 
 ### Network OS tested (native openconfig model)
 Above models are tested against below platform when data is passed in native openconfig model
 
 - IOS-XR version 6.1.2
 
 ### Network OS tested (openconfig to os native transform)
 
 Above models are tested against below platforms where openconfig model is converted to OS native data model
 - Junos version version 17.3R1.10
 
 # Adding new openconfig model
 
 ## openconfig native
 
 If your platform supports openconfig data model and model you want to test is fully complaint with destination, only thing you will need to do is to add xml namespaces for your model at below location
 
- schema_transform/openconfig_nsmap_def.py 

## vendor specific model
 - first you need to define xpath_map which will have mapping for openconfig tags to vendor specific tags at below location
   and pass it as argument to openconfig_parser module.
   Sample mappings are written in .yml file syntax format e.g. template/junos_open_to_native_xpath_map.yml
   
 - There might be some code required to do schema conversion. e.g. junos needs interface ip in format <ip-address>/<mask>
   but there are separate tags for <ip-address> and <mask> name or hierarchy of tags can be changed via xpath_map but data
  conversion can be done by code only.
   Sample code at schema_transform/junos_netconf_transform.py
  
  
  # open issues
  - xpath_map does not output correct configs when there are multiple sections with same tags e.g. multiple subinterfaces under same interface
 
