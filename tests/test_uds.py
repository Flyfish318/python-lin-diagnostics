import pytest
from lindiagnostics import LinMaster
from lindiagnostics.drivers import SimulatedLinNetwork
from lindiagnostics.connectors import LinDiagnosticsUDSConnector
from udsoncan.client import Client

def test_tester_present():
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        with LinDiagnosticsUDSConnector(lin_master, nad) as lin_diagnostic_connector:
            with Client(lin_diagnostic_connector) as uds_client:
                result = uds_client.tester_present()
                assert result.valid
                assert result.data == bytes([0x00])


def test_routine_control_present():
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        with LinDiagnosticsUDSConnector(lin_master, nad) as lin_diagnostic_connector:
            with Client(lin_diagnostic_connector) as uds_client:
                result = uds_client.start_routine(0x1, data=bytes(10))
                assert result.valid
                assert result.data == bytes([0x01, 0x00, 0x01] + [0x00] * 10)
