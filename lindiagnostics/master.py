import time
from .transport import Transport
from .constants import *

class LinMaster:
    def __init__(self, driver):
        self._driver = driver
        self._transport = Transport(False, driver)
        self._transport.run()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self._transport.close()

    def assign_slave_frame_ids(self, start_index, frame_ids, nad=None, timeout=None):
        sid = ASSIGN_FRAME_IDENTIFIER_RANGE_SID
        payload = bytearray([start_index, 0xff, 0xff, 0xff, 0xff])
        if len(frame_ids) > 4:
            raise ValueError("Can only assign 4 frame ID's at once")
        else:
            for i, frame_id in enumerate(frame_ids):
                payload[1 + i] = frame_id

        target_nad = BROADCAST_NAD
        if nad is not None:
            target_nad = nad
        self._transport.transmit(target_nad, sid, bytes(payload))
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError("Timed out waiting for slave to respond to Assign NAD")
            result = self._transport.receive()
            if result is not None:
                nad, rsid, _ = result
                if rsid == sid + 0x40:
                    return nad

    def assign_slave_nad(self, new_nad, supplier_id=BROADCAST_SUPPLIER_ID, function_id=BROADCAST_FUNCTION_ID, nad=BROADCAST_NAD, timeout=None):
        sid = ASSIGN_NAD_SID
        payload = bytes([supplier_id & 0xff, supplier_id >> 8, function_id & 0xff, function_id >> 8, new_nad])
        self._transport.transmit(nad, sid, payload)
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError("Timed out waiting for slave to respond to Assign NAD")
            result = self._transport.receive()
            if result is not None:
                nad, rsid, _ = result
                if rsid == sid + 0x40:
                    return nad

    def save_slave_configuration(self, nad=None, timeout=None):
        sid = SAVE_CONFIGURATION_SID
        payload = bytes()
        self._transport.transmit(nad, sid, payload)
        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError("Timed out waiting for slave to respond to Read By Identifier")
            result = self._transport.receive()
            if result is not None:
                nad, rsid, payload = result
                if rsid == sid + 0x40:
                    return nad

    def slave_data_dump(self, payload, nad=None, timeout=None):
        sid = DATA_DUMP_SID
        if len(payload) > 5:
            raise ValueError("Payload must be less than 5 bytes.")
        self._transport.transmit(nad, sid, payload)
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError("Timed out waiting for slave to respond to Conditional Change NAD")
            result = self._transport.receive()
            if result is not None:
                nad, rsid, payload = result
                if rsid == sid + 0x40:
                    return nad, payload

    def get_slave_serial_number(self, supplier_id=BROADCAST_SUPPLIER_ID, function_id=BROADCAST_FUNCTION_ID, nad=BROADCAST_NAD, timeout=None):
        nad, payload = self.read_by_identifier(DATA_IDENTIFIER_SERIAL_NUMBER, supplier_id=supplier_id, function_id=function_id, nad=nad, timeout=timeout)
        return nad, bytes([payload[0], payload[1], payload[2], payload[3]])

    def get_slave_product_identifier(self, supplier_id=BROADCAST_SUPPLIER_ID, function_id=BROADCAST_FUNCTION_ID, nad=BROADCAST_NAD, timeout=None):
        nad, payload = self.read_by_identifier(DATA_IDENTIFIER_LIN_PRODUCT_IDENTIFIER, supplier_id=supplier_id, function_id=function_id, nad=nad, timeout=timeout)
        return nad, payload[0] | payload[1] << 8, payload[2] | payload[3] << 8, payload[4]

    def conditional_change_slave_nad(self, id_type, id_byte_index, id_mask, id_invert, new_nad, nad=None, timeout=None):
        sid = CONDITIONAL_CHANGE_NAD_SID
        payload = bytes([id_type, id_byte_index, id_mask, id_invert, new_nad])
        self._transport.transmit(nad, sid, payload)
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError("Timed out waiting for slave to respond to Conditional Change NAD")
            result = self._transport.receive()
            if result is not None:
                nad, rsid, payload = result
                if rsid == sid + 0x40:
                    return nad

    def read_by_identifier(self, identifier, supplier_id=BROADCAST_SUPPLIER_ID, function_id=BROADCAST_FUNCTION_ID, nad=BROADCAST_NAD, timeout=None):
        sid = READ_BY_IDENTIFIER_SID
        payload = bytes([identifier, supplier_id & 0xff, supplier_id >> 8, function_id & 0xff, function_id >> 8])
        self._transport.transmit(nad, sid, payload)
        start_time = time.time()
        while True:
            if timeout and time.time() - start_time > timeout:
                raise TimeoutError("Timed out waiting for slave to respond to Read By Identifier")
            result = self._transport.receive()
            if result is not None:
                nad, rsid, payload = result
                if rsid == sid + 0x40:
                    return nad, payload
                elif rsid == 0x7f:
                    raise NotImplementedError("Slave did not support Read Identifier 0x{identifer:x}. Error code: 0x:{payload[1]}")

    def send_diagnostic(self, nad, sid, payload):
        self._transport.transmit(nad, sid, payload)

    def receive_diagnostic(self, timeout=None):
        start_time = time.time()
        while time.time() - start_time < timeout:
            return self._transport.receive()

    def empty_rxqueue(self):
        pass

    def empty_txqueue(self):
        pass
