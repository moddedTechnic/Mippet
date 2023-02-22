from collections import OrderedDict
from dataclasses import dataclass, field

from .instruction import CallInstruction, SpillContext, InstructionNode, JumpRegisterInstruction, SyscallInstruction
from .node import *


PROCEDURE_SPILLS = tuple(RegisterNode(f'$s{i}') for i in range(8))


@dataclass
class SectionNode(Node):
    typ: str
    body: list[Node]

    def register(self, ctxt: Context) -> Context:
        return register(self.body, ctxt)

    def construct(self, ctxt: Context) -> str:
        return construct([
            self.typ,
            LabelNode(IdentifierNode('entry')),
            CallInstruction(IdentifierNode('main')),
            SyscallInstruction(IdentifierNode('halt')),
            self.body,
            '\n'
        ], ctxt)


@dataclass
class KernelTextSectionNode(SectionNode):
    address: NumberNode
    typ: str = field(default='.ktext', init=False)

    def construct(self, ctxt: Context) -> str:
        return construct([
            f'{self.typ} {construct(self.address, ctxt)}',
            self.body,
            '\n',
        ], ctxt)


class DataNode(Node, ABC):
    pass


@dataclass
class StringDataDefinitionNode(DataNode):
    data: StringNode
    is_null_terminated: bool = True

    def construct(self, ctxt: Context) -> str:
        return construct([
            '.asciiz' if self.is_null_terminated else '.ascii',
            self.data,
        ], ctxt)


@dataclass
class WordDataDefinitionNode(DataNode):
    data: NumberNode | ArrayNode

    def construct(self, ctxt: Context) -> str:
        return construct([
            '.word',
            self.data,
        ], ctxt)


@dataclass
class DataSectionNode(SectionNode):
    typ: str = field(default='.data', init=False)
    body: dict[LabelNode, DataNode]

    def register(self, ctxt: Context) -> Context:
        for k, v in self.body.items():
            ctxt = register(k, ctxt)
            ctxt = register(v, ctxt)
        return ctxt

    def construct(self, ctxt: Context) -> str:
        return construct(
            [
                '.data',
                LabelNode(IdentifierNode('_return')),
                WordDataDefinitionNode(NumberNode(0)),
            ] + [list(x) for x in self.body.items()],
            ctxt
        )


@dataclass
class ProcedureNode(Node):
    name: IdentifierNode
    parameters: OrderedDict[str, RegisterNode | PointerNode]
    documentation: list[DocCommentNode] = field(default_factory=list)

    def register(self, ctxt: Context) -> Context:
        ctxt.procedures[self.name.name] = self.parameters
        if self.name not in ctxt.symbols:
            ctxt.symbols[self.name] = 0
        return super().register(ctxt)

    def construct(self, ctxt: Context) -> str:
        _construct = partial(construct, ctxt=ctxt)
        doc_comments = []
        for doc in self.documentation:
            doc_comments.extend(doc.comments)
        if self.parameters:
            doc_comments.append(CommentNode(''))
            doc_comments.extend([
                CommentNode(f'{construct(r, ctxt)}: {name}')
                for name, r in self.parameters.items()
            ])
        spill_ctxt = SpillContext(ctxt)
        documentation = _construct(doc_comments)
        label = _construct(LabelNode(self.name))
        if documentation:
            label = label.lstrip()
            documentation = '\n' + documentation
        spill = _construct([
            spill_ctxt.spill(
                *PROCEDURE_SPILLS,
                depth=len([
                    p for p in self.parameters.values()
                    if isinstance(p, PointerNode) and p.base == RegisterNode.sp
                ])
            )
        ])
        return '\n'.join(
            filter(
                lambda x: x.strip(),
                [documentation, label, spill],
            )
        )


class ReturnInstruction(InstructionNode, mneumonic='ret'):
    def construct(self, ctxt: Context) -> str:
        return construct([
            SpillContext(ctxt).unspill(PROCEDURE_SPILLS),
            JumpRegisterInstruction(RegisterNode.ra),
        ], ctxt)














