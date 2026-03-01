from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from codegen.lexer import Lexer

from codegen.obj.tokens import TokenType

def view(self: Lexer, char: str):
    if char == '&':
        if self.peek() == '&':
            self.put(TokenType.AND, '&&')
            self.advance()
        elif self.peek() == '=':
            self.put(TokenType.ASSIGN_AND, '&=')
            self.advance()
        else:
            self.put(TokenType.BAND, '&')
    elif char == '|':
        if self.peek() == '|':
            self.put(TokenType.OR, '||')
            self.advance()
        elif self.peek() == '=':
            self.put(TokenType.ASSIGN_OR, '|=')
            self.advance()
        else:
            self.put(TokenType.BOR, '|')
    elif char == '!':
        if self.peek() == '=':
            self.put(TokenType.UNEQUAL, '!=')
            self.advance()
        else:
            self.put(TokenType.NOT, '!')
    elif char == '^':
        if self.peek() == '=':
            self.put(TokenType.ASSIGN_XOR, '^=')
            self.advance()
        else:
            self.put(TokenType.BXOR, '^')
    elif char == '~':
        self.put(TokenType.BNOT, '~')
    else:
        self.error(f"Cáracter de operador lógico no reconocido '{char}'")
