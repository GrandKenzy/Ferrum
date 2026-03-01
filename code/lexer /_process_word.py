from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from codegen.lexer import Lexer

from codegen.item.keywords import *
from codegen.obj.tokens import TokenType

def view(self: Lexer, char: str):
    name = char
    while self.peek().isalnum() or self.peek() == '_':
        name += self.advance()

    if not name:
        self.error("Identificador vacío o inválido")

    if name in KEYWORDS:
        if name in ('True', 'False'):
            self.put(TokenType.BOOL, name)
        elif name == 'not':
            self.put(TokenType.NOT, 'not')
        elif name == 'and':
            self.put(TokenType.AND, 'and')
        elif name == 'or':
            self.put(TokenType.OR, 'or')
        else:
            self.put(TokenType.KEYWORD, name)
    elif name in TYPES:
        self.put(TokenType.TYPE, name)
    else:
        self.put(TokenType.IDENT, name)
