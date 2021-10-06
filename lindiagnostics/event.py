from enum import IntEnum

class LinEvent:
    class Direction(IntEnum):
        RX = 0
        TX = 1

    class ChecksumType(IntEnum):
        CLASSIC = 0
        ENHANCED = 1

    def __init__(self, event_id, event_payload, checksum_type, direction=None, timestamp=None):
        self.event_id = event_id
        self.event_payload = event_payload
        self.checksum_type = checksum_type
        self.direction = direction
        self.timestamp = timestamp

    def __str__(self):
        return repr(self)

    def __repr__(self):
        return f"LinEvent(0x{self.event_id:X}, {self.event_payload}, {self.checksum_type}, {self.direction}, {self.timestamp})"
