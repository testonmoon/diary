import tkinter as tk

window = tk.Tk()

name_label = tk.Label(text="Name")
name_label.config(font=("consolas", 12))
name_label.grid(row=0, column=0, sticky="nsew")
name_entry = tk.Entry()
name_entry.grid(row=1, column=0, sticky="nsew")

content_label = tk.Label(text="Content").grid(row=2, column=0, sticky="nsew")
content_entry = tk.Text(borderwidth=3, relief="sunken")
content_entry.config(font=("consolas", 12), undo=True, wrap='word')
content_entry.grid(row=3, column=0, sticky="nsew")
scrollb = tk.Scrollbar(command=content_entry.yview)
scrollb.grid(row=3, column=1, sticky='nsew')
content_entry['yscrollcommand'] = scrollb.set

def post():
    title = name_entry.get()
    lines = content_entry.get("1.0", tk.END).splitlines()
    print(title, lines)

tk.Button(text='Post!', command=post).grid(row=4, column=0)

window.mainloop()
