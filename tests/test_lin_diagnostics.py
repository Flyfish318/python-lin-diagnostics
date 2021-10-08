import pytest
from lindiagnostics import LinMaster
from lindiagnostics.drivers import SimulatedLinNetwork
from lindiagnostics.constants import *

SLAVE_NAD = 1
SLAVE_SUPPLIER_ID = 2
SLAVE_FUNCTION_ID = 3
SLAVE_VARIANT_ID = 4
SLAVE_SERIAL_NUMBER = bytes([1,2,3,4])

@pytest.fixture
def simulated_lin_network():
    return SimulatedLinNetwork()

@pytest.fixture
def lin_slave(simulated_lin_network):
    return simulated_lin_network.register_slave(SLAVE_NAD, SLAVE_SUPPLIER_ID, SLAVE_FUNCTION_ID, SLAVE_VARIANT_ID, serial_number = SLAVE_SERIAL_NUMBER)

@pytest.fixture
def lin_master(simulated_lin_network):
    master_driver = simulated_lin_network.get_master_driver()
    with LinMaster(master_driver) as lin_master:
        yield lin_master

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
@pytest.mark.parametrize('target_supplier_id', (SLAVE_SUPPLIER_ID, BROADCAST_SUPPLIER_ID))
@pytest.mark.parametrize('target_function_id', (SLAVE_FUNCTION_ID, BROADCAST_FUNCTION_ID))
def test_read_product_identifier(lin_slave, lin_master, target_function_id, target_supplier_id, target_nad):
    result = lin_master.get_slave_product_identifier(supplier_id=target_supplier_id, function_id=target_function_id, nad=target_nad)
    assert result == (SLAVE_NAD, SLAVE_SUPPLIER_ID, SLAVE_FUNCTION_ID, SLAVE_VARIANT_ID)

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
@pytest.mark.parametrize('target_supplier_id', (SLAVE_SUPPLIER_ID, BROADCAST_SUPPLIER_ID))
@pytest.mark.parametrize('target_function_id', (SLAVE_FUNCTION_ID, BROADCAST_FUNCTION_ID))
def test_read_serial_number(lin_slave, lin_master, target_function_id, target_supplier_id, target_nad):
    result = lin_master.get_slave_serial_number(supplier_id=target_supplier_id, function_id=target_function_id, nad=target_nad)
    assert result == (SLAVE_NAD, SLAVE_SERIAL_NUMBER)

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
@pytest.mark.parametrize('target_supplier_id', (SLAVE_SUPPLIER_ID, BROADCAST_SUPPLIER_ID))
@pytest.mark.parametrize('target_function_id', (SLAVE_FUNCTION_ID, BROADCAST_FUNCTION_ID))
def test_read_bad_sid(lin_slave, lin_master, target_function_id, target_supplier_id, target_nad):
    with pytest.raises(NotImplementedError) as excinfo:
        result = lin_master.read_by_identifier(3, supplier_id=target_supplier_id, function_id=target_function_id, nad=target_nad)

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
@pytest.mark.parametrize('target_supplier_id', (SLAVE_SUPPLIER_ID, BROADCAST_SUPPLIER_ID))
@pytest.mark.parametrize('target_function_id', (SLAVE_FUNCTION_ID, BROADCAST_FUNCTION_ID))
def test_assign_nad_by(lin_slave, lin_master, target_function_id, target_supplier_id, target_nad):
    new_nad = SLAVE_NAD + 1
    result = lin_master.assign_slave_nad(new_nad, supplier_id=target_supplier_id, function_id=target_function_id, nad=target_nad)
    assert SLAVE_NAD == result
    assert lin_slave.nad == new_nad

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_save_configuration(lin_slave, lin_master, target_nad):
    result = lin_master.save_slave_configuration(nad=target_nad)
    assert SLAVE_NAD == result
    assert lin_slave.saved_nad == SLAVE_NAD

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_assign_frame_ids(lin_slave, lin_master, target_nad):
    result = lin_master.assign_slave_frame_ids(1, [0x80, 0xc1, 0x42, 0x0], nad=target_nad)
    assert SLAVE_NAD == result
    assert lin_slave.frame_identifiers == [None, 0x80, 0xc1, 0x42, None]

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_conditional_change_nad_case_1_match(lin_slave, lin_master, target_nad):
    id_type = 1 # Serial (1,2,3,4)
    id_byte_index = 3 # The third byte (3)
    id_mask = 0x2 # Final mask
    id_invert = 0x2 # XOR
    new_nad = SLAVE_NAD + 1
    # (3 ^ 2) & 2 == 0
    result = lin_master.conditional_change_slave_nad(id_type, id_byte_index, id_mask, id_invert, new_nad, nad=target_nad)
    assert new_nad == result

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_conditional_change_nad_case_1_no_match(lin_slave, lin_master, target_nad):
    id_type = 1 # Serial (1,2,3,4)
    id_byte_index = 3 # The third byte (3)
    id_mask = 0x1 # Final mask
    id_invert = 0x2 # XOR
    new_nad = SLAVE_NAD + 1
    # (3 ^ 2) & 1 == 1
    with pytest.raises(TimeoutError) as excinfo:
        result = lin_master.conditional_change_slave_nad(id_type, id_byte_index, id_mask, id_invert, new_nad, nad=target_nad, timeout=0.5)


@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_conditional_change_nad_case_0_match(lin_slave, lin_master, target_nad):
    id_type = 0 # Product ID (2, 0, 3, 0, 4)
    id_byte_index = 1 # The first byte (2)
    id_mask = 0x4 # Final mask
    id_invert = 0x1 # XOR
    new_nad = SLAVE_NAD + 1
    # (2 ^ 1) & 4 == 0
    result = lin_master.conditional_change_slave_nad(id_type, id_byte_index, id_mask, id_invert, new_nad, nad=target_nad)
    assert new_nad == result

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_conditional_change_nad_case_0_no_match(lin_slave, lin_master, target_nad):
    id_type = 0 # Product ID (2, 0, 3, 0, 4)
    id_byte_index = 1 # The first byte (2)
    id_mask = 0x1 # Final mask
    id_invert = 0x3 # XOR
    new_nad = SLAVE_NAD + 1
    # (2 ^ 3) & 1 == 1
    with pytest.raises(TimeoutError) as excinfo:
        result = lin_master.conditional_change_slave_nad(id_type, id_byte_index, id_mask, id_invert, new_nad, nad=target_nad, timeout=0.5)

@pytest.mark.parametrize('target_nad', (SLAVE_NAD, BROADCAST_NAD))
def test_data_dump(lin_slave, lin_master, target_nad):
    payload = bytes(list(range(5)))
    result = lin_master.slave_data_dump(payload, nad=target_nad)
    assert SLAVE_NAD, payload == result
