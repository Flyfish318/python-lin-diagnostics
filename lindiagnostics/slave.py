from .constants import BROADCAST_NAD
from .transport import Transport

class LinSlave:
    def __init__(self, nad, supplier_id, function_id, variant_id, driver):
        self._nad = nad
        self._supplier_id = supplier_id
        self._function_id = function_id
        self._variant_id = variant_id
        self._driver = driver
        self._transport = Transport(True, driver)

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
            if sid == 0xB2:
                # Read by ID
                pass
            elif sid == 0xB6:
                # Save configuration
                pass
            elif sid == 0xB0:
                # Assign NAD
                pass
            elif sid == 0xB1:
                # Assign frame identifier
                pass
            elif sid == 0xB3:
                # Conditional change NAD
                pass
            elif sid == 0xb4:
                # Data dump
                pass
            elif sid == 0xb5:
                # assign nad via snpd
                pass
            elif sid == 0xb7:
                # Assign frame identifier range
                pass
            elif sid == 0x3E:
                # UDS Tester present
                if data[0] == 0x00:
                    self._transport.transmit(self._nad, sid + 0x40, bytes([0x00]))

        self._transport.execute()
