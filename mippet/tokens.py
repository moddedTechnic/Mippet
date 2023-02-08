from enum import Enum
from typing import Iterable


class Tokens(Enum):
    KWD_PROC = r'proc'

    DOC_COMMENT = r'##'
    COMMENT = r'#.*'

    SECTION = r'\.[a-z]+'
    REGISTER = r'\$(zero|at|v[01]|a[0-3]|t[0-9]|s[0-7]|k[01]|gp|sp|fp|ra)'
    IDENTIFIER = r'[a-z_]+'
    NUMBER = r'-?\d+'
    
    COMMA = r','
    COLON = r':'
    SEMI = r';'
    OPEN_PAREN = r'\('
    CLOSE_PAREN = r'\)'

    @classmethod
    def items(cls) -> Iterable[tuple[str, str]]:
        for name, value in vars(cls).items():
            if not isinstance(value, Tokens):
                continue
            yield name, value.value

    @classmethod
    def keys(cls) -> Iterable[str]:
        for name, _ in cls.items():
            yield name

