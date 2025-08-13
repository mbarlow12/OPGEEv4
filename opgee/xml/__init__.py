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


__all__ = [
    # Attribute adapters
    'parse_attributes_from_xml',
    'create_attribute_from_def',
    'validate_attribute_constraints',
    'extract_xml_element_attributes',
    'parse_boolean_xml_attr',
    'parse_optional_attr',
    'Attribute',
    'SimpleAttributeContainer',
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
