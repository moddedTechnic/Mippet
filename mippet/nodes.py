from abc import ABC, abstractmethod
from dataclasses import dataclass


class Node(ABC):
    @abstractmethod
    def construct(self) -> str:
        raise NotImplemented()


@dataclass
class InstructionNode(Node):
    mneumonic: str
    arguments: list[Node]

    def construct(self) -> str:
        return f'    {self.mneumonic} ' + ', '.join(a.construct() for a in self.arguments)


@dataclass
class RegisterNode(Node):
    register: str

    def construct(self) -> str:
        return self.register


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
class LabelNode(Node):
    name: str

    def construct(self) -> str:
        return f'{self.name}:'


@dataclass
class SectionNode(Node):
    typ: str
    body: list[Node]

    def construct(self) -> str:
        return f'{self.typ}\n' + construct(self.body)


def construct(ast: Node | list[Node]) -> str:
    if isinstance(ast, list):
        return '\n'.join(construct(n) for n in ast)
    return ast.construct()

