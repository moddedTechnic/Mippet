from __future__ import annotations

from abc import ABC, abstractmethod
from collections import OrderedDict
from dataclasses import dataclass


class Node(ABC):
    @abstractmethod
    def construct(self) -> str:
        raise NotImplemented()


@dataclass
class NumberNode(Node):
    value: int

    def construct(self) -> str:
        return str(self.value)


@dataclass
class IdentifierNode(Node):
    name: str

    def construct(self) -> str:
        return self.name


@dataclass(frozen=True)
class RegisterNode(Node):
    register: str

    def construct(self) -> str:
        if self.register == '$0':
            return '$zero'
        return self.register

    @classmethod
    @property
    def v0(cls) -> RegisterNode:
        return cls('$v0')

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

    def construct(self) -> str:
        return f'{construct(self.offset)}({construct(self.base)})'


@dataclass
class LabelNode(Node):
    name: IdentifierNode

    def construct(self) -> str:
        return f'\n{construct(self.name)}:'


@dataclass
class ProcedureNode(Node):
    name: IdentifierNode
    parameters: OrderedDict[str, Node]

    def construct(self) -> str:
        return construct([
            LabelNode(self.name)
        ])


@dataclass
class SectionNode(Node):
    typ: str
    body: list[Node]

    def construct(self) -> str:
        return f'{self.typ}\n' + construct(self.body) + '\n'


def construct(ast) -> str:
    if isinstance(ast, list):
        return '\n'.join(construct(n) for n in ast)
    return ast.construct()

