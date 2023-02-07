from collections import OrderedDict

from rply import ParserGenerator, Token

from .nodes import *
from .tokens import Tokens

__all__ = 'parse',


pg = ParserGenerator(Tokens.keys())


@pg.production('section : SECTION statements')
def section(p):
    return SectionNode(p[0].getstr(), p[1])


@pg.production('statements : statements statement')
def statements(p):
    return [*p[0], p[1]]


@pg.production('statements : statement')
def statements_one(p):
    return [p[0]]


@pg.production('statement : label')
@pg.production('statement : instruction')
@pg.production('statement : procedure')
def statement(p):
    return p[0]


@pg.production('label : identifier COLON')
def label(p):
    return LabelNode(p[0])


@pg.production('instruction : identifier arguments')
def instruction(p):
    return InstructionNode.parse(p[0], p[1])


@pg.production('procedure : KWD_PROC identifier OPEN_PAREN parameters CLOSE_PAREN COLON')
def procedure(p):
    return ProcedureNode(p[1], OrderedDict(p[3]))


@pg.production('arguments : ')
def arguments_zero(p):
    return []


@pg.production('arguments : argument')
def arguments_one(p):
    return [p[0]]


@pg.production('arguments : argument COMMA arguments')
def arguments_many(p):
    return [p[0], *p[2]]


@pg.production('argument : number')
@pg.production('argument : identifier')
@pg.production('argument : register')
@pg.production('argument : pointer')
def argument(p):
    return p[0]


@pg.production('parameters : ')
def parameters_zero(p):
    return []


@pg.production('parameters : parameter')
def parameters_one(p):
    return [p[0]]


@pg.production('parameters : parameter COMMA parameters')
def parameters_many(p):
    return [p[0], *p[1]]


@pg.production('parameter : identifier COLON pointer')
@pg.production('parameter : identifier COLON register')
def parameter(p):
    return p[0].name, p[2]


@pg.production('pointer : number OPEN_PAREN register CLOSE_PAREN')
def pointer(p):
    return PointerNode(p[2], p[0])


@pg.production('number : NUMBER')
def number(p):
    return NumberNode(int(p[0].getstr()))


@pg.production('identifier : IDENTIFIER')
def identifier(p):
    return IdentifierNode(p[0].getstr())


@pg.production('register : REGISTER')
def register(p):
    return RegisterNode(p[0].getstr())


@pg.error
def on_error(bad_token: Token):
    raise SyntaxError(f'Got unexpected {bad_token.name} ({bad_token.getstr()}) at {bad_token.getsourcepos()}')


parser = pg.build()
parse = parser.parse

