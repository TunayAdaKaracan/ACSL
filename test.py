from Lexer import Lexer
from Parser import Parser
from Processor import Preprocessor
import os


files = []
for file in os.listdir('./schemas'):
    with open('./schemas/' + file, "r") as f:
        files.append((file, f.read()))

pre = Preprocessor(files)
tokens = {}
for file in pre.getOrderedFiles():
    lexer = Lexer(file[1])
    tokens[file[0]] = lexer.lex()

parser = Parser()
for key, val in tokens.items():
    parser.parse(key, val)

for ns in parser.namespaces:
    print("Namespace - "+ns.path)
    for record in ns.records:
        print("Record Name: "+record.name +" Metatags: "+", ".join(record.metatags))
        for field in record.fields:
            print(field)
    for enum in ns.enums:
        print("Enum Name: "+enum.name)
        for value in enum.values:
            print(value)