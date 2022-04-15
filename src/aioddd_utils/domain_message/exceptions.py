from marshmallow.exceptions import ValidationError

__all__ = ['ValidationError', 'UnknownMessageType']


class UnknownMessageType(Exception):
    def __init__(self, domain: str, message_type: str):
        super(UnknownMessageType, self).__init__(f'Unknown message type {domain=} {message_type=}')