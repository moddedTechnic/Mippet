from collections import OrderedDict
from dataclasses import dataclass, field

from .instruction import Context, InstructionNode, JumpRegisterInstruction
from .node import *


PROCEDURE_SPILLS = tuple(RegisterNode(f'$s{i}') for i in range(8))


@dataclass
class ProcedureNode(Node):
    name: IdentifierNode
    parameters: OrderedDict[str, RegisterNode | PointerNode]
    documentation: list[DocCommentNode] = field(default_factory=list)

    def construct(self) -> str:
        doc_comments = []
        for doc in self.documentation:
            doc_comments.extend(doc.comments)
        if self.parameters:
            doc_comments.append(CommentNode(''))
            doc_comments.extend([
                CommentNode(f'{construct(r)}: {name}')
                for name, r in self.parameters.items()
            ])
        ctxt = Context()
        documentation = construct(doc_comments)
        label = construct(LabelNode(self.name))
        if documentation:
            label = label.lstrip()
            documentation = '\n' + documentation
        spill = construct(ctxt.spill(*PROCEDURE_SPILLS))
        return '\n'.join(
            filter(
                lambda x: x.strip(),
                [documentation, label, spill],
            )
        )


class ReturnInstruction(InstructionNode, mneumonic='ret'):
    def construct(self) -> str:
        return construct([
            Context().unspill(PROCEDURE_SPILLS),
            JumpRegisterInstruction(RegisterNode.ra),
        ])














