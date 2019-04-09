import tkinter as tk
from tkinter import font
from PIL import Image, ImageDraw

from Objects import ClassBox

class UmlClassDiagram(tk.Frame):
    def __init__(self, parent, class_model):
        tk.Frame.__init__(self, parent)
        self.class_model = class_model

        theme_color = '#AAAAAA'
        parent.configure(bg=theme_color, takefocus=1)
        self.font = font.Font(family='Courier', size=13)
        self.canvas = tk.Canvas(background="white", scrollregion=(0,0,300,600), takefocus=1,
                                borderwidth=3, highlightthickness=5,
                                highlightbackground='gray', highlightcolor='red')
        self.vsb = tk.Scrollbar(bg='black', orient="vertical", borderwidth=2, command=self.canvas.yview)
        self.hsb = tk.Scrollbar(bg='black', orient='horizontal', borderwidth=2, command=self.canvas.xview)
        self.vsb.pack(in_=self, side="right", fill="y", expand=False)
        self.hsb.pack(in_=self, side="bottom", fill="x", expand=False)
        self.canvas.configure(xscrollcommand=self.hsb.set, yscrollcommand=self.vsb.set)
        self.canvas.pack(in_=self, side="left", fill="both", expand=True)

        self.classDiagram = ClassBox()

        # Set the default locations of the diagram separator lines
        self.member_line = 2
        self.method_line = 5

        self.right_click_active = False
        self.canvas.bind('<Button-1>', self.on_left_click)
        self.canvas.bind('<Button-2>', self.on_right_click)
        self.canvas.bind('<MouseWheel>', self.on_mouse_wheel)

        self.draw_diagram()

    def make_new(self):
        # Set the default locations of the diagram separator lines
        self.member_line = 2
        self.method_line = 5
        self.draw_diagram()

    def on_left_click(self, event):
        print('Click!')
        # print(self.focus)
        # print(self.tk_focusPrev())
        # print(self.tk_focusNext())
        self.canvas.focus_force()

    def on_right_click(self, event):
        print('Right click')

    def on_mouse_wheel(self, event):
        # print(event)
        if event.state == 1:
            self.canvas.xview_scroll(-1 * event.delta, 'units')
        else:
            self.canvas.yview_scroll(-1 * event.delta, 'units')

    def draw_diagram(self):
        self.canvas.delete('all')
        rectangle_tag = self.canvas.create_rectangle(self.classDiagram.getBox(), fill='#FFFFCC', width=3)
        max_width = 10
        line = self.member_line + 1
        # Show the list of variables
        if self.class_model.variables_list != {}:
            for key in self.class_model.variables_ordered_list:
                variable = ''
                var = self.class_model.variables_list[key]
                if var.protection == 'public':
                    variable = '+ '
                elif var.protection == 'private':
                    variable = '- '
                elif var.protection == 'protected':
                    variable = '~ '
                variable = '{}{} : '.format(variable, key)
                if var.specialtype != '':
                    variable = '{}{} '.format(variable, var.specialtype)
                variable = '{}{}'.format(variable, var.returntype)
                if len(variable) > max_width:
                    max_width = len(variable)
                self.add_text(line, variable)
                line = line + 1
        self.method_line = line
        line = line + 1
        # Show the list of functions
        if self.class_model.function_list != {}:
            for key in self.class_model.function_ordered_key_list:
                method = ''
                func = self.class_model.function_list[key[0]][1]
                if func.protection == 'public':
                    method = '+ '
                elif func.protection == 'private':
                    method = '- '
                elif func.protection == 'protected':
                    method = '~ '
                if func.returntype == '':
                    returntype = 'void'
                else:
                    returntype = func.returntype
                method = '{}{}({}) : {}'.format(method, key[0], func.parameters, returntype)
                if len(method) > max_width:
                    max_width = len(method)
                self.add_text(line, method)
                line = line + 1
        if self.class_model.function_list == {}:
            height = self.method_line + 4
        else:
            height = self.method_line + len(self.class_model.function_list) + 1
        self.classDiagram.setWidthHeight(max_width + 4, height)
        self.classDiagram.updateTopBottom()

        self.add_line(self.member_line)
        self.add_line(self.method_line)
        if self.class_model.name == None:
            self.add_text(1, '<<Class>>', False)
        else:
            self.add_text(1, self.class_model.name, False)
        # Update the background rectangle
        self.canvas.delete(rectangle_tag)
        rectangle_tag = self.canvas.create_rectangle(self.classDiagram.getBox(), fill='#FFFFCC', width=3)
        self.canvas.tag_lower(rectangle_tag)
        self.canvas.configure(scrollregion=self.classDiagram.getBox())
        self.after(1000, self.draw_diagram)

    def add_text(self, line, text, justify=True):
        # text is centered
        height = self.classDiagram.top + line * self.classDiagram.line_height
        if justify is True:
            self.canvas.create_text(self.classDiagram.left + 4, height, text=text, font=self.font, anchor=tk.W)
        else:
            offset = (self.classDiagram.left + self.classDiagram.right) / 2
            self.canvas.create_text(offset, height, text=text, font=self.font, anchor=tk.CENTER)

    def add_line(self, line):
        height = self.classDiagram.top + line * self.classDiagram.line_height
        self.canvas.create_line(self.classDiagram.left, height,
                                self.classDiagram.right, height,
                                fill='black', width=3)

    def get_image(self):
        self.canvas.postscript(file="my_drawing.ps", colormode='color')
        image = Image.new("RGB", (self.classDiagram.width, self.classDiagram.height), 'white')
        draw = ImageDraw.Draw(image)
        return image
