class TokenType:
	EOF = None
	IDENTIFIER = None
	NAME = None
	STRING = None
	NUMBER = None
	LCURLY = None
	RCURLY = None
	LBRACES = None
	RBRACES = None
	DOTDOT = None
	DOT = None
	SEMICOLON = None
	COMMA = None
	ASSIGN = None

	def __init__(self, name):
		self.name = name

	def __repr__(self):
		return f"<TokenType {self.name}>"


TokenType.EOF = TokenType("EOF")
TokenType.IDENTIFIER = TokenType("IDENTIFIER")
TokenType.NAME = TokenType("NAME")
TokenType.STRING = TokenType("STRING")
TokenType.NUMBER = TokenType("NUMBER")
TokenType.DOTDOT = TokenType("DOTDOT")
TokenType.LCURLY = TokenType("LCURLY")
TokenType.RCURLY = TokenType("RCURLY")
TokenType.LBRACES = TokenType("LBRACES")
TokenType.RBRACES = TokenType("RBRACES")
TokenType.DOT = TokenType("DOT")
TokenType.SEMICOLON = TokenType("SEMICOLON")
TokenType.COMMA = TokenType("COMMA")
TokenType.ASSIGN = TokenType("ASSIGN")

KEYWORDS = [
	"namespace",
	"packet",
	"enum",
	"record"
]

PRIMITIVE_VALUES = [
	"VarInt",
	"VarLong",
	"int",
	"bool",
	"String",
	"char",
	"double",
	"float",
	"short",
	"List"
]

KEYWORDS.extend(PRIMITIVE_VALUES)

class Token:
	def __init__(self, type, line, value=None):
		self.type = type
		self.line = line
		self.value = value
		
	def __repr__(self):
		return f"<Token type={self.type} line={self.line}{' value=' +str(self.value) if self.value is not None else ''}>"


class Lexer:
	def __init__(self, source):
		self.source = source
		self.idx = 0
		self.line = 1
		self.tokens = []
	
	def _isAtEnd(self):
		return self.idx >= len(self.source)
	
	def _advance(self):
		self.idx += 1
		return self.source[self.idx-1]
	
	def _peek(self):
		return self.source[self.idx]
		
	def _peekNext(self):
		return self.source[self.idx+1]
		
	def _match(self, char):
		if self._peek() == char:
			self._advance()
			return True
		return False
	
	def _consume(self, char, errMsg):
		if self._peek() == char:
			self._advance()
			return
		print(errMsg)
		exit(-1)
	
	def _isAlphanum(self, char):
		return self._isAlpha(char) or self._isDigit(char)
	
	def _isAlpha(self, char):
		return char.isalpha()
	
	def _isDigit(self, char):
		return char.isdigit()
		
	def _makeToken(self, tokenType, value=None):
		tok = Token(tokenType, self.line, value)
		self.tokens.append(tok)
	
	def _skipWhitespaces(self):
		while True:
			if self._peek() in " \t\r	":
				self._advance()
				continue
			if self._peek() == "\n":
				self._advance()
				self.line += 1
				continue
			if self._peek() == "/":
				if self._match("/"):
					while self._peek() != "\n":
						self._advance()
					continue
			return
	
	def _identifier(self, start):
		text = start
		while self._isAlphanum(self._peek()):
			text += self._advance()
		if text in KEYWORDS or text in PRIMITIVE_VALUES:
			return self._makeToken(TokenType.IDENTIFIER, text)
		
		self._makeToken(TokenType.NAME, text)
	
	def _string(self):
		text = ""
		while not self._isAtEnd() and self._peek() != '"':
			text += self._advance()
		
		if self._isAtEnd():
			print("Unclosed string")
			exit(-1)
		
		self._consume('"', "Unclosed string")
		self._makeToken(TokenType.STRING, text)
	
	def _number(self, start):
		number = start	
		while self._isDigit(self._peek()):
			number += self._advance()
		
		if number[0] == "0" and self._peek() == "x":
			number += self._advance()
			
			def isAHex(self, char):
				return self._isDigit(char) or char.upper() in "ABCDEF"
			
			while isAHex(self, self._peek()):
				number += self._advance()
			return self._makeToken(TokenType.NUMBER, int(number, base=16))
		
		if self._peek() == ".":
			number += self._advance()
			while self._isDigit(self._peek()):
				number += self._advance()
		self._makeToken(TokenType.NUMBER, int(number) if "." not in number else float(number))
			
	
	def lex(self):
		while not self._isAtEnd():
			self._skipWhitespaces()
			char = self._advance()
			
			if self._isAlpha(char):
				self._identifier(char)
				continue
				
			if self._isDigit(char) or (char == "-" and self._isDigit(self._peek())):
				self._number(char)
				continue
			
			if char == "{":
				self._makeToken(TokenType.LCURLY)
			elif char == "}":
				self._makeToken(TokenType.RCURLY)
			elif char == "[":
				self._makeToken(TokenType.LBRACES)
			elif char == "]":
				self._makeToken(TokenType.RBRACES)
			elif char == "=":
				self._makeToken(TokenType.ASSIGN)
			elif char == ":":
				self._makeToken(TokenType.DOTDOT)
			elif char == ";":
				self._makeToken(TokenType.SEMICOLON)
			elif char == ".":
				self._makeToken(TokenType.DOT)
			elif char == ",":
				self._makeToken(TokenType.COMMA)
			elif char == '"':
				self._string()
			else:
				print("Unknown character")
				exit(-1)
		self._makeToken(TokenType.EOF)
		return self.tokens