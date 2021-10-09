import queue
import time

from ..event import LinEvent
from ..constants import *

has_linlib = False
try:
    import canlib
    from canlib import linlib
    from canlib import LINFrame
    has_linlib = True
except ImportError:
    pass

class KvaserLinDriver:
    @staticmethod
    def get_virtual_channel(serial, port):
        if not has_linlib:
            raise ImportError("You need Kvaser CAN/LINLib to use Kvaser driver")

        port = 0
        for channel in range(canlib.getNumberOfChannels()):
            channel_data = canlib.ChannelData(channel)
            if channel_data.card_serial_no == serial:
                if port == port:
                    return channel
                else:
                    port += 1

        if port > 0:
            raise IndexError(f"Kvaser serial {serial} was found but didn't have enough ports")
        else:
            raise IOError(f"Kvaser serial {serial} was not found. Check your drivers.")

    def __init__(self, virtual_channel, is_slave, baud_rate=19200, lin_2=True):
        self.is_slave = is_slave
        self.driver_event_queue = queue.Queue()
        self.baud_rate = baud_rate
        self.lin_2 = lin_2

        if self.is_slave:
            self.channel = linlib.openSlave(1)
        else:
            self.channel = linlib.openMaster(0)

        self.can_handle = self.channel.getCanHandle()

        if self.lin_2:
            self.flags = linlib.Setup.ENHANCED_CHECKSUM | linlib.Setup.VARIABLE_DLC
        else:
            self.flags = 0

        self.channel.busOn()
        self.channel.setupLIN(flags=self.flags, bps=self.baud_rate)

    def read_event(self, timeout=0):

        if timeout is None:
            read_timeout_ms = 0xFFFFFFFF
        else:
            read_timeout_ms = int(timeout * 1000) # Seconds to milliseconds

        try:
            while True:
                print("Reading event from driver, timeout", read_timeout_ms)
                self.driver_event_queue.put(self.channel.read(timeout=read_timeout_ms))
        except linlib.exceptions.LinNoMessageError:
            pass

        if self.driver_event_queue.empty():
            return None
        else:
            # Convert linlib event into our standardized format
            event = self.driver_event_queue.get()

            direction = LinEvent.Direction.RX
            if event.flags & linlib.MessageFlag.TX:
                direction = LinEvent.Direction.TX
            timestamp = time.time() # Todo: Use Kvaser IOCTL and magic
            lin_id = event.id
            if self.lin_2 and event.id not in (MASTER_DIAGNOSTIC_FRAME_ID, SLAVE_DIAGNOSTIC_FRAME_ID):
                checksum_type = LinEvent.ChecksumType.ENHANCED
            else:
                checksum_type = LinEvent.ChecksumType.CLASSIC
            checksum = event.info.checkSum
            return LinEvent(lin_id, event.data, checksum_type, direction=direction, timestamp=timestamp)

    def write_message(self, lin_event, timeout=1):
        # TODO: Error if event is not diagnostic and does not match checksum type
        # Kvaser can't send with mixed types
        frame = LINFrame(lin_event.event_id, lin_event.event_payload)
        if not self.is_slave:
            print("Writing message")
            print(lin_event)

            # Write the frame
            self.channel.writeMessage(frame)
            # Read until timeout or confirmed
            start_time = time.time()
            while (timeout is None) or (time.time() - start_time < timeout):
                read_timeout_ms = int(max(timeout - (time.time() - start_time), 0)) * 1000
                if timeout is None:
                    read_timeout_ms = 0xFFFFFFFF
                try:
                    event = self.channel.read(timeout=read_timeout_ms)
                    print(event)
                    self.driver_event_queue.put(event)
                    if event.id == lin_event.event_id and (event.flags & linlib.MessageFlag.TX):
                        print("Confirmed")
                        return
                except linlib.exceptions.LinNoMessageError:
                    pass
            raise TimeoutError("Timed out waiting for write message to confirm")
        else:
            raise NotImplementedError("LIN Master's can call write_message()")

    def schedule_slave_response(self, lin_event):
        frame = LINFrame(lin_event.event_id, lin_event.event_payload)
        if self.is_slave:
            self.channel.updateMessage(frame)
        else:
            raise NotImplementedError("Only LIN Slave's can call schedule_slave_response()")

    def request_slave_response(self, message_id):
        print(f"Requested ID: {message_id} from slave")

        if not self.is_slave:
            self.channel.requestMessage(message_id)
        else:
            raise NotImplementedError("Only LIN Master's can request a slave response")