"""
SAS Parser - Converts SAS code to an Abstract Syntax Tree (AST)
"""
import re
from dataclasses import dataclass
from typing import List, Union, Optional

# ---------------------------------------------------------------------
# TOKEN SPECIFICATION
# ---------------------------------------------------------------------

TOKEN_SPEC = [
    ('NUMBER',   r'\d+(\.\d+)?'),
    ('IDENT',    r'[A-Za-z_]\w*'),
    ('EQ',       r'='),
    ('PLUS',     r'\+'),
    ('MINUS',    r'-'),
    ('MULT',     r'\*'),
    ('DIV',      r'/'),
    ('DOT',      r'\.'),
    ('SEMI',     r';'),
    ('LPAREN',   r'\('),
    ('RPAREN',   r'\)'),
    ('COMMA',    r','),
    ('WS',       r'\s+'),
    ('OTHER',    r'.'),
]

MASTER_REGEX = '|'.join(f'(?P<{name}>{pattern})' for name, pattern in TOKEN_SPEC)
KEYWORDS = {'data', 'set', 'run', 'if', 'then', 'proc', 'sort', 'by', 'print', 'import', 'replace'}


# ---------------------------------------------------------------------
# AST NODE TYPES
# ---------------------------------------------------------------------

@dataclass
class Token:
    type: str
    value: str

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

@dataclass
class PrintStatement:
    dataset: Optional[str] = None


# ---------------------------------------------------------------------
# LEXER
# ---------------------------------------------------------------------

