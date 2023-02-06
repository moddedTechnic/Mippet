from typing import TypeVar

from .nodes import *

VisitNode = TypeVar('VisitNode', Node, list[Node])


SYSCALLS = {
    'print_int': 1,
    'print_float': 2,
    'print_double': 3,
    'print_string': 4,
    'read_int': 5,
    'read_float': 6,
    'read_double': 7,
    'read_string': 8,
    'sbrk': 9,
    'exit': 10,
}


class Preprocessor:
    def transform(self, ast: Node):
        return self.visit(ast)

    def visit(self, node: VisitNode) -> VisitNode:
        if isinstance(node, list):
            result: list[Node] = []
            for n in node:
                r = self.visit(n)
                if isinstance(r, list):
                    result.extend(r)
                else:
                    result.append(r)
            return result
        typ = type(node).__name__
        handler = Preprocessor.__dict__.get(f'visit_{typ}')
        if handler is None:
            return node
        return handler(self, node)

    def visit_SectionNode(self, node: SectionNode):
        return SectionNode(node.typ, self.visit(node.body))

    def visit_InstructionNode(self, node: InstructionNode):
        if node.mneumonic == 'syscall':
            return self.visit_InstructionNode_syscall(node)
        return node

    def visit_InstructionNode_syscall(self, node: InstructionNode):
        args = node.arguments
        if not args:
            return node
        if not isinstance(args[0], IdentifierNode):
            raise TypeError('Expected the name of a syscall')
        syscall = args[0].name
        syscall_id = SYSCALLS.get(syscall)
        if syscall_id is None:
            raise ValueError(f'Unknown syscall {syscall}')
        # TODO: spill $v0 around syscall
        new_instructions = [
            InstructionNode('lw', [RegisterNode('$v0'), NumberNode(syscall_id)]),
            InstructionNode('syscall', []),
        ]
        return new_instructions


preprocess = Preprocessor().transform

