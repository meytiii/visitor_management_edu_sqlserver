import tkinter as tk
from tkinter import ttk

class RoundedEntry(tk.Canvas):
    def __init__(self, parent, width=200, height=30, radius=15, 
                 bg="white", border_color="#E0E0E0", 
                 text_var=None, show=None, justify='center', font=("Tahoma", 11)):
        super().__init__(parent, width=width, height=height, 
                         bg=parent["bg"], highlightthickness=0)
        self.entry_bg = bg
        
        self.create_polygon(
            radius, 0, width-radius, 0, width, 0, width, radius,
            width, height-radius, width, height, width-radius, height,
            radius, height, 0, height, 0, height-radius, 0, radius, 0, 0,
            smooth=True, fill=bg, outline=border_color, width=1
        )
        
        self.entry = tk.Entry(self, bg=bg, bd=0, highlightthickness=0, 
                              fg="#333333", justify=justify, font=font,
                              textvariable=text_var, show=show)
        
        self.create_window(width//2, height//2, window=self.entry, width=width-20)

    def get(self):
        return self.entry.get()

    def delete(self, first, last=tk.END):
        self.entry.delete(first, last)

    def focus(self):
        self.entry.focus()
        
    def bind(self, sequence=None, func=None, add=None):
        self.entry.bind(sequence, func, add)

class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None,
                 width=260, height=44,
                 radius=22,
                 bg="#1976D2",
                 hover_bg="#1565C0",
                 fg="white",
                 font=("Tahoma", 11, "bold")):
        super().__init__(parent, width=width, height=height,
                         bg=parent["bg"], highlightthickness=0)
        self.command = command
        self.bg = bg
        self.hover_bg = hover_bg
        self.rect = self.create_polygon(
            radius, 0,
            width-radius, 0,
            width, 0,
            width, radius,
            width, height-radius,
            width, height,
            width-radius, height,
            radius, height,
            0, height,
            0, height-radius,
            0, radius,
            0, 0,
            smooth=True,
            fill=bg,
            outline=""
        )
        self.text_item = self.create_text(
            width//2, height//2,
            text=text, fill=fg, font=font
        )
        self.bind("<Enter>", lambda e: self.itemconfig(self.rect, fill=hover_bg))
        self.bind("<Leave>", lambda e: self.itemconfig(self.rect, fill=bg))
        self.bind("<Button-1>", lambda e: command() if command else None)

class AutocompleteEntry(ttk.Entry):
    def __init__(self, master, completevalues=None, selection_callback=None, **kwargs):
        super().__init__(master, **kwargs)
        self.completevalues = sorted(completevalues) if completevalues else []
        self.selection_callback = selection_callback
        self.var = self["textvariable"]
        if self.var == '':
            self.var = tk.StringVar()
            self["textvariable"] = self.var
        
        self.var.trace('w', self.changed)
        self.bind("<Right>", self.selection)
        self.bind("<Up>", self.move_up)
        self.bind("<Down>", self.move_down)
        self.bind("<Return>", self.selection)
        self.bind("<FocusOut>", self.hidetip)
        
        self.lb_up = False
        self._after_id = None

    def changed(self, name, index, mode):
        if self.var.get() == '':
            self._destroy_lb()
            return
        words = self.comparison()
        if words:
            if not self.lb_up:
                self.lb = tk.Listbox(self.master, width=self["width"], height=8, font=self["font"], bd=1, relief=tk.SOLID)
                self.lb.bind("<ButtonRelease-1>", self.selection)
                self.lb.bind("<Right>", self.selection)
                self.lb.place(x=self.winfo_x(), y=self.winfo_y() + self.winfo_height())
                self.lb.lift() 
                self.lb_up = True
            
            self.lb.delete(0, tk.END)
            for w in words:
                self.lb.insert(tk.END, w)
        else:
            self._destroy_lb()

    def comparison(self):
        pattern = self.var.get().lower()
        return [w for w in self.completevalues if w.lower().startswith(pattern)]

    def selection(self, event):
        if self._after_id:
            self.after_cancel(self._after_id)
            self._after_id = None
        if self.lb_up:
            selected_val = None
            if event and event.widget == self.lb:
                try:
                    index = self.lb.nearest(event.y)
                    selected_val = self.lb.get(index)
                except: pass
            else:
                try:
                    if self.lb.curselection():
                        selected_val = self.lb.get(self.lb.curselection())
                except: pass
            
            if selected_val:
                self.var.set(selected_val)
                if self.selection_callback:
                    self.selection_callback(selected_val)
            
            self._destroy_lb()
            self.icursor(tk.END)
            self.tk_focusNext().focus()
            return "break"

    def move_up(self, event):
        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != '0':
                self.lb.selection_clear(first=index)
                index = str(int(index) - 1)
                self.lb.selection_set(first=index)
                self.lb.activate(index)

    def move_down(self, event):
        if self.lb_up:
            if self.lb.curselection() == ():
                index = '0'
            else:
                index = self.lb.curselection()[0]
            if index != str(self.lb.size() - 1):
                self.lb.selection_clear(first=index)
                index = str(int(index) + 1)
                self.lb.selection_set(first=index)
                self.lb.activate(index)

    def hidetip(self, event=None):
        if self.lb_up:
            self._after_id = self.after(200, self._destroy_lb)
    
    def _destroy_lb(self):
        if self.lb_up:
            self.lb.destroy()
            self.lb_up = False
            self._after_id = None
            
    def set_completion_list(self, completion_list):
        self.completevalues = sorted(completion_list)