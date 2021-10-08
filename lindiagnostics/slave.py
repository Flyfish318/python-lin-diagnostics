from .constants import *
from .transport import Transport

class LinSlave:
    def __init__(self, nad, supplier_id, function_id, variant_id, driver, serial_number=bytes([0x01, 0x02, 0x03, 0x04])):
        self._nad = nad
        self._saved_nad = None
        self._supplier_id = supplier_id
        self._function_id = function_id
        self._variant_id = variant_id
        self._serial_number = serial_number
        self._driver = driver
        self._transport = Transport(True, driver)
        self._frame_identifiers = [None, None, None, None, None]

    @property
    def nad(self):
        return self._nad

    @property
    def saved_nad(self):
        return self._saved_nad

    @property
    def frame_identifiers(self):
        return self._frame_identifiers

    def matches_id(self, supplier_id, function_id):
        return (((supplier_id == self._supplier_id) or (supplier_id == BROADCAST_SUPPLIER_ID)) and
                ((function_id == self._function_id) or (function_id == BROADCAST_FUNCTION_ID)))

    def get_id_bytes(self, id_type):
        if id_type == DATA_IDENTIFIER_LIN_PRODUCT_IDENTIFIER:
            return bytes([self._supplier_id & 0xff, self._supplier_id >> 8, self._function_id & 0xff, self._function_id >> 8, self._variant_id & 0xff])
        elif id_type == DATA_IDENTIFIER_SERIAL_NUMBER:
            return self._serial_number
        else:
            print(f"Unsupported ID type: {id_type}")
            return None

    def transmit_negative_response(self, requested_sid, error_code):
        self._transport.transmit(self._nad, 0x7F, bytes([requested_sid, error_code]))

    def simulate(self):
        # Don't run the transport, we'll cycle it manually since we require the caller to
        # cycle the slave periodically
        self._transport.execute()

        nad, sid, data = None, None, None
        try:
            nad, sid, data = self._transport.receive()
        except TypeError:
            pass

        if nad == self._nad or nad == BROADCAST_NAD:
            if sid == READ_BY_IDENTIFIER_SID:
                identifier = data[0]
                supplier_id = data[1] | (data[2] << 8)
                function_id = data[3] | (data[4] << 8)
                if self.matches_id(supplier_id, function_id):
                    response = self.get_id_bytes(identifier)
                    if response is not None:
                        self._transport.transmit(self._nad, sid + 0x40, response)
                    else:
                        self.transmit_negative_response(sid, 0x12)

            elif sid == SAVE_CONFIGURATION_SID:
                self._saved_nad = self._nad
                self._transport.transmit(self._nad, sid + 0x40, bytes())

            elif sid == ASSIGN_NAD_SID:
                supplier_id = data[0] | (data[1] << 8)
                function_id = data[2] | (data[3] << 8)
                new_nad = data[4]
                if self.matches_id(supplier_id, function_id):
                    self._transport.transmit(self._nad, sid + 0x40, bytes())
                    self._nad = new_nad
                        
            elif sid == ASSIGN_FRAME_IDENTIFIER_RANGE_SID:
                start_index = data[0]
                for i in range(4):
                    try:
                        if data[1 + i] == 0x00:
                            # Unset
                            self._frame_identifiers[start_index + i] = None
                        elif data[1 + i] == 0xff:
                            # Do-not-care
                            pass
                        else:
                            # Assign
                            self._frame_identifiers[start_index + i] = data[1 + i]
                    except IndexError:
                        break
                self._transport.transmit(self._nad, sid + 0x40, bytes())

            elif sid == CONDITIONAL_CHANGE_NAD_SID:
                id_type = data[0]
                id_byte_index = data[1]
                id_mask = data[2]
                id_invert = data[3]
                new_nad = data[4]

                id_bytes = self.get_id_bytes(id_type)
                if id_bytes is None:
                    id_bytes = [0x00] * 5

                target_byte = (id_bytes[id_byte_index - 1] ^ id_invert) & id_mask
                
                if target_byte == 0:
                    # The Conditional Change NAD is addressed with the current NAD, i.e. it does not use the initial
                    # NAD as opposed to the Assign NAD request
                    self._nad = new_nad
                    self._transport.transmit(self._nad, sid + 0x40, bytes())

            elif sid == DATA_DUMP_SID:
                # Data dump - user defined. Mirror back command for now
                self._transport.transmit(self._nad, sid + 0x40, data)

            elif sid == ASSIGN_NAD_VIA_SNPD_SID:
                # assign nad via snpd - too lazy to go lookup snpd spec
                # LIN Slave Node Position Detection - Implementation Note, version 1.0 
                pass

            elif sid == ASSIGN_FRAME_IDENTIFIER_SID:
                # Assign frame identifier - obsolete, too lazy to lookup old spec
                pass

            elif sid == 0x22:
                # UDS Read Data By Identifier
                if data[0] == 0x12 and data[1] == 0x34:
                    self._transport.transmit(self._nad, sid + 0x40, bytes([data[0], data[1], 0x00, 0x01]))
            elif sid == 0x31:
                # UDS Routine Contrl
                print(f"Slave received Routine Control: {nad} {sid} {data}")
                if data[0] == 0x01 and data[1] == 0x00 and data[2] == 0x01:
                    self._transport.transmit(self._nad, sid + 0x40, data)
            elif sid == 0x3E:
                # UDS Tester present
                if data[0] == 0x00:
                    self._transport.transmit(self._nad, sid + 0x40, bytes([0x00]))

        self._transport.execute()
