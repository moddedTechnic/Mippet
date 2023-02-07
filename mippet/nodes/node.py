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


@dataclass
class RegisterNode(Node):
    register: str

    def construct(self) -> str:
        return self.register


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

