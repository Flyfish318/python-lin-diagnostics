import pytest
from lindiagnostics import LinMaster
from lindiagnostics.drivers import SimulatedLinNetwork

#TODO: Test allow all broadcasts

@pytest.mark.parametrize('broadcast', (True, False))
def test_read_product_identifier(broadcast):
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        if broadcast:
            result = lin_master.get_slave_product_identifier(supplier_id, function_id)
        else:
            result = lin_master.get_slave_product_identifier(supplier_id, function_id, nad=nad)
        assert (nad, supplier_id, function_id, variant_id) == result


@pytest.mark.parametrize('broadcast', (True, False))
def test_read_serial_number(broadcast):
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    serial_number = bytes([0x01, 0x02, 0x03, 0x04])
    simulated_network.register_slave(nad, supplier_id, function_id, variant_id, serial_number = serial_number)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        if broadcast:
            result = lin_master.get_slave_serial_number(supplier_id, function_id)
        else:
            result = lin_master.get_slave_serial_number(supplier_id, function_id, nad=nad)
        assert (nad, serial_number) == result


@pytest.mark.parametrize('broadcast', (True, False))
def test_assign_nad_by(broadcast):
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    new_nad = 2
    slave = simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        if broadcast:
            result = lin_master.assign_slave_nad(supplier_id, function_id, new_nad)
        else:
            result = lin_master.assign_slave_nad(supplier_id, function_id, new_nad, initial_nad=nad)
        assert nad == result
        assert slave.nad == new_nad

@pytest.mark.parametrize('broadcast', (True, False))
def test_save_configuration(broadcast):
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    slave = simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        if broadcast:
            result = lin_master.save_slave_configuration()
        else:
            result = lin_master.save_slave_configuration(nad=nad)
        assert nad == result
        assert slave.saved_nad == nad

@pytest.mark.parametrize('broadcast', (True, False))
def test_assign_frame_ids(broadcast):
    simulated_network = SimulatedLinNetwork()
    nad = 1
    supplier_id = 2
    function_id = 3
    variant_id = 4
    slave = simulated_network.register_slave(nad, supplier_id, function_id, variant_id)
    master_driver = simulated_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        if broadcast:
            result = lin_master.assign_slave_frame_ids(1, [0x80, 0xc1, 0x42, 0x0])
        else:
            result = lin_master.assign_slave_frame_ids(1, [0x80, 0xc1, 0x42, 0x0], nad=nad)
        assert nad == result
        assert slave.frame_identifiers == [None, 0x80, 0xc1, 0x42, None]
