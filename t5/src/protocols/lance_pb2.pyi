from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OnLanceRequest(_message.Message):
    __slots__ = ("leilao_id", "client_id", "value")
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    leilao_id: str
    client_id: str
    value: str
    def __init__(self, leilao_id: _Optional[str] = ..., client_id: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class OnLanceResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...

class OnInitLeilaoRequest(_message.Message):
    __slots__ = ("id", "description", "start", "end")
    ID_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    id: str
    description: str
    start: float
    end: float
    def __init__(self, id: _Optional[str] = ..., description: _Optional[str] = ..., start: _Optional[float] = ..., end: _Optional[float] = ...) -> None: ...

class OnInitLeilaoResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...

class OnEndLeilaoRequest(_message.Message):
    __slots__ = ("id",)
    ID_FIELD_NUMBER: _ClassVar[int]
    id: str
    def __init__(self, id: _Optional[str] = ...) -> None: ...

class OnEndLeilaoResponse(_message.Message):
    __slots__ = ("ok", "leilao_id", "cliente_vencedor", "lance_vencedor")
    OK_FIELD_NUMBER: _ClassVar[int]
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENTE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    LANCE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    leilao_id: str
    cliente_vencedor: str
    lance_vencedor: str
    def __init__(self, ok: bool = ..., leilao_id: _Optional[str] = ..., cliente_vencedor: _Optional[str] = ..., lance_vencedor: _Optional[str] = ...) -> None: ...
