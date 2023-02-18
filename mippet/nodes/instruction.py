from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

from .node import Context, Node, IdentifierNode, NumberNode, PointerNode, RegisterNode, construct, register

__dir__ = Path(__file__).parent
root = __dir__.parent


@dataclass
class SpillContext:
    ctxt: Context
    stack: list[tuple[RegisterNode, ...]] = field(default_factory=list, init=False)

    def spill(self, *registers: RegisterNode, depth: int = 0):
        if not registers:
            return ''
        self.stack.append(registers)
        if not depth:
            return construct([
                AddIntegerInstruction(RegisterNode.sp, RegisterNode.sp, NumberNode(len(registers) * -4)),
                [
                    StoreWordInstruction(PointerNode(RegisterNode.sp, NumberNode(i * 4)), r)
                    for i, r in enumerate(registers, 1)
                ]
            ], self.ctxt)
        if len(registers) > 1:
            return construct([
                self.spill(registers[-1], depth=depth),
                self.spill(*registers[:-1], depth=depth),
            ], self.ctxt)
        register = registers[0]
        return construct([
            AddIntegerInstruction(RegisterNode.sp, RegisterNode.sp, NumberNode(-4)),
            [
                [
                    LoadWordInstruction(RegisterNode('$t9'), PointerNode(RegisterNode.sp, NumberNode((i+1) * 4))),
                    StoreWordInstruction(PointerNode(RegisterNode.sp, NumberNode(i*4)), RegisterNode('$t9')),
                ]
                for i in range(1, depth + 1)
            ],
            StoreWordInstruction(PointerNode(RegisterNode.sp, NumberNode((depth+1) * 4)), register),
        ], self.ctxt)

    def unspill(self, registers: tuple[RegisterNode, ...] | None = None):
        if registers is None:
            registers = self.stack.pop()
        return construct([
            LoadWordInstruction(r, PointerNode(RegisterNode.sp, NumberNode(i * 4)))
            for i, r in enumerate(registers, 1)
        ] + [
            AddIntegerInstruction(RegisterNode.sp, RegisterNode.sp, NumberNode(4 * len(registers))),
        ], self.ctxt)
     

class InstructionNode(Node, ABC):
    _subclasses: dict[str, type[InstructionNode]] = {}
    __mneumonic__: str | None = None

   
    def __init_subclass__(cls, *, mneumonic: str, **kwargs) -> None:
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

    def register(self, ctxt: Context) -> Context:
        for arg in self.arguments:
            ctxt = register(arg, ctxt)
        return super().register(ctxt)

    def construct(self, ctxt: Context) -> str:
        return f'    {self.mneumonic} ' + ', '.join(a.construct(ctxt) for a in self.arguments)

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
    reg: RegisterNode = field()
    value: NumberNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.reg, self.value]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        reg, value = arguments
        if not isinstance(reg, RegisterNode):
            raise ValueError(f'Expected a reg as the first argument to `li`')
        if not isinstance(value, NumberNode):
            raise ValueError(f'Expected an integer as the second argument to `li`')
        return cls(reg, value)


@dataclass
class LoadWordInstruction(InstructionNode, mneumonic='lw'):
    destination: RegisterNode
    source: PointerNode | IdentifierNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.destination, self.source]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        destination, source = arguments
        if not isinstance(destination, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `lw`')
        if not isinstance(source, (PointerNode, IdentifierNode)):
            raise ValueError(f'Expected a pointer or identifier as the second argument to `lw`, got `{type(source).__name__}`')
        return cls(destination, source)


@dataclass
class StoreWordInstruction(InstructionNode, mneumonic='sw'):
    destination: PointerNode | IdentifierNode
    source: RegisterNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.source, self.destination]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        source, destination = arguments
        if not isinstance(source, RegisterNode):
            raise ValueError(f'Expected a register as the first argument to `lw`')
        if not isinstance(destination, (PointerNode, IdentifierNode)):
            raise ValueError(f'Expected a pointer as the second argument to `lw`')
        return cls(destination, source)


