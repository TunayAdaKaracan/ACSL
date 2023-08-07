import re
import os

NAMESPACE = re.compile(r'namespace "\w+(\.\w+)*"')
NAMESPACE_STRING = re.compile(r'"\w+(\.\w+)*"')
IMPORT_FROM_OTHER = re.compile(r'\w+(\.\w+)+')


class Preprocessor:
    def __init__(self, files):
        self.files = files  # List[(filePath, fileData)]

        self.ordered = []  # List[(filePath, (ns, imports))]
        self.tmp = []
        for file in self.files:
            self.tmp.append((file[0], self.getImports(file[0], file[1])))

    def error(self, msg):
        print(msg)
        exit(-1)

    def getData(self, filePath):
        for tmp in self.files:
            if tmp[0] == filePath:
                return tmp[1]
        return None

    def getNamespace(self, fileName, file):
        if NAMESPACE.search(file) is None:
            self.error("No namespace defined in file: "+fileName)
        return NAMESPACE_STRING.search(file)[0][1:-1]

    def usedImports(self, file):
        imports = []
        for line in file.split('\n')[1:]:
            imprt = IMPORT_FROM_OTHER.search(line)
            if imprt:
                imports.append('.'.join(imprt[0].split('.')[:-1]))
        return imports

    def getImports(self, fileName, file):
        data = (self.getNamespace(fileName, file), self.usedImports(file))
        return data

    def isAlreadyLoaded(self, data):
        for tmp in self.ordered:
            if tmp == data:
                return True
        return False

    def getNamespaceFromName(self, name):
        files = []
        for tmp in self.tmp:
            if tmp[1][0] == name:
                files.append(tmp)
        return files

    def _order(self, prev, datas):
        if not datas:
            self.error("Undefined import use.")
        for data in datas:
            if self.isAlreadyLoaded(data):
                continue

            if len(data[1][1]) > 0:
                for otherNS in data[1][1]:
                    if prev is not None and prev[1][0] == otherNS:
                        continue
                    self._order(data, self.getNamespaceFromName(otherNS))
            self.ordered.append(data)
            self.tmp.remove(data)

    """
        Order them by imports
    """
    def firstPass(self):
        while len(self.tmp) != 0:
            self._order(None, [self.tmp[0]])


    """
        Order them by internal data uses
    """
    def secondPass(self):
        pass

    def getOrderedFiles(self):  # -> List[(FilePath, FileData)]
        self.firstPass()
        self.secondPass()

        return [(data[0], self.getData(data[0])) for data in self.ordered]