from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from collections.abc import Mapping as _Mapping
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class Leilao_instance(_message.Message):
    __slots__ = ("id", "name", "description", "value", "start", "end")
    ID_FIELD_NUMBER: _ClassVar[int]
    NAME_FIELD_NUMBER: _ClassVar[int]
    DESCRIPTION_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    START_FIELD_NUMBER: _ClassVar[int]
    END_FIELD_NUMBER: _ClassVar[int]
    id: str
    name: str
    description: str
    value: str
    start: str
    end: str
    def __init__(self, id: _Optional[str] = ..., name: _Optional[str] = ..., description: _Optional[str] = ..., value: _Optional[str] = ..., start: _Optional[str] = ..., end: _Optional[str] = ...) -> None: ...

class GetLeiloesRequest(_message.Message):
    __slots__ = ("empty",)
    EMPTY_FIELD_NUMBER: _ClassVar[int]
    empty: str
    def __init__(self, empty: _Optional[str] = ...) -> None: ...

class GetLeiloesResponse(_message.Message):
    __slots__ = ("leilao",)
    LEILAO_FIELD_NUMBER: _ClassVar[int]
    leilao: Leilao_instance
    def __init__(self, leilao: _Optional[_Union[Leilao_instance, _Mapping]] = ...) -> None: ...

class CreateLeilaoRequest(_message.Message):
    __slots__ = ("leilao",)
    LEILAO_FIELD_NUMBER: _ClassVar[int]
    leilao: Leilao_instance
    def __init__(self, leilao: _Optional[_Union[Leilao_instance, _Mapping]] = ...) -> None: ...

class CreateLeilaoResponse(_message.Message):
    __slots__ = ("ok",)
    OK_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    def __init__(self, ok: bool = ...) -> None: ...
