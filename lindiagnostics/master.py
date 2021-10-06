import time
from .transport import Transport

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

    def change_slave_nad(supplier_id, funtion_id, new_nad):
        pass

    def get_slave_id(nad):
        pass

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
