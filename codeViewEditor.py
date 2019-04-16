from tkinter import *
import tkinter.filedialog as FileDialog
import tkinter.messagebox as MessageBox
import UML
import CodeText
from Objects import ClassModel
import os.path
import json

code_dir = 'code'
try:
    os.listdir(code_dir)
except FileNotFoundError:
    os.mkdir(code_dir)


def new_files():
    global header, source, header_label, source_label, uml_label
    class_model.make_new()
    header.make_new()
    source.make_new()
    uml_label.config(text='?.uml', bg='#FFFF00')
    header_label.config(text='?.hpp', bg='#00FF00')
    source_label.config(text='?.cpp', bg='#00FF00')


def save_as():
    global header, source
    t = header.text.get("1.0", "end-1c")
    t2 = source.text.get("1.0", "end-1c")
    save_location = FileDialog.asksaveasfilename(initialdir=code_dir, initialfile=class_model.name)
    if save_location == '':
        return
    answer = True
    if os.path.isfile(save_location + '.hpp') or os.path.isfile(save_location + '.cpp'):
        answer = MessageBox.askyesno('Files already exists.', 'Overwrite?')
    if answer is True:
        with open(save_location + ".hpp", "w") as file:
            file.write(t)
        with open(save_location + ".cpp", "w") as file:
            file.write(t2)
        with open(save_location + '.json', 'w') as file:
            file.write(json.dumps(header.json_pack(), indent=4))

        filename = save_location.rsplit('/', 1)[-1]
        uml_label.config(text=str(filename + '.uml'), bg='#00FF00')
        header_label.config(text= str(filename + '.hpp'), bg='#00FF00')
        source_label.config(text= str(filename + '.cpp'), bg='#00FF00')
        header.text.edit_modified(FALSE)
        source.text.edit_modified(FALSE)


def load_files():
    global header, source, uml_label, header_label, source_label
    infilenamebase = FileDialog.askopenfilename(initialdir=code_dir,
                                                filetypes=[('JSON files', '*.json'), ('Header files', '*.hpp'),
                                                           ('C++ files', '*.cpp'), ('All files', '*.*')])
    if infilenamebase.endswith(".hpp") or infilenamebase.endswith(".cpp") or infilenamebase.endswith(".json"):
        infilenamebase = infilenamebase.rsplit('.', 1)[0]
    print(infilenamebase)
    if infilenamebase == '':
        return
    with open(infilenamebase+".json", "rt") as infile:
        data = json.load(infile)
    with open(infilenamebase+".hpp", "r") as infile:
        header_in = infile.readlines()
    with open(infilenamebase+".cpp", "r") as infile:
        codedecl = infile.readlines()

    header_in = ''.join(header_in)
    codedecl = ''.join(codedecl)

    filename = infilenamebase.rsplit('/', 1)[-1]
    class_model.make_new()
    class_model.name = filename
    header.make_new()
    source.make_new()
    header.json_unpack(data)

    header.text.insert('1.0', header_in)
    source.text.delete('1.0', END)
    source.text.insert('1.0', codedecl)
    uml_label.config(text=str(filename + '.uml'), bg='#FFFF00')
    header_label.config(text= str(filename + '.hpp'), bg='#00FF00')
    source_label.config(text= str(filename + '.cpp'), bg='#00FF00')
    header.class_defined = True


def check_updates(event):
    global header_label, header, source_label, source
    if header.text.edit_modified():
        header_label.config(bg='#FFFF00')
    if source.text.edit_modified():
        source_label.config(bg='#FFFF00')


if __name__ == "__main__":
    base = Tk()
    base.title('MultiView Code Editor')
    theme_color = '#AAAAAA'

    root = PanedWindow(base, bg=theme_color, orient=HORIZONTAL, showhandle=1, sashpad='3', handlepad=3, handlesize=10)
    root.pack(side=BOTTOM, fill=BOTH, expand=1)
    root.grid_rowconfigure(0, weight=1)
    root.grid_rowconfigure(1, weight=1)
    root.grid_rowconfigure(2, weight=10)
    root.grid_columnconfigure(0, weight=1)
    root.grid_columnconfigure(1, weight=1)
    root.grid_columnconfigure(2, weight=1)

    controls_frame = Frame(root, bg=theme_color)
    uml_frame = Frame(root, bg=theme_color)
    header_frame = Frame(root, bg=theme_color)
    source_frame = Frame(root, bg=theme_color)

    button_new = Button(controls_frame, text="New", command=new_files, borderwidth=5,
                        highlightcolor='black')
    button_save = Button(controls_frame, text="Save", command=save_as, borderwidth=5,
                         highlightcolor='black')
    button_load = Button(controls_frame, text="Load", command=load_files, borderwidth=5,
                         highlightcolor='black')
    controls_frame.grid(row=0, column=0)
    button_new.pack(pady=5)
    button_save.pack(pady=5)
    button_load.pack(pady=5)

    uml_label = Label(uml_frame, text="UML Class", bg='gray', borderwidth=1)
    header_label = Label(header_frame, text="Header", bg='gray', borderwidth=1)
    source_label = Label(source_frame, text="Definition/Source", bg='gray', borderwidth=1)

    class_model = ClassModel()
    uml_class = UML.UmlClassDiagram(uml_frame, class_model)
    header = CodeText.CppCodeText(header_frame, 'hpp', class_model)
    source = CodeText.CppCodeText(source_frame, 'cpp', class_model)
    header.connect_alternate_view('cpp', source)
    header.connect_uml_class_view(uml_class)
    source.connect_alternate_view('hpp', header)
    uml_class.connect_header_view(header)

    uml_frame.grid(row=1, column=0)
    uml_label.pack()
    uml_class.pack(fill=BOTH, expand=1)

    header_frame.grid(row=0, column=1)
    header_label.pack(side=TOP)
    header.pack(side=BOTTOM, fill=BOTH, expand=1)

    source_frame.grid(row=1, column=1)
    source_label.pack()
    source.pack(fill=BOTH, expand=1)

    root.paneconfig(controls_frame, width = 60, height = 100, sticky = N)
    root.paneconfig(uml_frame, width = 500, height = 600, sticky = E+W+S+N)
    root.paneconfig(header_frame, width = 500, height = 600, sticky = E+W+S+N)
    root.paneconfig(source_frame, width = 500, height = 600, sticky = E+W+S+N)

    header.text.bind("<<Modified>>", check_updates)
    source.text.bind('<<Modified>>', check_updates)

    root.mainloop()
