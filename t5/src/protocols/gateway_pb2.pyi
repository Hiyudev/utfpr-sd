from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class OnLanceValidadoRequest(_message.Message):
    __slots__ = ("leilao_id", "client_id", "value")
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    leilao_id: str
    client_id: str
    value: str
    def __init__(self, leilao_id: _Optional[str] = ..., client_id: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class OnLanceValidadoResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...

class OnLanceInvalidadoRequest(_message.Message):
    __slots__ = ("leilao_id", "client_id", "value")
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    VALUE_FIELD_NUMBER: _ClassVar[int]
    leilao_id: str
    client_id: str
    value: str
    def __init__(self, leilao_id: _Optional[str] = ..., client_id: _Optional[str] = ..., value: _Optional[str] = ...) -> None: ...

class OnLanceInvalidadoResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...

class OnLeilaoVencedorRequest(_message.Message):
    __slots__ = ("leilao_id", "lance_vencedor", "cliente_vencedor")
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    LANCE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    CLIENTE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    leilao_id: str
    lance_vencedor: str
    cliente_vencedor: str
    def __init__(self, leilao_id: _Optional[str] = ..., lance_vencedor: _Optional[str] = ..., cliente_vencedor: _Optional[str] = ...) -> None: ...

class OnLeilaoVencedorResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...

class OnLinkPagamentoRequest(_message.Message):
    __slots__ = ("leilao_id", "lance_vencedor", "cliente_vencedor", "link")
    LEILAO_ID_FIELD_NUMBER: _ClassVar[int]
    LANCE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    CLIENTE_VENCEDOR_FIELD_NUMBER: _ClassVar[int]
    LINK_FIELD_NUMBER: _ClassVar[int]
    leilao_id: str
    lance_vencedor: str
    cliente_vencedor: str
    link: str
    def __init__(self, leilao_id: _Optional[str] = ..., lance_vencedor: _Optional[str] = ..., cliente_vencedor: _Optional[str] = ..., link: _Optional[str] = ...) -> None: ...

class OnLinkPagamentoResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...

class OnStatusPagamentoRequest(_message.Message):
    __slots__ = ("value", "status", "transaction_id", "client_id")
    VALUE_FIELD_NUMBER: _ClassVar[int]
    STATUS_FIELD_NUMBER: _ClassVar[int]
    TRANSACTION_ID_FIELD_NUMBER: _ClassVar[int]
    CLIENT_ID_FIELD_NUMBER: _ClassVar[int]
    value: str
    status: str
    transaction_id: str
    client_id: str
    def __init__(self, value: _Optional[str] = ..., status: _Optional[str] = ..., transaction_id: _Optional[str] = ..., client_id: _Optional[str] = ...) -> None: ...

class OnStatusPagamentoResponse(_message.Message):
    __slots__ = ("ok", "message")
    OK_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    ok: bool
    message: str
    def __init__(self, ok: bool = ..., message: _Optional[str] = ...) -> None: ...
