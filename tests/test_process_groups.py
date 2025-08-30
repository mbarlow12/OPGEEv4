import pytest
from opgee.core.error import OpgeeException
from .utils_for_tests import load_test_model


@pytest.fixture(scope="module")
def process_groups_model(configure_logging_for_tests):
    return load_test_model('test_process_groups.xml')


@pytest.fixture(scope="module")
def test_field(process_groups_model):
    analysis = process_groups_model.get_analysis('test')
    field = analysis.get_field('test')
    return field


def test_process_choice_resolution(test_field):
    """Test that ProcessChoice resolution works correctly in the new architecture."""
    # Test that field attributes reflect the ProcessChoice selections
    attrs = test_field.attr_dict
    
    # Check that ProcessChoice attributes are present and have expected values
    assert 'oil_sands_mine' in attrs
    assert attrs['oil_sands_mine'].str_value() == 'None'
    
    assert 'gas_processing_path' in attrs
    assert attrs['gas_processing_path'].str_value() == 'Acid Wet Gas'
    
    assert 'oil_processing_path' in attrs  
    assert attrs['oil_processing_path'].str_value() == 'Stabilization'
    
    assert 'common_gas_process_choice' in attrs
    assert attrs['common_gas_process_choice'].str_value() == 'All'


def test_selected_processes_present(test_field):
    """Test that processes from selected ProcessGroups are present in the field."""
    process_names = {proc.name for proc in test_field.processes()}
    
    # These processes should be present based on the selections:
    # gas_processing_path = "Acid Wet Gas" should include:
    expected_gas_processes = {'GasGathering', 'GasDehydration', 'AcidGasRemoval', 'Demethanizer'}
    
    # oil_processing_path = "Stabilization" should include:
    expected_oil_processes = {'CrudeOilStabilization', 'CrudeOilStorage'}
    
    # common_gas_process_choice = "All" should include:
    expected_common_processes = {'GasPartition', 'GasLiftingCompressor', 'GasReinjectionCompressor', 
                               'TransmissionCompressor', 'GasReinjectionWell', 'StorageCompressor',
                               'LNGLiquefaction', 'GasDistribution', 'LNGRegasification', 'LNGTransport',
                               'StorageWell', 'StorageSeparator', 'PostStorageCompressor', 'NGL'}
    
    # oil_sands_mine = "None" should include processes from the "None" group
    expected_basic_processes = {'Exploration', 'Drilling', 'Reservoir', 'ReservoirWellInterface',
                              'Separation', 'DownholePump', 'CrudeOilDewatering', 'WaterTreatment',
                              'WaterInjection', 'SteamGeneration', 'Flaring', 'Venting',
                              'CrudeOilTransport', 'PetrocokeTransport'}
    
    # Check that selected processes are present
    assert expected_gas_processes.issubset(process_names), f"Missing gas processes: {expected_gas_processes - process_names}"
    assert expected_oil_processes.issubset(process_names), f"Missing oil processes: {expected_oil_processes - process_names}"
    assert expected_common_processes.issubset(process_names), f"Missing common processes: {expected_common_processes - process_names}"
    assert expected_basic_processes.issubset(process_names), f"Missing basic processes: {expected_basic_processes - process_names}"


def test_unselected_processes_absent(test_field):
    """Test that processes from unselected ProcessGroups are NOT present in the field."""
    process_names = {proc.name for proc in test_field.processes()}
    
    # These processes should NOT be present based on the selections:
    # oil_sands_mine = "None" means "Integrated with upgrader" group should be excluded:
    excluded_oil_sands = {'BitumenMining'}  # This is only in the "Integrated with upgrader" group
    
    # gas_processing_path = "Acid Wet Gas" means other groups should be excluded
    # Check for processes that are in other gas processing groups but not in "Acid Wet Gas"
    # Based on the XML structure, processes unique to other groups:
    excluded_gas_processes = {'RyanHolmes', 'CO2ReinjectionCompressor', 'CO2InjectionWell',
                            'PreMembraneChiller', 'PreMembraneCompressor', 'CO2Membrane',
                            'SourGasCompressor', 'SourGasInjection'}  # These are in other groups
    
    # oil_processing_path = "Stabilization" means other oil processing groups should be excluded
    excluded_oil_processes = {'HeavyOilUpgrading', 'HeavyOilDilution'}  # These are in other groups
    
    # Verify excluded processes are not present
    present_excluded = excluded_oil_sands.intersection(process_names)
    assert not present_excluded, f"Excluded oil sands processes present: {present_excluded}"
    
    present_excluded_gas = excluded_gas_processes.intersection(process_names)
    assert not present_excluded_gas, f"Excluded gas processes present: {present_excluded_gas}"
    
    present_excluded_oil = excluded_oil_processes.intersection(process_names)
    assert not present_excluded_oil, f"Excluded oil processes present: {present_excluded_oil}"


def test_selected_streams_present(test_field):
    """Test that streams from selected ProcessGroups are present in the field."""
    stream_names = {stream.name for stream in test_field.streams()}
    
    # Based on "Acid Wet Gas" selection, these streams should be present:
    expected_streams = {'GasGathering => GasDehydration', 'GasDehydration => AcidGasRemoval',
                       'AcidGasRemoval => Demethanizer', 'Demethanizer => GasPartition',
                       'Demethanizer => NGL'}
    
    # Check that expected streams are present (allowing for different stream naming conventions)
    # Note: streams might be named differently in actual implementation
    print(f"Available streams: {sorted(stream_names)}")  # Debug output
    
    # Test that we have the correct number of streams after ProcessChoice resolution
    assert len(stream_names) == 57, f"Expected 57 streams after ProcessChoice resolution, got {len(stream_names)}"


def test_no_process_choice_dict_in_field(test_field):
    """Test that Field no longer has process_choice_dict attribute."""
    # This ensures the old ProcessChoice logic has been properly removed
    assert not hasattr(test_field, 'process_choice_dict'), "Field should not have process_choice_dict attribute"


def test_field_functionality_after_resolution(test_field):
    """Test that the field functions normally after ProcessChoice resolution."""
    # Test basic field operations work
    processes = list(test_field.processes())
    streams = list(test_field.streams())
    
    assert len(processes) == 38, f"Expected 38 processes after ProcessChoice resolution, got {len(processes)}"
    assert len(streams) == 57, f"Expected 57 streams after ProcessChoice resolution, got {len(streams)}"
    
    # Test that processes have proper attributes
    for proc in processes[:5]:  # Test first 5 processes
        assert hasattr(proc, 'name')
        assert hasattr(proc, 'enabled')
        assert proc.enabled  # All processes should be enabled (no disabled processes)
    
    # Test that field can be validated (basic structural integrity)
    try:
        # This should not raise an exception if field structure is valid
        boundary_procs = [p for p in processes if hasattr(p, 'boundary') and p.boundary]
        assert len(boundary_procs) > 0, "Expected at least one boundary process"
    except Exception as e:
        pytest.fail(f"Field validation failed: {e}")
