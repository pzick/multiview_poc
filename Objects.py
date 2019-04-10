class Variable(object):
    def __init__(self, values):
        self.classname = values['classname']
        self.name = values['name']
        self.specialtype = values['specialtype']
        self.returntype = values['returntype']
        self.protection = values['protection']
        self.uml_line = ''
        self.header_start = ''
        self.header_end = ''
        self.code_start = ''
        self.code_end = ''
        self.body_loc = ''

    def setProtectionType(self, protection):
        self.protection = protection

    def setUmlLine(self, line):
        self.uml_line = line

class Function(object):
    def __init__(self, values):
        self.classname = values['classname']
        self.name = values['name']
        self.specialtype = values['specialtype']
        self.returntype = values['returntype']
        self.parameters = values['parameters']
        self.body = values['body']
        self.protection = ''
        self.body_loc = ''
        self.uml_line = ''
        self.header_start = ''
        self.header_end = ''
        self.code_start = ''
        self.code_end = ''

    def __call__(self):
        return self

    def setBody(self, body):
        self.body = body

    def setUmlLine(self, line):
        self.uml_line = line

    def setHeaderStartStop(self, start, end):
        self.header_start = start
        self.header_end = end

    def getHeaderStartStop(self):
        return self.header_start, self.header_end

    def setCodeStartStop(self, start, end):
        self.code_start = start
        self.code_end = end

    def getCodeStartStop(self):
        return self.code_start, self.code_end

    def setParameters(self, params):
        self.parameters = params

    def setProtectionType(self, type):
        self.protection = type

    def getSignature(self):
        signature = ''
        if self.specialtype == '~':
            signature = '~{}::{}()'.format(self.classname, self.classname)
        else:
            if self.specialtype != '':
                signature = '{}{} '.format(signature, self.specialtype)
            if self.returntype != '':
                signature = '{}{} '.format(signature, self.returntype)
            signature = '{}{}::{}({})'.format(signature, self.classname, self.name, self.parameters)
        return signature

class ClassBox(object):
    def __init__(self):
        self.line_height = 20
        self.char_width = 8
        self.left = 0
        self.right = 0
        self.top = 0
        self.bottom = 0
        self.width = 0
        self.height = 0

        self.setUpperLeftLocation(20, 20)
        self.setWidthHeight(14, 9)
        self.updateTopBottom()

    def setUpperLeftLocation(self, x, y):
        self.left = x
        self.top = y

    def updateTopBottom(self):
        self.bottom = self.top + self.height
        self.right = self.left + self.width

    def setWidthHeight(self, char_width, char_height):
        self.width = char_width * self.char_width
        self.height = char_height * self.line_height

    def getBox(self):
        box = (self.left,
               self.top,
               self.right,
               self.bottom)
        return box


class ClassModel(object):
    def __init__(self):
        self.name = ''
        self.variables_list = {}
        self.variables_ordered_list = []
        self.function_list = {}
        self.function_ordered_key_list = []
        self.header_start = None
        self.header_end = None
        self.protection_state = 'public'

    def make_new(self):
        self.name = ''
        self.variables_list = {}
        self.variables_ordered_list = []
        self.function_list = {}
        self.function_ordered_keys = []
        self.header_start = None
        self.header_end = None
        self.protection_state = 'public'
