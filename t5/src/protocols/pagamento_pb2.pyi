from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OnWinnerRequest(_message.Message):
    __slots__ = ("leilao_id", "lance_vencedor", "cliente_vencedor")
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    LANCE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    CLIENTE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    leilao_id: str
    lance_vencedor: str
    cliente_vencedor: str
    def __init__(self, leilao_id: _Optional[str] = ..., lance_vencedor: _Optional[str] = ..., cliente_vencedor: _Optional[str] = ...) -> None: ...

class OnWinnerResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...
