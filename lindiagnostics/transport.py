from enum import IntEnum
from threading import Thread, Event
from queue import Queue
import time
import logging
from .constants import MASTER_DIAGNOSTIC_FRAME_ID, SLAVE_DIAGNOSTIC_FRAME_ID
from .event import LinEvent

logger = logging.getLogger(__name__)

class TransportThread(Thread):
    def __init__(self, transport):
        Thread.__init__(self)
        self._transport = transport
        self._running = Event()

    def run(self):
        self._running.clear()
        print("Starting thread")
        while not self._running.is_set():
            print("Cycling thread")
            self._transport.execute()
            time.sleep(0.010)
        print("done thread")

    def stop(self):
        self._running.set()


class Transport:
    class PCIType(IntEnum):
        SF = 0
        FF = 1
        CF = 2

    def __init__(self, is_slave, driver):
        self._thread = None
        self._is_slave = is_slave
        self._tx_queue = Queue()
        self._rx_queue = Queue()
        self._reset_state()
        self._driver = driver
        self._scheduled_tx_event = None
        self._timeout = 0.500

    def run(self):
        self._thread = TransportThread(self)
        self._thread.start()

    def close(self):
        if self._thread is not None:
            self._thread.stop()
            self._thread.join()
            self._thread = None

    def execute(self):
        while True:
           event = self._driver.read_event(self._timeout)
           print(event)
           if event is None:
               break
           else:
               self._receive_from_driver(event)

        if self._is_slave:
            if self._scheduled_tx_event is None and not self._tx_queue.empty():
                event = self._tx_queue.get()
                self._driver.schedule_slave_response(event)
                self._scheduled_tx_event = event
        else:
            if not self._tx_queue.empty():
                event = self._tx_queue.get()
                self._driver.write_message(event)
            else:
                self._driver.request_slave_response(SLAVE_DIAGNOSTIC_FRAME_ID)

    def receive(self):
        if self._rx_queue.empty():
            return None
        else:
            return self._rx_queue.get()

    def _reset_state(self):
        self._current_frame_data = bytearray()
        self._current_sid = None
        self._current_nad = None
        self._current_frame_counter = 0
        self._remaining_bytes = 0

    def transmit(self, nad, sid, data):
        event_id = MASTER_DIAGNOSTIC_FRAME_ID
        if self._is_slave:
            event_id = SLAVE_DIAGNOSTIC_FRAME_ID

        print(f"Transmitting: {event_id} {nad} {sid} {data}")

        if len(data) <= 5:
            print("Using SF")
            # SF
            # Pad with 0xff
            pci = (Transport.PCIType.SF << 4) | len(data)
            response = bytearray([nad, pci, sid, 0xff, 0xff, 0xff, 0xff, 0xff])
            # Copy over pyaload
            for i, byte in enumerate(data):
                response[3 + i] = byte
            self._tx_queue.put(LinEvent(event_id, bytes(response), LinEvent.ChecksumType.CLASSIC))
        else:
            pass

    def _receive_from_driver(self, event):
        event_id, frame_bytes, frame_length = event.event_id, event.event_payload, len(event.event_payload)

        # TODO: Clear on-deck for slave

        if event.direction == LinEvent.Direction.RX:
            if frame_length < 8:
                # If a PDU is not completely filled (applies to CF and SF PDUs only) the unused bytes shall be filled with ones, i.e. their value shall be 255 (0xFF).
                raise ValueError("SF Frames with unused bytes shall be padded to 8 bytes with ones")

            nad, pci = frame_bytes[0], frame_bytes[1]
            pci_type = Transport.PCIType(pci >> 4)
            additional_information = pci & 0x0f
            
            if pci_type == Transport.PCIType.SF:
                # Single Frame

                # Request:
                # | NAD | PCI | SID | D1 | D2 | D3 | D4 | D5 |
                #    0     1     2     3    4    5    6    7
                #
                # Response:
                # | NAD | PCI | RSID | D1 | D2 | D3 | D4 | D5 |
                #    0     1      2     3    4    5    6    7

                if self._remaining_bytes > 0:
                    logger.warn("Received a First-Frame before completing the last one. Previous frame dropped")
                    self._reset_state()

                sid = frame_bytes[2]
                length = additional_information
                data = frame_bytes[3:3+length]
                self._reset_state()
                self._rx_queue.put((nad, sid, data))

            elif pci_type == Transport.PCIType.FF:
                # First Frame
                # Request:
                # | NAD | PCI | LEN | SID | D1 | D2 | D3 | D4 |
                #    0     1     2     3     4    5    6    7
                #
                # Response:
                # | NAD | PCI | LEN | RSID | D1 | D2 | D3 | D4 |
                #    0     1     2      3     4    5    6    7

                if self._remaining_bytes > 0:
                    logger.warn("Received a First-Frame before completing the last one. Previous frame dropped")
                    self._reset_state()

                length = (additional_information << 8) | frame_bytes[2]
                sid = frame_bytes[3]
                self._remaining_bytes = length - 4
                self._current_frame_data += frame_bytes[4:]
                self._current_nad = nad
                self._current_sid = sid

            elif pci_type == Transport.PCIType.CF:
                # Consecutive Frame
                # Request/Response:
                # | NAD | PCI | D1 | D2 | D3 | D4 | D5 | D6 |
                #    0     1     2    3    4    5    6    7

                if self._remaining_bytes == 0:
                    logger.warn("Received a Consecutive Frame but was not expecting more bytes. Discarding")
                    self._reset_state()
                    return

                frame_counter = additional_information
                if frame_counter != (self._current_frame_counter + 1) % 16:
                    logger.warn("Received an out-of-order Consecutive Frame but was not expecting more bytes. Discarding")
                    self._reset_state()
                    return

                length = min(self._remaining_bytes, 6)
                self._remaining_bytes -= length
                self._current_frame_data += frame_bytes[2:2 + length]

                if (self._remaining_bytes == 0):
                    nad, sid, data = self._current_nad, self._current_sid, self._current_frame_data
                    self._reset_state()
                    self._rx_queue.put((nad, sid, data))
