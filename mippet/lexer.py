from rply import LexerGenerator

from .tokens import Tokens

__all__ = 'lex',


lg = LexerGenerator()

for name, value in Tokens.items():
    lg.add(name, value)
lg.ignore(r'[ \t\r\n]')

lexer = lg.build()

lex = lexer.lex

