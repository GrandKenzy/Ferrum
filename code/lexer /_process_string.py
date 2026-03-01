from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from codegen.lexer import Lexer

from codegen.obj.tokens import TokenType

def view(self: Lexer, char: str):
    count = 1
    while self.peek() == char:
        self.advance()
        count += 1

    if count == 2:
        self.put(TokenType.STRING, "")
        return

    is_triple = count >= 3
    content = ""

    if is_triple and count > 3:
        content += char * (count - 3)

    ttype = TokenType.DOCSTRING if is_triple else TokenType.STRING

    while True:
        curr = self.advance()

        if curr == "":
            self.error(
                f"Fin de archivo sin cerrar el {'docstring' if is_triple else 'string'}"
            )

        if curr == '\n':
            self.line += 1
            self.linepos = 0
            if not is_triple:
                self.error("Salto de línea no permitido en string simple")

        if curr == char:
            if is_triple:
                if self.peek() == char:
                    self.advance()
                    if self.peek() == char:
                        self.advance()
                        self.put(ttype, content)
                        return
                    else:
                        content += char * 2
                else:
                    content += char
            else:
                self.put(ttype, content)
                return

        elif curr == '\\':
            next_c = self.advance()
            if next_c == "":
                self.error("Secuencia de escape incompleta al final del archivo")
            if next_c == char or next_c == '\\':
                content += next_c
            else:
                content += '\\' + next_c
        else:
            content += curr
