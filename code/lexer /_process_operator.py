from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from codegen.lexer import Lexer

from codegen.obj.tokens import TokenType

def view(self: Lexer, char: str):
    if self.peek() == '=':
        self.advance()
        if char == '+':
            self.put(TokenType.ASSIGN_PLUS, '+=')
        elif char == '-':
            self.put(TokenType.ASSIGN_SUB, '-=')
        elif char == '%':
            self.put(TokenType.ASSIGN_MOD, '%=')
        elif char == '*':
            self.put(TokenType.ASSIGN_MULT, '*=')
        elif char == '/':
            self.put(TokenType.ASSIGN_DIV, '/=')
        else:
            self.error(f"Asignador compuesto no válido para '{char}'")
    else:
        if char == '+':
            if self.peek() == '+':
                self.put(TokenType.PLUSPLUS, '++')
                self.advance()
            else:
                self.put(TokenType.PLUS, '+')
        elif char == '-':
            if self.peek() == '-':
                self.put(TokenType.MINUSMINUS, '--')
                self.advance()
            else:
                self.put(TokenType.MINUS, '-')
        elif char == '*':
            if self.peek() == '*':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.put(TokenType.ASSIGN_POW, '**=')
                else:
                    self.put(TokenType.POW, '**')
            elif self.peek() == '/':
                self.advance()
                self.comment_start = False
            else:
                self.put(TokenType.MULT, '*')
        elif char == '/':
            if self.peek() == '/':
                self.advance()
                if self.peek() == '=':
                    self.advance()
                    self.put(TokenType.ASSIGN_FLOORDIV, '//=')
                else:
                    self.put(TokenType.FLOORDIV, '//')
            elif self.peek() == '*':
                self.advance()
                self.comment_start = True
                return
            else:
                self.put(TokenType.DIV, '/')
        elif char == '%':
            self.put(TokenType.MOD, '%')
        else:
            self.error(f"Operador no reconocido '{char}'")
