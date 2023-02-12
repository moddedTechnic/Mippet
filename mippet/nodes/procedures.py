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
class ProcedureNode(Node):
    name: IdentifierNode
    parameters: OrderedDict[str, RegisterNode | PointerNode]
    documentation: list[DocCommentNode] = field(default_factory=list)

    def register(self, ctxt: Context) -> Context:
        ctxt.procedures[self.name.name] = self.parameters
        return super().register(ctxt)

    def construct(self, ctxt: Context) -> str:
        print(self.name)
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
        documentation = construct(doc_comments, ctxt)
        label = construct(LabelNode(self.name), ctxt)
        if documentation:
            label = label.lstrip()
            documentation = '\n' + documentation
        spill = construct(
            spill_ctxt.spill(
                *PROCEDURE_SPILLS,
                depth=len([
                    p for p in self.parameters.values()
                    if isinstance(p, PointerNode) and p.base == RegisterNode.sp
                ])
            ),
            ctxt
        )
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














