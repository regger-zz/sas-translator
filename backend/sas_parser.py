import re
from dataclasses import dataclass
from typing import List, Union

# ---------------------------------------------------------------------
# TOKENS
# ---------------------------------------------------------------------

TOKEN_SPEC = [
    ('NUMBER',   r'\d+(\.\d+)?'),
    ('IDENT',    r'[A-Za-z_]\w*'),
    ('EQ',       r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MULT',     r'\*'),
    ('DIV',      r'/'),
    ('SEMI',     r';'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('COMMA',    r','),
    ('WS',       r'\s+'),
    ('OTHER',    r'.'),  # catch-all
]

MASTER_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
KEYWORDS = {'data', 'set', 'run', 'if', 'then', 'proc', 'sort', 'by', 'print', 'import', 'replace'}

@dataclass
class Token:
    type: str
    value: str

def lex(code: str) -> List[Token]:
    tokens = []
    for match in re.finditer(MASTER_REGEX, code, flags=re.IGNORECASE):
        kind = match.lastgroup
        value = match.group()

        if kind == 'WS':
            continue
        if kind == 'IDENT':
            if value.lower() in KEYWORDS:
                kind = value.lower().upper()  # keyword token type
        tokens.append(Token(kind, value))
    return tokens

# ---------------------------------------------------------------------
# AST NODE TYPES
# ---------------------------------------------------------------------

@dataclass
class DataStep:
    name: str
    statements: List

@dataclass
class SetStatement:
    table: str

@dataclass
class Assignment:
    var: str
    expr: str

@dataclass
class IfStatement:
    condition: str
    assignment: Assignment

@dataclass
class InfileStatement:
    path: str

# ---------------------------------------------------------------------
# PARSER
# ---------------------------------------------------------------------

class Parser:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.i = 0

    def peek(self):
        return self.tokens[self.i] if self.i < len(self.tokens) else None

    def eat(self, kind=None):
        tok = self.peek()
        if not tok:
            raise ValueError("Unexpected EOF")
        if kind and tok.type != kind:
            raise ValueError(f"Expected {kind}, got {tok.type}")
        self.i += 1
        return tok

    # ---------------------------------------------------------


    def parse(self):
        items = []
        while self.peek():
            tok = self.peek()
            if tok.type == 'DATA':
                items.append(self.parse_data_step())
            elif tok.type == 'PROC': 
                self.parse_proc()     # Skip PROC statements
            else:
                self.eat()  # skip unknown
        return items

        # ---------------------------------------------------------

    def parse_data_step(self):
        self.eat('DATA')
        name = self.eat('IDENT').value
        self.eat('SEMI')
    
        statements = []
        while True:
            tok = self.peek()
            if not tok or tok.type == 'RUN':
                break
                
            if tok.type == 'SET':
                statements.append(self.parse_set())
            elif tok.type == 'INFILE':
                # Skip INFILE statement for now
                self.eat('INFILE')
                while self.peek() and self.peek().type != 'SEMI':
                    self.eat()
                self.eat('SEMI')
            elif tok.type == 'DATALINES':
                # Skip DATALINES block
                self.eat('DATALINES')
                while self.peek() and self.peek().type != 'SEMI':
                    self.eat()
                self.eat('SEMI')
            elif tok.type == 'IF':
                statements.append(self.parse_if())
            elif tok.type == 'IDENT':
                statements.append(self.parse_assignment())
            elif tok.type == 'PROC':  
                self.eat('PROC')
                proc_name = self.eat('IDENT').value

            elif tok.type == 'PROC':
                self.eat('PROC')
                proc_name = self.eat('IDENT').value
                # Skip everything until RUN or next PROC/DATA
                while self.peek() and self.peek().type not in ['RUN', 'PROC', 'DATA']:
                    self.eat()
                if self.peek() and self.peek().type == 'RUN':
                    self.eat('RUN')
                    self.eat('SEMI')

                if proc_name.upper() == 'PRINT':
                    # Skip PROC PRINT
                    while self.peek() and self.peek().type not in ['RUN', 'DATA', 'PROC']:
                        self.eat()
                    if self.peek() and self.peek().type == 'RUN':
                        self.eat('RUN')
                        self.eat('SEMI')
                else:
                    # Unknown PROC - skip it
                    while self.peek() and self.peek().type not in ['RUN', 'DATA', 'PROC']:
                        self.eat()
            else:
                self.eat()

        self.eat('RUN')
        self.eat('SEMI')
        return DataStep(name=name, statements=statements)

    def parse_set(self):
        self.eat('SET')
        table = self.eat('IDENT').value
        self.eat('SEMI')
        return SetStatement(table)

    def parse_proc(self):
        """Skip entire PROC statement"""
        self.eat('PROC')
        while self.peek() and self.peek().type != 'RUN':
            self.eat()
        if self.peek() and self.peek().type == 'RUN':
            self.eat('RUN')
            self.eat('SEMI')

    def parse_assignment(self):
        var = self.eat('IDENT').value
        self.eat('EQ')
        expr_tokens = []
        while self.peek() and self.peek().type != 'SEMI':
            expr_tokens.append(self.eat().value)
        self.eat('SEMI')
        return Assignment(var, ' '.join(expr_tokens))

    def parse_if(self):
        self.eat('IF')
        cond_tokens = []
        while self.peek() and self.peek().type != 'THEN':
            cond_tokens.append(self.eat().value)
        self.eat('THEN')
        assign = self.parse_assignment()
        return IfStatement(' '.join(cond_tokens), assign)

    def parse_infile(self):
        self.eat('INFILE')
        path = self.eat('IDENT').value  # Simplifies for now
        self.eat('SEMI')
        return InfileStatement(path)
    
# ---------------------------------------------------------------------
# CODE GENERATION (SAS AST → Python/Pandas)
# ---------------------------------------------------------------------

class CodeGen:
    def generate(self, ast_items):
        py = ["import pandas as pd", ""]
        for item in ast_items:
            if isinstance(item, DataStep):
                py.append(self.gen_data_step(item))
        return "\n".join(py)

    def gen_data_step(self, node: DataStep):
        lines = [f"# DATA step {node.name}"]
        lines.append("df = pd.DataFrame()")
        for stmt in node.statements:
            if isinstance(stmt, SetStatement):
                lines.append(f"df = pd.read_csv('{stmt.table}.csv')")
            elif isinstance(stmt, Assignment):
                lines.append(f"df['{stmt.var}'] = {stmt.expr}")
            elif isinstance(stmt, IfStatement):
                cond = stmt.condition.replace("=", "==")
                lines.append(
                    f"df.loc[{self._cond_to_mask(cond)}, '{stmt.assignment.var}'] = {stmt.assignment.expr}"
                )
        return "\n".join(lines)

    def gen_infile(self, stmt):
        return f"df = pd.read_csv('{stmt.path}')"
    
    def _cond_to_mask(self, cond: str):
        # simple "x == 1" → df['x'] == 1
        left, op, right = cond.split()
        return f"(df['{left}'] {op} {right})"


# ---------------------------------------------------------------------
# DRIVER
# ---------------------------------------------------------------------

    def sas_to_python(code: str) -> str:
        print(f"Parsing code: {repr(code[:100])}...")  # Debug
        tokens = lex(code)
        print(f"Tokens: {[(t.type, t.value) for t in tokens[:10]]}")  # Debug
        ast = Parser(tokens).parse()
        return CodeGen().generate(ast)


# Example usage:
    if __name__ == "__main__":
        sas = """
            data example;
                set mytable;
                x = a + b;
                if a = 1 then y = 3*b;
            run;
        """
        print(sas_to_python(sas))