@dataclass
class MoveInstruction(InstructionNode, mneumonic='move'):
    source: RegisterNode
    destination: RegisterNode

    @property
    def arguments(self) -> Iterable[Node]:
        return [self.destination, self.source]

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        destination, source = arguments
        if not isinstance(destination, RegisterNode):
            raise ValueError('`move` expected a register as the first argument')
        if not isinstance(source, RegisterNode):
            raise ValueError('`move` expected a register as the second argument')
        return cls(source, destination)


@dataclass
class PushInstuction(InstructionNode, mneumonic='push'):
    source: RegisterNode

    def construct(self, ctxt: Context) -> str:
        return construct(SpillContext(ctxt).spill(self.source), ctxt)

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        source = arguments[0]
        if not isinstance(source, RegisterNode):
            raise ValueError(f'`push` expects a pointer as the argument')
        return cls(source)


@dataclass
class PopInstruction(InstructionNode, mneumonic='pop'):
    destination: RegisterNode | None = None

    def construct(self, ctxt: Context) -> str:
        if not self.destination:
            return construct(AddIntegerInstruction(RegisterNode.sp, RegisterNode.sp, NumberNode(4)), ctxt)
        return construct(SpillContext(ctxt).unspill((self.destination,)), ctxt)

    @classmethod
    def parse_arguments(cls, arguments: list[Node]) -> InstructionNode:
        if len(arguments) == 0:
            return cls()
        destination = arguments[0]
        if not isinstance(destination, RegisterNode):
            raise ValueError(f'`pop` expects a pointer as the argument')
        return cls(destination)


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
    """$D = $S * value
    For technical reasons, $D cannot be $t9
    """
    def construct(self, ctxt: Context) -> str:
        return construct([
            LoadIntegerInstruction(RegisterNode('$t9'), self.value),
            MultiplyRegisterInstruction(self.destination, RegisterNode('$t9'), self.source),
        ], ctxt)


class MultiplyRegisterInstruction(MathRegisterInstruction, mneumonic='mul'):
    pass


class ModuloIntegerInstruction(MathIntegerInstruction, mneumonic='modi'):
    def construct(self, ctxt: Context) -> str:
        return construct([
            LoadIntegerInstruction(RegisterNode('$t9'), self.value),
            ModuloRegisterInstruction(self.destination, self.source, RegisterNode('$t9')),
        ], ctxt)


class ModuloRegisterInstruction(MathRegisterInstruction, mneumonic='mod'):
    def construct(self, ctxt: Context) -> str:
        return construct([
            GenericInstruction.parse_arguments([IdentifierNode('div'), self.source, self.value]),
            GenericInstruction.parse_arguments([IdentifierNode('mfhi'), self.destination]),
        ], ctxt)


@dataclass
class CallInstruction(InstructionNode, mneumonic='call'):
    proc: IdentifierNode

    def construct(self, ctxt: Context) -> str:
        parameters = ctxt.procedures[self.proc.name]
        spill_depth = sum(1 for p in parameters.values() if isinstance(p, PointerNode) and p.base == RegisterNode.sp)
        spill_ctxt = SpillContext(ctxt)
        # TODO: need to check what we're calling and get spill-preservation depth
        return construct([
            spill_ctxt.spill(RegisterNode.ra, depth=spill_depth),
            JumpAndLinkInstruction(self.proc),
            spill_ctxt.unspill(),
        ], ctxt)

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

    def construct(self, ctxt: Context) -> str:
        if self.identifier is None:
            return super().construct(ctxt)
        syscall_name = self.identifier.name
        syscall_id = self.SYSCALLS.get(syscall_name)
        if syscall_id is None:
            raise ValueError(f'Unknown syscall {syscall_name}')
        spill_ctxt = SpillContext(ctxt)
        return '\n'.join(
            filter(
                lambda x: x.strip(),
                construct([
                    spill_ctxt.spill(RegisterNode.v0),
                    LoadIntegerInstruction(RegisterNode.v0, NumberNode(syscall_id)),
                    SyscallInstruction(),
                    StoreWordInstruction(IdentifierNode('_return'), RegisterNode.v0),
                    spill_ctxt.unspill(),
                ], ctxt).splitlines()
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










