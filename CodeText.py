import tkinter as tk

from Objects import ClassModel
from Objects import Function
from Objects import Variable


class CppCodeText(tk.Frame):
    def __init__(self, parent, type, class_model):
        tk.Frame.__init__(self, parent)
        self.config(relief='sunken')
        self.type = type
        self.class_model = class_model

        # Main part of the GUI
        self.text = tk.Text(wrap="word", background="white",
                            highlightthickness=5, undo=True, font="Courier", borderwidth=3,
                            highlightbackground='gray', highlightcolor='red',
                            selectbackground='yellow', inactiveselectbackground='#CCCCCC')
        self.vsb = tk.Scrollbar(bg='black', orient="vertical", borderwidth=2, command=self.text.yview)
        self.hsb = tk.Scrollbar(bg='black', orient='horizontal', borderwidth=2, command=self.text.xview)
        self.text.configure(xscrollcommand=self.hsb.set, yscrollcommand=self.vsb.set, wrap=tk.NONE,
                            borderwidth=3, highlightbackground='gray', highlightcolor='red')
        self.vsb.pack(in_=self, side="right", fill="y", expand=False)
        self.hsb.pack(in_=self, side="bottom", fill="x", expand=False)
        self.text.pack(in_=self, side="left", fill="both", expand=True)

        self.return_types = ['int', 'float', 'void', 'unsigned int', 'char', 'unsigned char', 'long', 'unsigned long']
        self.keywords = ['class', 'public', 'private', 'protected', 'if', 'else', 'elseif', 'unsigned', 'const',
                         'static', 'while', 'return']
        self.keywords = self.return_types + self.keywords
        self.comment = ['//', '/*', '*/']
        self.pre_process = ['#include', '#define', '#ifndef', '#ifdef', '#endif']
        self.default_return = {'int': '-1', 'float': '0.0f', 'char': '0', 'unsigned char': '0', 'unsigned int': '0',
                               'void': '', '': '', 'long': '-1', 'unsigned long': '0'}

        self.alternate_type = ''
        self.alternate_view = None
        self.umlClassView = None

        self.class_start = None
        self.class_end = None
        self.protection_state = 'public'
        self.current_functions = []

        self.set_tags()
        self.create_bindings()
        self.scan_layout()

    def make_new(self):
        self.text.delete('1.0', tk.END)
        self.class_start = None
        self.class_end = None
        self.protection_state = 'public'
        self.current_functions = []
        if not (self.umlClassView is None):
            self.umlClassView.make_new()
        self.text.edit_modified(tk.FALSE)

    def set_tags(self):
        self.text.tag_configure('keyword', foreground='blue')
        self.text.tag_configure('preprocessor', foreground='magenta')
        self.text.tag_configure('comment', foreground='green')
        self.text.tag_configure('error', background='red')
        self.text.tag_configure('altered', background='#FFCC55')

    def create_bindings(self):
        self.text.bind('<<Undo>>', self.on_undo)
        self.text.bind('<<Redo>>', self.on_redo)
        self.text.bind('<space>', self.check_line)
        self.text.bind('<Return>', self.check_for_class)
        self.text.bind('<Key-;>', self.process_line)
        self.text.bind('<Key-:>', self.process_line)
        self.text.bind('<Tab>', self.on_tab)
        self.text.bind('<Control-u>', self.print_function_list)

    def connect_alternate_view(self, other_type, other_view):
        self.alternate_view = other_view
        self.alternate_type = other_type

    def connect_uml_class_view(self, uml_class_view):
        self.umlClassView = uml_class_view

    def parse_header(self):
        # Find class bounds
        # Get variable order in file
        current_variables = []
        current_functions = []
        index = self.text.search('class ', '1.0', tk.END)
        if (index != '') and (self.class_model.name != ''):
            self.class_start = self.text.search('{', index, tk.END)
            self.class_end = self.text.search('};', self.class_start, tk.END)

            # Identify the function name, then start and stop locations for function
            body = self.text.get(self.class_start+'+1c', self.class_end)
            line_number = int(self.class_start.split('.')[0]) - 1
            for line in body.splitlines():
                line_number = line_number + 1
                if len(line.strip()) > 0:
                    # Remove comments
                    if line.find('//') > -1:
                        line = line.split('//')[0].strip()
                    elif len(line.strip()) > 0:
                        line = line.strip()
                    if len(line) == 0:
                        # There was a comment on the line, but nothing to process
                        continue
                    if line[-1] == ';':
                        return_type, special_type = self.get_return_type(line)
                        name = self.get_name(line)
                        self.protection_state = self.get_protection_state('{}.0'.format(line_number))
                        # Do not count duplicate function names
                        if 'error' in self.text.tag_names(str(line_number) + '.0'):
                            pass
                        elif self.text.search('(', '{}.0'.format(line_number), '{}.0 lineend'.format(line_number)) == '':
                            if name not in self.class_model.variables_list.keys():
                                value = self.parse_variable_line(line)
                                if not (value is None):
                                    if not (value.name in self.class_model.variables_list.keys()):
                                        self.class_model.variables_list[value.name] = value
                            else:
                                current_variables.append(name)
                        elif line[0:-1].strip()[-1] == ')':
                            clean_line = line.strip()
                            func_name = clean_line.split('(')[0].split(' ')[-1].strip()
                            if not (func_name in self.class_model.function_list.keys()):
                                self.process_line(line_index='{}.0'.format(line_number))
                            else:
                                current_functions.append([func_name, line_number])
                                # Check for change of parameters
                                parameters_changed = False
                                params, loc = self.get_parameters(clean_line)
                                if self.class_model.function_list[func_name][1].parameters != params:
                                    parameters_changed = True
                                if self.type == 'hpp':
                                    func = self.class_model.function_list[func_name][1]
                                    func.protection = self.protection_state
                                    func.setHeaderStartStop('{}.0'.format(line_number),
                                                            '{}.0 lineend'.format(line_number))
                                    if parameters_changed:
                                        func.setParameters(params)
                                        if self.alternate_type == 'cpp':
                                            self.alternate_view.update_cpp_parameters(func, params)
        # Update ordered variable and function list in the class model
        self.class_model.variables_ordered_list = current_variables
        self.class_model.function_ordered_key_list = current_functions
        return current_functions

    def parse_cpp(self):
        current_functions = []
        text = self.text.get('1.0', tk.END)
        line_number = 0
        for line in text.splitlines():
            line_number = line_number + 1
            # Find function signatures
            if line.find('::') > 0:
                # Get function name
                name = line.split('::')[1].split('(')[0].strip()
                if line[0] == '~':
                    name = '~{}'.format(name)

                # Find the end of the function
                function_start = self.text.search(line, '1.0', tk.END)
                function_body_start = '{} +1c'.format(self.text.search('{', function_start, tk.END))
                function_end = 0
                func_line_number = -1
                function_text = self.text.get(function_start, tk.END)
                for function_line in function_text.splitlines():
                    func_line_number = func_line_number + 1
                    if (function_line != '') and (function_line[0] == '}'):
                        function_end = line_number + func_line_number
                        break
                if name in self.class_model.function_list.keys():
                    if line == self.class_model.function_list[name][1].getSignature():
                        if self.type == 'cpp':
                            func = self.class_model.function_list[name][1]
                            func.setCodeStartStop('{}.0'.format(line_number),
                                                  '{}.0'.format(function_end))
                            func.setBody(self.text.get(function_body_start, '{}.0'.format(function_end)))
                current_functions.append((name, line_number, function_end))
        return current_functions

    def update_cpp_parameters(self, function, new_params):
        location_start = self.text.search('(', function.code_start, function.code_end)
        location_end = self.text.search(')', function.code_start, function.code_end)
        self.text.replace(location_start, location_end+'+1c', '({})'.format(new_params))
        function.parameters = new_params

    def scan_layout(self):
        if self.type == 'hpp':
            self.current_functions = self.parse_header()
        elif self.type == 'cpp':
            self.current_functions = self.parse_cpp()
        self.update_keyword_colors('1.0', tk.END)
        self.update_comments('1.0', tk.END)
        self.after(1000, self.scan_layout)

    def check_for_class(self, event):
        if self.class_model.name != '':
            return
        if self.type == 'hpp':
            for line in self.text.get('1.0', tk.END).splitlines():
                clean_line = line.strip().split(' ')
                if clean_line[0] == 'class' and self.class_model.name == '':
                    self.text.edit_separator()
                    current_index = self.text.index(tk.INSERT)
                    self.class_model.name = clean_line[1]
                    self.text.insert(current_index, '\n{\n};\n')

                    # Add the ifndef wrapper and braces wrapper for the class
                    self.text.insert('1.0', '#ifndef {}_HPP\n#define {}_HPP\n\n'.format(
                        self.class_model.name.upper(), self.class_model.name.upper()))
                    self.text.insert(tk.END, '\n\n#endif\n')
                    # Set an undo marker to allow the undo to step to this point if triggered
                    self.text.edit_separator()

                    # Set the insertion point to the start of the class body
                    idx = self.text.search('{', '1.0', tk.END)
                    self.text.mark_set('insert', idx+' lineend')

                    # Insert the initial class body
                    self.text.insert(idx+' lineend', '\n    public:\n')

                    # Make a default constructor function
                    constructor = self.create_function(self.class_model.name, self.class_model.name,
                                                       '', '', '', '', 'public')
                    self.class_model.function_list[self.class_model.name] = [1, constructor]

                    # Insert the default constructor into the class body of the header file
                    start_index = self.text.index(tk.INSERT)
                    self.text.insert(start_index,'        {}();'.format(self.class_model.name))
                    stop_index = self.text.index(tk.INSERT)
                    constructor.setHeaderStartStop(start_index, stop_index)

                    # Make a default destructor function
                    destructor = self.create_function(self.class_model.name, self.class_model.name, '~', '', '', '', 'public')
                    self.class_model.function_list['~' + self.class_model.name] = [2, destructor]
                    self.text.insert(tk.INSERT, '\n')

                    # Insert the destructor into the class body of the header file
                    start_index = self.text.index(tk.INSERT)
                    self.text.insert(start_index, '        ~{}();'.format(self.class_model.name))
                    stop_index = self.text.index(tk.INSERT)
                    destructor.setHeaderStartStop(start_index, stop_index)

                    # Update the cpp file to match the new header layout
                    if self.alternate_type == 'cpp':
                        self.alternate_view.class_name = self.class_model.name
                        # Place the header file include at the start of the file
                        output = '#include "{}.hpp"\n\n'.format(self.class_model.name)
                        self.alternate_view.text.insert('1.0', output)

                        # Insert the constructor and destructor function definitions
                        self.alternate_view.insert_code_function(tk.END, constructor)
                        self.alternate_view.insert_code_function(tk.END, destructor)

                        # Trigger the keyword coloring update
                        self.alternate_view.update_keyword_colors('1.0', tk.END)
                    break

    def update_keyword_colors(self, start, end):
        self.text.tag_remove("keyword", start, end)
        for word in self.keywords:
            idx = start
            while True:
                idx = self.text.search(word, idx, nocase=0, stopindex=end)
                if not idx:
                    break
                found = self.text.get(idx+' wordstart', idx + ' wordend').strip()
                if found == word:
                    self.text.tag_add('keyword', idx+' wordstart', idx + ' wordend')
                    if word == 'public':
                        self.protection_state = 'public'
                    elif word == 'private':
                        self.protection_state = 'private'
                    elif word == 'protected':
                        self.protection_state = 'protected'
                idx = idx + ' wordend+1c'

    def update_comments(self, start, end):
        self.text.tag_remove('comment', start, end)
        lines = self.text.get('1.0', tk.END)
        line_number = 0
        for line in lines.splitlines():
            line_number = line_number + 1
            column = line.find('//')
            if column > -1:
                tag_start = '{}.{}'.format(line_number, column)
                self.text.tag_add('comment', tag_start, '{} lineend'.format(tag_start))

    def check_line(self, event):
        self.text.edit_separator()
        current_position = self.text.index(tk.INSERT)
        start = current_position + ' linestart'
        end = current_position + ' lineend'
        self.update_keyword_colors(start, end)
        self.update_comments(start, end)

    def get_protection_state(self, start_index):
        # Check for protection status last registered at or above the line to process
        protection_state = 'public'
        text = self.text.get('1.0', start_index)
        for line in text.splitlines()[::-1]:
            if line.find('public:')> 0:
                protection_state = 'public'
                break
            elif line.find('private:') > 0:
                protection_state = 'private'
                break
            elif line.find('protected:') > 0:
                protection_state = 'protected'
                break
        return protection_state

    def get_return_type(self, line_text):
        return_type = ''
        special = ''
        if line_text.find('(') > -1:
            line_text = line_text.split('(')[0]
        elif line_text.find(';') > -1:
            line_text = line_text.split(';')[0]
        if line_text.strip()[0] == '~':
            special = '~'
        elif line_text.strip().find('const ') == 0:
            special = 'const'
            elements = line_text.split(' ')
            return_type = ' '.join(elements[1:-1])
        elif line_text.strip().find('static ') == 0:
            special = 'static'
            elements = line_text.split(' ')
            return_type = ' '.join(elements[1:-1])
        else:
            elements = line_text.split(' ')
            return_type = ' '.join(elements[0:-1])
        return return_type, special

    def get_name(self, line_text):
        if line_text.find('(') > -1:
            line_text = line_text.split('(')[0]
        elif line_text.find(';') > -1:
            line_text = line_text.split(';')[0]
        if line_text.strip()[0] == '~':
            name = line_text.strip()[1:]
        else:
            name = line_text.split(' ')[-1]
        return name

    def get_parameters(self, line_text):
        # Separate line by ( and ) to pull out parameters
        params = ''
        location = line_text.find('(')
        if location > -1:
            params = line_text[location+1:-1].split(')')[0].strip()
        return params, location

    def parse_variable_line(self, line_text):
        if line_text.find('(') > -1:
            # This is not a variable line
            return None
        return_type, special_type = self.get_return_type(line_text)
        name = self.get_name(line_text)
        if not (return_type in self.return_types):
            return None
        else:
            # Add it to the variables list
            if not (name in self.class_model.variables_list.keys()):
                new_variable = self.create_variable(name, self.class_model.name, special_type,
                                                    return_type, self.protection_state)
                return new_variable
            else:
                # Update if something changed
                variable = self.class_model.variables_list[name]
                variable.protection = self.protection_state
            return None

    def parse_function_line(self, line_text):
        if line_text.find('(') < 0:
            # This is not a function line
            return None
        return_type, special_type = self.get_return_type(line_text)
        name = self.get_name(line_text)
        if (not (return_type in self.return_types)) and (special_type != '~'):
            return None
        else:
            pass

    def process_line(self, event=None, line_index=None):
        if self.type == 'cpp':
            # Only process hpp file for now. Need different process for cpp
            return
        if not (event is None):
            self.check_line(event)
        if line_index is None:
            current_position = self.text.index(tk.INSERT)
        else:
            current_position = line_index

        # Clear the existing error tags ont the current line before checking for duplicated function name errors
        self.text.tag_remove('error', current_position + ' linestart', current_position + ' lineend')

        # Check for protection status last registered at or above the line to process
        self.protection_state = self.get_protection_state(current_position)

        line = self.text.get(current_position + ' linestart', current_position + ' lineend').strip()
        # Remove any comment blocks on the line
        line = line.split('//')[0].strip()
        # Get the line information: return type, special type, and name
        return_type, special_type = self.get_return_type(line)
        name = self.get_name(line)

        if (name != self.class_model.name) and (return_type not in self.default_return.keys()):
            self.text.tag_add('error', current_position + ' linestart', current_position + ' lineend')
            return
        # Check for type keyword start
        param_split = line.split('(')
        if len(param_split) == 1:
            # Process the line as a variable declaration
            if name not in self.class_model.variables_list.keys():
                new_variable = self.parse_variable_line(param_split[0])
                if new_variable is not None:
                    if new_variable.name in self.class_model.variables_list.keys():
                        # If the function name has already been used, highlight the line, don't create another copy
                        self.text.tag_add('error', current_position + ' linestart', current_position + ' lineend')
                    else:
                        self.class_model.variables_list[new_variable.name] = new_variable
            else:
                self.text.tag_add('error', current_position + ' linestart', current_position + ' lineend')
        elif (name == self.class_model.name)\
                or ((name == self.class_model.name) and (special_type == '~'))\
                or ((return_type in self.return_types) and (len(param_split) > 1)):
            params, params_location = self.get_parameters(line)

            # If this function was called for a new entry rather than a key or time triggered event,
            # fill in the default body content of the cpp file
            if event is not None:
                body = self.default_return[return_type]
                if body != '':
                    body = '    return {};\n'.format(body)
            else:
                body = None

            # Prepare to add the function to the stored list and update the cpp file
            if (self.class_model.name != '') and (self.alternate_type == 'cpp'):
                if (name == self.class_model.name) and (special_type == '~'):
                    name = '~' + name
                if name in self.class_model.function_list.keys():
                    # If the function name has already been used, highlight the line, don't create another copy
                    self.text.tag_add('error', current_position + ' linestart', current_position + ' lineend')
                else:
                    func = self.create_function(name, self.class_model.name, special_type, return_type,
                                                params, body, self.protection_state)
                    func.setHeaderStartStop(current_position + ' linestart', current_position + ' lineend')
                    # Add the function to the list
                    self.class_model.function_list[name] = [len(self.class_model.function_list)+1, func]
                    if not (event is None):
                        # Figure out where to insert the new function in the cpp file
                        current_line = int(current_position.split('.')[0])
                        index = [i for i, x in enumerate(self.current_functions) if x[1] > current_line]
                        if index == []:
                            insert_at = tk.END
                        else:
                            insert_at = self.class_model.function_list[self.current_functions[index[0]][0]][1].code_start
                        self.alternate_view.insert_code_function(insert_at, func)

    def create_variable(self, name, class_name, special_type, return_type, protection_state):
        variable_data = {'classname': class_name,
                         'name': name,
                         'specialtype': special_type,
                         'returntype': return_type,
                         'protection': protection_state}
        new_variable = Variable(variable_data)
        return new_variable

    def create_function(self, name, class_name, special_type, return_type, params, body, protection_state):
        function_data = {'classname': class_name,
                         'name': name,
                         'specialtype': special_type,
                         'returntype': return_type,
                         'parameters': params,
                         'body': body}
        new_func = Function(function_data)
        new_func.setProtectionType(protection_state)
        return new_func

    def insert_code_function(self, index, function):
        start_index = self.text.index(index)
        insert_special = ''
        insert_return = ''
        if function.specialtype == '~':
            insert_special = function.specialtype
        elif function.specialtype != '':
            insert_special = '{} '.format(function.specialtype)
        if function.returntype != '':
            insert_return = '{} '.format(function.returntype)

        output = '{}{}{}::{}({})\n{{\n{}}}\n\n'.format(insert_special,
                                                   insert_return,
                                                   function.classname,
                                                   function.name,
                                                   function.parameters,
                                                   function.body)
        self.text.insert(start_index, output)
        stop_index = self.text.index(tk.INSERT)
        function.setCodeStartStop(start_index, stop_index)
        if function.specialtype == '~':
            self.class_model.function_list['~{}'.format(function.name)]\
                = [len(self.class_model.function_list)+1, function]
        else:
            self.class_model.function_list[function.name]\
                = [len(self.class_model.function_list)+1, function]

    def print_function_list(self, event):
        print('In: ' + self.type)
        print('Start of function list')
        functions = []
        for item_key in self.class_model.function_list.keys():
            func = self.class_model.function_list[item_key][1]
            functions.append(item_key)
            print(' Name: {}'.format(item_key))
            print('      Order Index:       {}'.format(self.class_model.function_list[item_key][0]))
            print('      Name:              {}'.format(func.name))
            print('      Protection:        {}'.format(func.protection))
            print('      Class:             {}'.format(func.classname))
            print('      Returns:           {}'.format(func.returntype))
            print('      Special:           {}'.format(func.specialtype))
            print('      Params:            {}'.format(func.parameters))
            print('      Header start/stop: {}, {}'.format(func.header_start, func.header_end))
            print('      Code start/stop:   {}, {}'.format(func.code_start, func.code_end))
        print('End of function list')
        print('--> List in ' + self.type + ': ')
        print(functions)

    def json_pack(self, event):
        variables = []
        functions = []
        out = {'variable_order': [], 'variables': {}, 'function_order': [], 'functions': {}}
        for item_key in self.class_model.variables_list.keys():
            variables.append(item_key)
            var = self.class_model.variables_list[item_key]
            out['variables'][item_key] = {'name': var.name, 'protection': var.protection, 'classname': var.classname,
                                          'returns': var.returntype, 'special': var.specialtype,
                                          'header_start': var.header_start, 'header_end': var.header_end,
                                          'code_start': var.code_start, 'code_end': var.code_end}
        for item_key in self.class_model.function_list.keys():
            functions.append(item_key)
            func = self.class_model.function_list[item_key][1]
            out['functions'][item_key] = {'name': func.name, 'protection': func.protection, 'classname': func.classname,
                   'returns': func.returntype, 'special': func.specialtype, 'parameters': func.parameters,
                   'header_start': func.header_start, 'header_end': func.header_end,
                   'code_start': func.code_start, 'code_end': func.code_end, 'body': func.body}
        out['variable_order'] = variables
        out['function_order'] = functions
        return out

    def on_undo(self, event):
        try:
            self.text.edit_undo()
        except tk.TclError:
            return

    def on_redo(self, event):
        try:
            self.text.edit_redo()
        except tk.TclError:
            return

    def on_tab(self, event):
        current_line = self.text.index(tk.INSERT)
        self.text.insert(current_line, '    ')
        return 'break'


if __name__ == "__main__":
    root = tk.Tk()
    app = CppCodeText(root)
    app.pack()
    app.mainloop()
