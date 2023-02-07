from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .node import Node, IdentifierNode, NumberNode, PointerNode, RegisterNode, construct

__dir__ = Path(__file__).parent
root = __dir__.parent


class InstructionNode(Node, ABC):
    _subclasses: dict[str, type[InstructionNode]] = {}
    __mneumonic__: str | None = None

   
    def __init_subclass__(cls, *, mneumonic: str, **kwargs) -> None:
        cls._subclasses[mneumonic] = cls
        cls.__mneumonic__ = mneumonic
        return super().__init_subclass__(**kwargs)

    @property
    def mneumonic(self) -> str:
        if self.__mneumonic__ is None:
            raise NotImplementedError(f'{type(self).__name__} is abstract')
        return self.__mneumonic__

    @property
    def arguments(self) -> Iterable[Node]:
        return []

    def construct(self) -> str:
        return f'    {self.mneumonic} ' + ', '.join(a.construct() for a in self.arguments)

    @classmethod
    @abstractmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        raise NotImplementedError()

    @classmethod
    def parse(cls, mneumonic: IdentifierNode, arguments: list[Node]) -> InstructionNode:
        instruction_cls = cls._subclasses.get(mneumonic.name)
        if instruction_cls is None:
            raise ValueError(f'Unknown instruction "{mneumonic}"')
        return instruction_cls.parse_arguments(arguments)
 

@dataclass
class JumpInstruction(InstructionNode, mneumonic='j'):
    target: IdentifierNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.target]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        target = arguments[0]
        if not isinstance(target, IdentifierNode):
            raise ValueError(f'Expected an identifier as the argument to `j`')
        return cls(target)


@dataclass
class JumpAndLinkInstruction(InstructionNode, mneumonic='jal'):
    target: IdentifierNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.target]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        target = arguments[0]
        if not isinstance(target, IdentifierNode):
            raise ValueError(f'`jal` expected an identifier as the first parameter')
        return cls(target)


@dataclass
class LoadIntegerInstruction(InstructionNode, mneumonic='li'):
    register: RegisterNode = field()
    value: NumberNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.register, self.value]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        register, value = arguments
        if not isinstance(register, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `li`')
        if not isinstance(value, NumberNode):
            raise ValueError(f'Expected an integer as the second argument to `li`')
        return cls(register, value)


@dataclass
class LoadWordInstruction(InstructionNode, mneumonic='lw'):
    destination: RegisterNode
    source: PointerNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.destination, self.source]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        destination, source = arguments
        if not isinstance(destination, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `lw`')
        if not isinstance(source, PointerNode):
            raise ValueError(f'Expected a pointer as the second argument to `lw`')
        return cls(destination, source)


@dataclass
class StoreWordInstruction(InstructionNode, mneumonic='sw'):
    destination: PointerNode
    source: RegisterNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.destination, self.source]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        source, destination = arguments
        if not isinstance(source, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `lw`')
        if not isinstance(destination, PointerNode):
            raise ValueError(f'Expected a pointer as the second argument to `lw`')
        return cls(destination, source)


@dataclass
class AddIntegerInstruction(InstructionNode, mneumonic='addi'):
    destination: RegisterNode
    source: RegisterNode
    value: NumberNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.destination, self.source, self.value]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        destination, source, value = arguments
        if not isinstance(destination, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `addi`')
        if not isinstance(source, RegisterNode):
            raise ValueError(f'Expected a register as the second argument to `addi`')
        if not isinstance(value, NumberNode):
            raise ValueError(f'Expected an integer as the third argument to `addi`')
        return cls(destination, source, value)


@dataclass
class CallInstruction(InstructionNode, mneumonic='call'):
    proc: IdentifierNode

    def construct(self) -> str:
        return construct([
            AddIntegerInstruction(RegisterNode('$sp'), RegisterNode('$sp'), NumberNode(-4)),
            StoreWordInstruction(PointerNode(RegisterNode('$sp'), NumberNode(4)), RegisterNode('$ra')),
            JumpAndLinkInstruction(self.proc),
            LoadWordInstruction(RegisterNode('$ra'), PointerNode(RegisterNode('$sp'), NumberNode(4))),
            AddIntegerInstruction(RegisterNode('$sp'), RegisterNode('$sp'), NumberNode(4)),
        ])

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        proc = arguments[0]
        if not isinstance(proc, IdentifierNode):
            raise ValueError(f'`call` expects a procedure to call')
        return cls(proc)


@dataclass
class SyscallInstruction(InstructionNode, mneumonic='syscall'):
    identifier: IdentifierNode | None = None

    SYSCALLS = {}
    for line in (root / 'syscalls.txt').open('r'):
        name, id, *_ = line.split(' ')
        SYSCALLS[name] = id

    def construct(self) -> str:
        if self.identifier is None:
            return super().construct()
        syscall_name = self.identifier.name
        syscall_id = self.SYSCALLS.get(syscall_name)
        if syscall_id is None:
            raise ValueError(f'Unknown syscall {syscall_name}')
        return construct([
            AddIntegerInstruction(RegisterNode('$sp'), RegisterNode('$sp'), NumberNode(-4)),
            StoreWordInstruction(PointerNode(RegisterNode('$sp'), NumberNode(4)), RegisterNode('$v0')),
            LoadIntegerInstruction(RegisterNode('$v0'), NumberNode(syscall_id)),
            SyscallInstruction(),
            LoadWordInstruction(RegisterNode('$v0'), PointerNode(RegisterNode('$sp'), NumberNode(4))),
            AddIntegerInstruction(RegisterNode('$sp'), RegisterNode('$sp'), NumberNode(4)),
        ])

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        if len(arguments) == 0:
            return cls()
        identifier = arguments[0]
        if not isinstance(identifier, IdentifierNode):
            raise ValueError(f'Expected an identifier if `syscall` is to be given an argument')
        return cls(identifier)










