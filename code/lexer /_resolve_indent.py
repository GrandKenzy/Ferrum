from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from codegen.lexer import Lexer

from codegen.obj.tokens import TokenType

def view(self: Lexer):
    indent = 0
    while self.peek() == ' ':
        indent += 1
        self.advance()

    if self.peek() == '\n':
        return

    current = self.indent_stack[-1]

    if indent == current:
        return

    if indent > current:
        self.indent_stack.append(indent)
        self.put(TokenType.INDENT, indent)
        return

    if indent < current:
        if indent not in self.indent_stack:
            self.error(f"Indentación inválida: nivel {indent} no coincide con ningún bloque abierto")

        while self.indent_stack[-1] > indent:
            self.indent_stack.pop()
            self.put(TokenType.DEDENT, indent)
