from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from codegen.lexer import Lexer

from codegen.obj.tokens import TokenType

def view(self: Lexer, char: str):
    if char == '(':
        self.put(TokenType.LPARENT, '(')
    elif char == ')':
        self.put(TokenType.RPARENT, ')')
    elif char == '[':
        self.put(TokenType.LBRACKET, '[')
    elif char == ']':
        self.put(TokenType.RBRACKET, ']')
    elif char == '{':
        self.put(TokenType.LKEY, '{')
    elif char == '}':
        self.put(TokenType.RKEY, '}')
    elif char == '<':
        if self.peek() == '=':
            self.put(TokenType.MINOR_EQUAL, '<=')
            self.advance()
        elif self.peek() == '<':
            self.advance()
            if self.peek() == '=':
                self.put(TokenType.ASSIGN_SHIFT_LEFT, '<<=')
                self.advance()
            else:
                self.put(TokenType.SHIFT_L, '<<')
        else:
            self.put(TokenType.MINOR, '<')
    elif char == '>':
        if self.peek() == '=':
            self.put(TokenType.MAJOR_EQUAL, '>=')
            self.advance()
        elif self.peek() == '>':
            self.advance()
            if self.peek() == '=':
                self.put(TokenType.ASSIGN_SHIFT_RIGHT, '>>=')
                self.advance()
            else:
                self.put(TokenType.SHIFT_R, '>>')
        else:
            self.put(TokenType.MAJOR, '>')
    else:
        self.error(f"Cáracter de bracket no reconocido '{char}'")
