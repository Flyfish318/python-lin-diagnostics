from copy import deepcopy
import queue
import time
from ..slave import LinSlave
from ..event import LinEvent

class SimulatedLinDriver:
    def __init__(self, network, is_slave):
        self.is_slave = is_slave
        self.network = network
        self.event_queue = queue.Queue()

    def read_event(self, timeout):
        try:
            return self.event_queue.get(block=True, timeout=timeout)
        except queue.Empty:
            return None

    def write_message(self, lin_event):
        if not self.is_slave:
            self.network.write_message(lin_event)

    def schedule_slave_response(self, lin_event):
        if self.is_slave:
            self.network.schedule_slave_response(lin_event)

    def request_slave_response(self, message_id):
        if not self.is_slave:
            self.network.request_slave_response(message_id)


class SimulatedLinNetwork:
    def __init__(self):
        self.slave_responses = dict()
        self.slave_rx_queue = queue.Queue()
        self.master_driver = None
        self.slave_drivers = []
        self.slaves = []
        self.callbacks = []

    def write_message(self, lin_event):
        print(f"Writing Message: {lin_event}")
        event_time = time.time()

        master_tx_event = deepcopy(lin_event)
        master_tx_event.timestamp = event_time
        master_tx_event.direction = LinEvent.Direction.TX
        self.master_driver.event_queue.put(lin_event)

        slave_rx_event = deepcopy(lin_event)
        slave_rx_event.direction = LinEvent.Direction.RX
        slave_rx_event.timestamp = event_time

        for slave_driver in self.slave_drivers:
            slave_driver.event_queue.put(slave_rx_event)

        for slave in self.slaves:
            slave.simulate()

    def request_slave_response(self, message_id):
        print(f"Requesting Slave Response: {message_id}")
        try:
            result = self.slave_responses.pop(message_id)
        except KeyError:
            return

        event_time = time.time()

        slave_tx_event = deepcopy(result)
        slave_tx_event.direction = LinEvent.Direction.TX
        slave_tx_event.timestamp = event_time
        for slave_driver in self.slave_drivers:
            slave_driver.event_queue.put(slave_tx_event)

        master_rx_event = deepcopy(result)
        master_rx_event.direction = LinEvent.Direction.RX
        master_rx_event.timestamp = event_time

        self.master_driver.event_queue.put(master_rx_event)

        for slave in self.slaves:
            slave.simulate()

    def schedule_slave_response(self, lin_event):
        print(f"Scheduling Slave Response: {lin_event}")
        self.slave_responses[lin_event.event_id] = lin_event

    def get_master_driver(self):
        if self.master_driver is None:
            self.master_driver = SimulatedLinDriver(self, False)
        return self.master_driver

    def register_slave(self, nad, supplier_id, function_id, variant_id, serial_number=None):
        slave_driver = SimulatedLinDriver(self, True)
        slave = LinSlave(nad, supplier_id, function_id, variant_id, slave_driver, serial_number=serial_number)
        self.slaves.append(slave)
        self.slave_drivers.append(slave_driver)
        return slave
