#
# OPGEE XML Package
#
# Clean XML parsing API for OPGEE core objects
# Part of XML/Core package separation refactoring
#
# Author: Refactoring Team
#
# Copyright (c) 2021-2022 The Board of Trustees of the Leland Stanford Junior University.
# See LICENSE.txt for license details.
#

# Main parsing functions - primary public API
from .parsers import (
    parse_stream,
    parse_field, 
    parse_process,
    parse_xml_attributes,
    find_child_elements
)

# Object construction functions for complex assembly
from .builders import (
    build_field_with_processes,
    build_process_hierarchy,
    build_stream_network,
    merge_attributes,
    apply_inheritance,
    extract_xml_attributes,
    parse_boolean_attr
)

# Attribute handling without AttributeMixin
from .adapters import (
    parse_attributes_from_xml,
    create_attribute_from_def,
    validate_attribute_constraints,
    extract_xml_element_attributes,
    parse_boolean_xml_attr,
    parse_optional_attr,
    Attribute,
    SimpleAttributeContainer
)

# Re-export existing XML utilities for compatibility
from .xml_utils import merge_elements, save_xml
from .XMLFile import XMLFile

# Re-export model file for main entry point
from .model_file import ModelFile

__all__ = [
    # Primary parsing API
    'parse_stream',
    'parse_field', 
    'parse_process',
    'parse_xml_attributes',
    'find_child_elements',
    
    # Object builders
    'build_field_with_processes',
    'build_process_hierarchy', 
    'build_stream_network',
    'merge_attributes',
    'apply_inheritance',
    'extract_xml_attributes',
    'parse_boolean_attr',
    
    # Attribute adapters
    'parse_attributes_from_xml',
    'create_attribute_from_def',
    'validate_attribute_constraints',
    'extract_xml_element_attributes',
    'parse_boolean_xml_attr',
    'parse_optional_attr',
    'Attribute',
    'SimpleAttributeContainer',
    
    # XML utilities
    'merge_elements',
    'save_xml',
    'XMLFile',
    'ModelFile',
]


# Convenience function for main use case
def parse_model_from_xml(xml_file_path: str):
    """
    Main convenience function to parse an entire OPGEE model from XML.
    
    This is the primary entry point for XML parsing in the new architecture.
    
    :param xml_file_path: Path to XML model file
    :return: Model object
    """
    # Import here to avoid circular dependencies
    from .model_file import ModelFile
    
    model_file = ModelFile(xml_file_path)
    return model_file.get_model()


# Add convenience function to __all__
__all__.append('parse_model_from_xml')