def lex(code: str) -> List[Token]:
    """Convert SAS code string to a list of tokens."""
    tokens = []
    for match in re.finditer(MASTER_REGEX, code, flags=re.IGNORECASE):
        kind = match.lastgroup
        value = match.group()

        if kind == 'WS':
            continue
        if kind == 'IDENT':
            if value.lower() in KEYWORDS:
                kind = value.lower().upper()
        tokens.append(Token(kind, value))
    return tokens


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

    def parse(self):
        """Parse the token stream into an AST."""
        items = []
        while self.peek():
            tok = self.peek()
            if tok.type == 'DATA':
                items.append(self.parse_data_step())
            elif tok.type == 'PROC':
                node = self.parse_proc()
                if node:
                    items.append(node)
            else:
                self.eat()
        return items

    def parse_data_step(self):
        """Parse a DATA step."""
        self.eat('DATA')
        
        # Handle qualified dataset name (e.g., work.test)
        parts = [self.eat('IDENT').value]
        while self.peek() and self.peek().type == 'DOT':
            self.eat('DOT')
            parts.append(self.eat('IDENT').value)
        name = '.'.join(parts)
        
        self.eat('SEMI')

        statements = []
        while True:
            tok = self.peek()
            if not tok or tok.type == 'RUN':
                break
                
            if tok.type == 'SEMI':
                self.eat('SEMI')
            elif tok.type == 'SET':
                statements.append(self.parse_set())
            elif tok.type == 'INFILE':
                # Skip INFILE for now
                self.eat('INFILE')
                while self.peek() and self.peek().type != 'SEMI':
                    self.eat()
                self.eat('SEMI')
            elif tok.type == 'DATALINES':
                # Skip DATALINES for now
                self.eat('DATALINES')
                while self.peek() and self.peek().type != 'SEMI':
                    self.eat()
                self.eat('SEMI')
            elif tok.type == 'IF':
                statements.append(self.parse_if())
            elif tok.type == 'IDENT':
                statements.append(self.parse_assignment())
            else:
                self.eat()

        self.eat('RUN')
        self.eat('SEMI')
        return DataStep(name=name, statements=statements)

    def parse_proc(self):
        """Parse a PROC step."""
        self.eat('PROC')
        proc_name = self.eat('IDENT').value
        
        if proc_name.upper() == 'PRINT':
            # Parse PROC PRINT
            dataset = None
            
            # Parse options until RUN
            while self.peek() and self.peek().type not in ['RUN', 'PROC']:
                if self.peek().type == 'IDENT' and self.peek().value.upper() == 'DATA':
                    self.eat('IDENT')  # DATA
                    self.eat('EQ')      # =
                    
                    # Get dataset name (may be qualified)
                    parts = [self.eat('IDENT').value]
                    while self.peek() and self.peek().type == 'DOT':
                        self.eat('DOT')
                        parts.append(self.eat('IDENT').value)
                    dataset = '.'.join(parts)
                else:
                    self.eat()
            
            # Consume RUN;
            if self.peek() and self.peek().type == 'RUN':
                self.eat('RUN')
                self.eat('SEMI')
            
            return PrintStatement(dataset=dataset)
        else:
            # Skip other PROCs
            while self.peek() and self.peek().type not in ['RUN', 'PROC']:
                self.eat()
            if self.peek() and self.peek().type == 'RUN':
                self.eat('RUN')
                self.eat('SEMI')
            return None

    def parse_set(self):
        """Parse a SET statement."""
        self.eat('SET')
        parts = [self.eat('IDENT').value]
        while self.peek() and self.peek().type == 'DOT':
            self.eat('DOT')
            parts.append(self.eat('IDENT').value)
        self.eat('SEMI')
        return SetStatement('.'.join(parts))

    def parse_assignment(self):
        """Parse an assignment statement (e.g., x = y + z)."""
        var = self.eat('IDENT').value
        self.eat('EQ')
        expr_tokens = []
        while self.peek() and self.peek().type != 'SEMI':
            expr_tokens.append(self.eat().value)
        self.eat('SEMI')
        return Assignment(var, ' '.join(expr_tokens))

    def parse_if(self):
        """Parse an IF-THEN statement."""
        self.eat('IF')
        cond_tokens = []
        while self.peek() and self.peek().type != 'THEN':
            cond_tokens.append(self.eat().value)
        self.eat('THEN')
        assign = self.parse_assignment()
        return IfStatement(' '.join(cond_tokens), assign)

    def parse_assignment(self):
        var = self.eat('IDENT').value
        self.eat('EQ')
        expr_tokens = []
        while self.peek() and self.peek().type != 'SEMI':
            # Accept any token as part of the expression
            expr_tokens.append(self.eat().value)
        self.eat('SEMI')
        return Assignment(var, ' '.join(expr_tokens))
# ---------------------------------------------------------------------
# CODE GENERATOR
# ---------------------------------------------------------------------

class CodeGen:
    def generate(self, ast_items):
        """Generate Python code from AST."""
        py = ["import pandas as pd", ""]
        for item in ast_items:
            if isinstance(item, DataStep):
                py.append(self.gen_data_step(item))
            elif isinstance(item, PrintStatement):
                if item.dataset:
                    py.append(f"print({item.dataset})")
                else:
                    py.append("print(df)")
        return "\n".join(py)

    def gen_data_step(self, node: DataStep):
        """Generate Python for a DATA step."""
        lines = [f"# DATA step {node.name}"]
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

    def _cond_to_mask(self, cond: str):
        """Convert SAS condition to pandas mask."""
        parts = cond.split()
        if len(parts) == 3:
            left, op, right = parts
            return f"(df['{left}'] {op} {right})"
        return cond


# ---------------------------------------------------------------------
# MAIN FUNCTION
# ---------------------------------------------------------------------

def sas_to_python(code: str) -> str:
    """Convert SAS code to Python."""
    tokens = lex(code)
    ast = Parser(tokens).parse()
    return CodeGen().generate(ast)


# Example usage
if __name__ == "__main__":
    test_sas = """
        data work.test;
            set sashelp.class;
            age2 = age * 2;
        run;
        
        proc print data=sashelp.class;
        run;
    """
    print(sas_to_python(test_sas))

