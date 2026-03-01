import sys
from typing import Any

from codegen.obj.tokens import *
from codegen.lexer import (
    _resolve_indent,
    _process_operator,
    _process_string,
    _process_brackets,
    _process_logic_op,
    _process_word,
)
from codegen.item.keywords import *


class LexerError(Exception):
    def __init__(self, message: str, line: int, column: int):
        super().__init__(f"[Lexer Error] {message} at line {line}, column {column}")


class Lexer:
    def __init__(self, source: str):
        self.src = source
        self.line = 1
        self.pos = 0
        self.linepos = 0
        self.at_start_line = True
        self.indent_stack = [0]
        self.tokens: list[Token] = []
        self.comment_start = False  # comentarios multilinea /* */

    def peek(self):
        return self.src[self.pos] if self.pos < len(self.src) else ""

    def advance(self):
        c = self.peek()
        self.pos += 1
        self.linepos += 1
        return c

    def put(self, ttype: TokenType, value: Any):
        if self.comment_start:
            return
        self.tokens.append(Token(ttype, value, self.line, self.linepos))

    def error(self, message: str):
        raise LexerError(message, self.line, self.linepos)

    def tokenize(self):
        self.tokens.clear()
        while self.peek():
            if self.at_start_line:
                _resolve_indent.view(self)
                self.at_start_line = False

            c = self.advance()

            # manejo de saltos de línea y espacios
            if c == '\n':
                self.put(TokenType.NEWLINE, None)
                self.linepos = 0
                self.line += 1
                self.at_start_line = True
                continue
            elif c in ' \0':
                continue

            # palabras y tipos
            elif c.isalpha() or c == '_':
                _process_word.view(self, c)
                continue

            # números
            elif c.isdigit() or (c == '-' and self.peek().isdigit()):
                num = c
                points = 0

                while self.peek().isdigit() or self.peek() == '.':
                    n = self.advance()
                    if n == '.':
                        if num == '-':
                            self.error("Número inválido: '-' seguido de '.' sin dígito")
                        points += 1
                        if points > 1:
                            self.error("Número flotante con múltiples puntos decimales")
                    num += n

                if num in ('', '-'):
                    self.error("Número inválido o incompleto")
                elif num.endswith('.'):
                    self.error(f"Número incompleto antes del punto final: {num}")

                self.put(TokenType.NUMBER, num)
                if self.peek() == 'f':
                    self.put(TokenType.SUFFIX_FLOAT, 'f')
                    self.advance()
                continue

            # asignación y comparaciones
            elif c == '=':
                if self.peek() == '=':
                    self.put(TokenType.EQUAL, '==')
                    self.advance()
                else:
                    self.put(TokenType.ASSIGN, '=')
                continue

            # operadores aritméticos
            elif c in '+-*/%':
                _process_operator.view(self, c)
                continue

            # strings
            elif c in ('"', "'"):
                _process_string.view(self, c)
                continue

            # comentarios de línea
            elif c == "#":
                while not (self.peek() in ('\n', '')):
                    self.advance()
                self.line += 1
                self.linepos = 0
                self.at_start_line = True
                continue

            # puntos y elipsis
            elif c == '.':
                if self.peek() == '.':
                    self.advance()
                    if self.peek() == '.':
                        self.advance()
                        self.put(TokenType.ELLIPSIS, '...')
                    else:
                        self.error("Se esperaban tres puntos consecutivos '...'")
                else:
                    self.put(TokenType.DOT, '.')
                continue

            # separadores
            elif c == ',':
                self.put(TokenType.COMMA, ',')
                continue
            elif c == ':':
                self.put(TokenType.COLON, ':')
                continue
            elif c in '(){}[]<>':
                _process_brackets.view(self, c)
                continue
            elif c in '|&!^~':
                _process_logic_op.view(self, c)
                continue
            elif c == '@':
                self.put(TokenType.AT, '@')
                continue
            elif c == ';':
                self.put(TokenType.SEMICOLON, ';')
                continue
            elif c == '\\':
                self.put(TokenType.BACKSLASH, '\\')
                continue

            self.error(f"Cáracter no reconocido '{c}'")

        self.put(TokenType.EOF, None)
        return self.tokens
