from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .node import Node, IdentifierNode, NumberNode, PointerNode, RegisterNode, construct

__dir__ = Path(__file__).parent
root = __dir__.parent


@dataclass
class Context:
    stack: list[tuple[RegisterNode, ...]] = field(default_factory=list, init=False)

    def spill(self, *registers: RegisterNode):
        self.stack.append(registers)
        return [
            AddIntegerInstruction(RegisterNode.sp, RegisterNode.sp, NumberNode(-4 * len(registers))),
        ] + [
            StoreWordInstruction(PointerNode(RegisterNode.sp, NumberNode(i * 4)), r)
            for i, r in enumerate(registers, 1)
        ]

    def unspill(self, registers: tuple[RegisterNode, ...] | None = None):
        if registers is None:
            registers = self.stack.pop()
        return [
            LoadWordInstruction(r, PointerNode(RegisterNode.sp, NumberNode(i * 4)))
            for i, r in enumerate(registers, 1)
        ] + [
            AddIntegerInstruction(RegisterNode.sp, RegisterNode.sp, NumberNode(4 * len(registers))),
        ]
     

class InstructionNode(Node, ABC):
    _subclasses: dict[str, type[InstructionNode]] = {}
    __mneumonic__: str | None = None

   
    def __init_subclass__(cls, *, mneumonic: str, **kwargs) -> None:
        print(mneumonic)
        cls._subclasses[mneumonic] = cls
        cls.__mneumonic__ = mneumonic
        return super().__init_subclass__(**kwargs)

    @property
    def mneumonic(cls) -> str:
        if cls.__mneumonic__ is None:
            raise NotImplementedError(f'{type(cls).__name__} is abstract')
        return cls.__mneumonic__

    @property
    def arguments(self) -> Iterable[Node]:
        return []

    def construct(self) -> str:
        return f'    {self.mneumonic} ' + ', '.join(a.construct() for a in self.arguments)

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        return cls()

    @classmethod
    def parse(cls, mneumonic: IdentifierNode, arguments: list[Node]) -> InstructionNode:
        instruction_cls = cls._subclasses.get(mneumonic.name, GenericInstruction)
        if instruction_cls is GenericInstruction:
            arguments.insert(0, mneumonic)
        return instruction_cls.parse_arguments(arguments)


@dataclass
class GenericInstruction(InstructionNode, mneumonic=''):
    _arguments: list[Node]

    @property
    def arguments(self) -> Iterable[Node]:
        return self._arguments

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        mneumonic, *arguments = arguments
        self = cls(arguments)
        assert isinstance(mneumonic, IdentifierNode)
        self.__mneumonic__ = mneumonic.name
        return self
 

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
class JumpRegisterInstruction(InstructionNode, mneumonic='jr'):
    target: RegisterNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.target]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        target = arguments[0]
        if not isinstance(target, RegisterNode):
            raise ValueError('`jr` expected a register as the parameter')
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
        return [self.source, self.destination]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        source, destination = arguments
        if not isinstance(source, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `lw`')
        if not isinstance(destination, PointerNode):
            raise ValueError(f'Expected a pointer as the second argument to `lw`')
        return cls(destination, source)


@dataclass
class MathIntegerInstruction(InstructionNode, mneumonic=''):
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
            raise ValueError(f'Expected a register as the first argument to `{cls.mneumonic}`')
        if not isinstance(source, RegisterNode):
            raise ValueError(f'Expected a register as the second argument to `{cls.mneumonic}`')
        if not isinstance(value, NumberNode):
            raise ValueError(f'Expected an integer as the third argument to `{cls.mneumonic}`')
        return cls(destination, source, value)


@dataclass
class MathRegisterInstruction(InstructionNode, mneumonic=''):
    destination: RegisterNode
    source: RegisterNode
    value: RegisterNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.destination, self.source, self.value]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        destination, source, value = arguments
        if not isinstance(destination, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `{cls.mneumonic}`')
        if not isinstance(source, RegisterNode):
            raise ValueError(f'Expected a register as the second argument to `{cls.mneumonic}`')
        if not isinstance(value, RegisterNode):
            raise ValueError(f'Expected an register as the third argument to `{cls.mneumonic}`')
        return cls(destination, source, value)

class AddIntegerInstruction(MathIntegerInstruction, mneumonic='addi'):
    pass


class MultiplyIntegerInstruction(MathIntegerInstruction, mneumonic='muli'):
    def construct(self) -> str:
        return construct([
            LoadIntegerInstruction(self.destination, self.value),
            MultiplyRegisterInstruction(self.destination, self.destination, self.source),
        ])


class MultiplyRegisterInstruction(MathRegisterInstruction, mneumonic='mul'):
    pass


@dataclass
class CallInstruction(InstructionNode, mneumonic='call'):
    proc: IdentifierNode

    def construct(self) -> str:
        ctxt = Context()
        return construct([
            ctxt.spill(RegisterNode.ra),
            JumpAndLinkInstruction(self.proc),
            ctxt.unspill(),
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
        ctxt = Context()
        return '\n'.join(
            filter(
                lambda x: x.strip(),
                construct([
                    ctxt.spill(RegisterNode.v0),
                    LoadIntegerInstruction(RegisterNode.v0, NumberNode(syscall_id)),
                    SyscallInstruction(),
                    ctxt.unspill(),
                ]).splitlines()
            )
        )

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        if len(arguments) == 0:
            return cls()
        identifier = arguments[0]
        if not isinstance(identifier, IdentifierNode):
            raise ValueError(f'Expected an identifier if `syscall` is to be given an argument')
        return cls(identifier)










