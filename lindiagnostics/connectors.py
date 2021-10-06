from .constants import BROADCAST_NAD

import time
from udsoncan.connections import BaseConnection

class LinDiagnosticsUDSConnector(BaseConnection):
    def __init__(self, lin_master, slave_nad, name=None):
        BaseConnection.__init__(self, name)
        self._lin_master = lin_master
        self._slave_nad = slave_nad
        self.opened = False

    def open(self):
        self.opened = True

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()

    def close(self):
        self.opened = False

    def is_open(self):
        return self.opened

    def specific_send(self, payload):
        sid = payload[0]
        print(f"udsoncan requested to send SID: 0x{sid:X}, Payload: {payload}")
        self._lin_master.send_diagnostic(self._slave_nad, sid, bytearray(payload[1:]))

    def specific_wait_frame(self, timeout=2):
        start_time = time.time()
        while time.time() - start_time < 10:
            result = self._lin_master.receive_diagnostic(timeout=timeout)
            if result:
                nad, sid, payload = result
                print(f"Received: {nad}, {sid}, {payload}")
                if (nad == BROADCAST_NAD) or (nad == self._slave_nad):
                    return bytes([sid, *payload])
        raise TimeoutError("Failed to receive response in time")

    def empty_rxqueue(self):
        self._lin_master.empty_rxqueue()

    def empty_txqueue(self):
        self._lin_master.empty_txqueue()

