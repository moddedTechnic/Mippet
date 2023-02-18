from __future__ import annotations

from abc import ABC, abstractmethod
from collections import defaultdict, OrderedDict
from dataclasses import dataclass, field
from functools import partial
import warnings
from warnings import warn


class Node(ABC):
    def register(self, ctxt: Context) -> Context:
        return ctxt

    @abstractmethod
    def construct(self, ctxt: Context) -> str:
        raise NotImplemented()


@dataclass
class CommentNode(Node):
    comment: str

    def construct(self, ctxt: Context) -> str:
        return f'# {self.comment}'


@dataclass
class DocCommentNode(Node):
    item: IdentifierNode
    comments: list[CommentNode]
    
    def construct(self, ctxt: Context) -> str:
        if not self.comments:
            return ''
        return construct([
            f'\n## {construct(self.item, ctxt)}',
            self.comments,
            '##',
        ], ctxt)


@dataclass
class NumberNode(Node):
    value: int

    def construct(self, ctxt: Context) -> str:
        return str(self.value)


@dataclass
class StringNode(Node):
    value: str

    def construct(self, ctxt: Context) -> str:
        return f'"{self.value}"'


@dataclass
class ArrayNode(Node):
    value: list[NumberNode]

    def construct(self, ctxt: Context) -> str:
        return ', '.join(construct(v, ctxt) for v in self.value)


@dataclass(eq=True, frozen=True)
class IdentifierNode(Node):
    name: str

    def register(self, ctxt: Context) -> Context:
        ctxt.symbols[self] += 1
        return super().register(ctxt)

    def construct(self, ctxt: Context) -> str:
        return self.name


@dataclass(frozen=True, eq=True)
class RegisterNode(Node):
    reg: str

    def construct(self, ctxt: Context) -> str:
        if self.reg == '$0':
            return '$zero'
        return self.reg

    @classmethod
    @property
    def v0(cls) -> RegisterNode:
        return cls('$v0')

    @classmethod
    @property
    def v1(cls) -> RegisterNode:
        return cls('$v1')


    @classmethod
    @property
    def sp(cls) -> RegisterNode:
        return cls('$sp')

    @classmethod
    @property
    def ra(cls) -> RegisterNode:
        return cls('$ra')


@dataclass
class PointerNode(Node):
    base: RegisterNode
    offset: NumberNode

    def construct(self, ctxt: Context) -> str:
        return f'{construct(self.offset, ctxt)}({construct(self.base, ctxt)})'


@dataclass(eq=True, frozen=True)
class LabelNode(Node):
    name: IdentifierNode

    def register(self, ctxt: Context) -> Context:
        if self.name not in ctxt.symbols:
            ctxt.symbols[self.name] = 0
        return super().register(ctxt)

    def construct(self, ctxt: Context) -> str:
        return f'\n{construct(self.name, ctxt)}:'


class UnusedSymbolWarning(UserWarning):
    pass


@dataclass()
class Context:
    procedures: dict[str, OrderedDict[str, RegisterNode | PointerNode]] = field(default_factory=partial(defaultdict, list), init=False)
    symbols: defaultdict[IdentifierNode, int] = field(default_factory=partial(defaultdict, int), init=False)

    def validate(self) -> None:
        warnings.simplefilter('always', UnusedSymbolWarning)
        for symbol, count in self.symbols.items():
            if count != 0:
                continue
            if symbol.name.startswith('_'):
                continue
            if symbol.name in {'main'}:
                continue
            warn(f'{symbol.name} is unused', UnusedSymbolWarning)


def register(ast, ctxt: Context | None = None) -> Context:
    if ctxt is None:
        ctxt = Context()
    if isinstance(ast, list):
        for n in ast:
            ctxt = register(n, ctxt)
        return ctxt
    return ast.register(ctxt)


def construct(ast, ctxt: Context) -> str:
    if isinstance(ast, list):
        return '\n'.join(construct(n, ctxt) for n in ast)
    if isinstance(ast, str):
        return ast
    return ast.construct(ctxt)

