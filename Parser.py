from Lexer import Lexer, Token, TokenType, PRIMITIVE_VALUES
import os


class StructHolder:
	def __init__(self):
		self.enums = []
		self.records = []
		self.packets = []

	def addEnum(self, enum):
		self.enums.append(enum)

	def addRecord(self, record):
		self.records.append(record)

	def addPacket(self, packet):
		self.packets.append(packet)


class Namespace:
	def __init__(self, path):
		self.path = path
		self.structs = {}
	
	def getName(self):
		return self.path.split(".")[-1]
	
	def addEnum(self, file, value):
		if file not in self.structs:
			self.structs[file] = StructHolder()
		self.structs[file].addEnum(value)
		
	def addRecord(self, file, value):
		if file not in self.structs:
			self.structs[file] = StructHolder()
		self.structs[file].addRecord(value)
	
	def addPacket(self, file, value):
		if file not in self.structs:
			self.structs[file] = StructHolder()
		self.structs[file].addPacket(value)


class Enum:
	def __init__(self, name):
		self.name = name
		self.values = []
	
	def addValue(self, name):
		self.values.append(name)

	def hasValue(self, name):
		for val in self.values:
			if val == name: return True
		return False


class Type:
	def __init__(self, name):
		self.name = name
		self.isArray = False
		self.subType = None
		
	def setArray(self, subType):
		self.isArray = True
		self.subType = subType
		self.name = "List"
		return self.subType

	def isPrimitiveType(self):
		if not self.isArray:
			return self.name in PRIMITIVE_VALUES
		else:
			return self.subType.isPrimitiveType()
	
	def __repr__(self):
		if self.isArray:
			return f"List<{self.subType}>"
		return f"{self.name}"


class Field:
	def __init__(self, name, type, value=None):
		self.name = name
		self.type = type
		self.value = value
	
	def hasValue(self):
		return self.value is not None
		
	def __repr__(self):
		return f"<Field name={self.name} type={self.type}{' value='+str(self.value) if self.hasValue() else ''}>"


class Record:
	def __init__(self, name):
		self.name = name
		self.fields = []
		self.metatags = []
	
	def addField(self, field):
		self.fields.append(field)
	
	def addMetatag(self, metatag):
		self.metatags.append(metatag)

	def getField(self, name):
		for field in self.fields:
			if field.name == name:
				return field
		return None
	
	def __repr__(self):
		pass


class Packet(Record):
	def __init__(self, name):
		super().__init__(name)
		self.packetID = -1
	
	def setPacketID(self, value):
		self.packetID = value
	
	def hasPacketID(self):
		return self.packetID != -1


