from collections import OrderedDict
from dataclasses import dataclass, field

from .instruction import Context, InstructionNode
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
        return ''.join(map(construct, [
            DocCommentNode(self.name, doc_comments),
            LabelNode(self.name),
            ctxt.spill(*PROCEDURE_SPILLS),
        ]))


class ReturnInstruction(InstructionNode, mneumonic='ret'):
    def construct(self) -> str:
        return construct([
            Context().unspill(PROCEDURE_SPILLS),
            JumpRegisterInstruction(RegisterNode.ra),
        ])


