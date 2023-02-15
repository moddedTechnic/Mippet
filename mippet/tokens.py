from enum import Enum
from typing import Iterable


class Tokens(Enum):
    KWD_PROC = r'proc'

    DOC_COMMENT = r'##'
    COMMENT = r'#.*'

    TEXT_SECTION = r'\.text'
    KTEXT_SECTION = r'\.ktext'
    DATA_SECTION = r'\.data'
    KDATA_SECTION = r'\.kdata'
    GLOBAL_SECTION = r'\.globa?l'
    EXCEPTION_SECTION = r'\.exception'
    ASCII_SECTION = r'\.asciiz?'
    WORD_SECTION = r'\.word'
    SECTION = r'\.[a-z]+'

    REGISTER = r'\$(zero|at|v[01]|a[0-3]|t[0-9]|s[0-7]|k[01]|gp|sp|fp|ra)'
    IDENTIFIER = r'[a-zA-Z_][a-zA-Z_\d]*'
    STRING = r'"(?:[^"\\]|\\.)*"'
    HEX_NUMBER = r'0x[\da-fA-F]+'
    NUMBER = r'-?\d+'
    
    COMMA = r','
    COLON = r':'
    SEMI = r';'
    BANG = r'!'
    EQUAL = r'='
    OPEN_PAREN = r'\('
    CLOSE_PAREN = r'\)'
    OPEN_BRACK = r'\['
    CLOSE_BRACK = r'\]'

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