class Parser:
	def __init__(self):
		self.tokens = []
		self.idx = 0
		self.file = None
		self.currentns = None
		
		self.namespaces = []
		self.metatag = []

	# Parser functions

	def isAtEnd(self):
		return self.idx >= len(self.tokens)
	
	def advance(self):
		self.idx += 1
		return self.tokens[self.idx-1]

	def previous(self):
		return self.tokens[self.idx-1]

	def peek(self):
		return self.tokens[self.idx]
	
	def peekNext(self):
		return self.tokens[self.idx+1]
		
	def match(self, type, value=None):
		if self.peek().type == type and ((value is not None and self.peek().value == value) or value is None):
			self.advance()
			return True
		return False

	def error(self, msg):
		print("Error in " + self.file + " at line " + str(self.previous().line) + ":")
		print(msg)
		exit(-1)

	def consume(self, type, errMsg, value = None):
		if self.peek().type == type and ((value is not None and self.peek().value == value) or value is None):
			tok = self.advance()
			return tok
		self.error(errMsg)

	def expect(self, type, value=None):
		return self.consume(type, "Expected " + type.name + " found " + self.peek().type.name, value)

	def isKeyword(self, tok, keyword):
		return tok.type == TokenType.IDENTIFIER and tok.value == keyword

	# Namespace Getters

	def isNameAvailable(self, ns, name):
		for struct in ns.records + ns.packets + ns.enums:
			if struct.name == name:
				return False
		return True

	def getNamespace(self, name):
		for ns in self.namespaces:
			if ns.path == name:
				return ns
		return None

	# Token Parsing

	def makeMetatag(self):
		name = self.expect(TokenType.NAME).value
		self.expect(TokenType.RBRACES)

		if name not in self.metatag:
			self.metatag.append(name)

	def makeFieldTypeIdentifier(self, until, allowAssign=False):
		typeName = self.advance().value
		value = None

		if typeName not in PRIMITIVE_VALUES:
			self.error("Expected a record, packet, enum or primitive type. Got " + typeName)

		if typeName == "List":
			type = Type("List")
			startType = type

			listAmount = 0

			self.expect(TokenType.LBRACES)
			while self.peek().type == TokenType.IDENTIFIER and self.peek().value == "List":
				type = type.setArray(Type("List"))
				self.advance()
				self.expect(TokenType.LBRACES)
				listAmount += 1

			if self.peek().type == TokenType.IDENTIFIER:
				type.subType = self.makeFieldTypeIdentifier(TokenType.RBRACES)
			elif self.peek().type == TokenType.NAME:
				type.subType = self.makeFieldTypeName(TokenType.RBRACES)
			else:
				self.error("Expected a name or primitive type. Found: " + self.peek().type.name)

			while self.peek().type != until:
				self.expect(TokenType.RBRACES)
				listAmount -= 1

			if listAmount > 0:
				self.error("Unclosed RBRACES")

			self.expect(TokenType.SEMICOLON)
			return startType, None

		else:
			if typeName in ["String", "int", "short", "double", "VarInt", "VarLong"] and allowAssign:
				if self.match(TokenType.ASSIGN):
					if self.peek().type == TokenType.NUMBER or self.peek().type == TokenType.STRING:
						value = self.advance().value
					else:
						self.error("A string or number expected. Found "+self.peek().type.name)
			self.expect(until)
			return Type(typeName), value

	def makeFieldTypeName(self, until):
		path = self.advance().value
		while self.peek().type != until:
			path += "."
			self.expect(TokenType.DOT)
			path += self.expect(TokenType.NAME).value
		self.expect(until)
		return Type(path), None

	def makeFieldType(self):
		if self.peek().type == TokenType.IDENTIFIER:
			return self.makeFieldTypeIdentifier(TokenType.SEMICOLON, True)
		elif self.peek().type == TokenType.NAME:
			return self.makeFieldTypeName(TokenType.SEMICOLON)
		else:
			self.error("Expected a name or primitive type. Found: "+self.peek().type.name)

	def makeRecordField(self):
		name = self.expect(TokenType.NAME).value
		self.expect(TokenType.DOTDOT)

		typ, val = self.makeFieldType()
		field = Field(name, typ, val)
		return field
	
	def makeRecord(self, isPacket):
			name = self.expect(TokenType.NAME).value

			if not self.isNameAvailable(self.currentns, name):
				self.error("You can't use same name for 2 types.")

			record = Record(name) if not isPacket else Packet(name)
			for _metatag in self.metatag:
				record.addMetatag(_metatag)
			self.metatag.clear()
			
			self.expect(TokenType.LCURLY)
			
			while not self.isAtEnd() and self.peek().type != TokenType.RCURLY:
				field = self.makeRecordField()
				if record.getField(field.name) is not None:
					self.error("You can't define two fields with same name in one "+("packet" if isPacket else "record"))
				record.addField(field)

			if self.isAtEnd():
				self.error("Unclosed block")

			if isPacket and (record.getField("packetID") is None or record.getField("packetID").value is None):
				self.error("Packets must have a packetID field with a value.")

			self.expect(TokenType.RCURLY)
			if isPacket:
				self.currentns.addPacket(self.file, record)
				return
			self.currentns.addRecord(self.file, record)
	
	def makeEnum(self):
			name = self.expect(TokenType.NAME).value

			if not self.isNameAvailable(self.currentns, name):
				self.error("You can't use same name for 2 types.")

			self.expect(TokenType.LCURLY)
			
			enum = Enum(name)
			
			while not self.isAtEnd() and self.peek().type != TokenType.RCURLY:
				val = self.expect(TokenType.NAME).value

				if enum.hasValue(val):
					self.error("You can't define same value twice inside an enum")
				enum.addValue(val)
				if self.peek().type != TokenType.RCURLY:
					self.expect(TokenType.COMMA)

			if self.isAtEnd():
				self.error("Unclosed block")
			
			self.currentns.addEnum(self.file, enum)

	# Main Parse Method

	def parse(self, filename, tokens):
		self.tokens = tokens
		self.idx = 0
		self.file = filename
		
		self.consume(TokenType.IDENTIFIER, "Namespace expected at the top of file", "namespace")
		
		name = self.consume(TokenType.STRING, "Namespace needs a name").value

		namespace = Namespace(name) if self.getNamespace(name) is None else self.getNamespace(name)
		self.currentns = namespace
		
		while not self.isAtEnd():
			tok = self.advance()
			
			if tok.type == TokenType.LBRACES:
				self.makeMetatag()
			elif self.isKeyword(tok, "record"):
				self.makeRecord(False)
			elif self.isKeyword(tok, "packet"):
				self.makeRecord(True)
			elif self.isKeyword(tok, "enum"):
				self.makeEnum()
			elif tok.type == TokenType.EOF:
				if len(self.metatag) > 0:
					self.error("Unknown metatag")
		if self.currentns not in self.namespaces:
			self.namespaces.append(self.currentns)