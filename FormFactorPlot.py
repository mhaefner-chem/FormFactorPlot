# -*- coding: utf-8 -*-
"""
Created on Mon Feb 12 19:25:17 2024

Copyright (c) 2024, Michael Häfner
Full copyright note in LICENSE

"""

import tkinter as tk
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter import messagebox
from matplotlib.figure import Figure 
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,  
NavigationToolbar2Tk) 
import matplotlib.pyplot as plt
import matplotlib as mpl
import numpy as np
import os, math

class data:
    def __init__(self,filename,origin):
        self.filename = filename
        
        self.expansion = 5 # size of the expansion in Gaussians, 4 for set-size 9 and 5 for set-size 11, current max
        
        self.labels = []
        self.data = []
        self.valid = True
        
        self.retrieve_data(filename)
        
        if self.valid == True:
            self.sort_data()
    
    
    # feeds in the data from the csv
    def retrieve_data(self,filename):
        with open(filename,mode="r") as file:
            lines = file.readlines()
            for line in lines:
                if "source" in line.lower():
                    tmp = line.split(",")
                    # make everything lowercase for convenience
                    for item in tmp:
                        self.labels.append(item.lower())
                    break
            self.check_labels()
               
            for line in lines:
                if not "source" in line.lower():
                    self.data.append(line.split(","))
        
    
    # checks if all important labels are given
    def check_labels(self):
        
        errors = ""
        
        checks = ["source","set-type","element","ox.","c"]
        
        # add the parameters for the Gaussians
        for i in range(1,self.expansion+1):
            checks.append("a"+str(i))
            checks.append("b"+str(i))
        
        for check in checks:
            if not check in self.labels:
                errors += "No column {} specified with '{}'.\n".format(check,check)

            
        if len(errors) > 0:
            errors += "Make sure that the file is a properly formatted csv with commas (,) as separators no additional line breaks."
            messagebox.showerror("Error in input file!", errors)
            self.valid = False
            
    
    def sort_data(self):
        # commentary if read ran into formatting troubles
        self.comment = [""] * len(self.data)
        # create list of oxidation states
        flip = False
        self.ox_list = [""] * len(self.data)
        for i in range(len(self.data)):
            try:
                ox = int(self.data[i][self.labels.index("ox.")])
            except:
                if flip == False:
                    flip = True 
                    self.comment[i] += "ox. "
                    # !!! ADD LATER
                    # messagebox.showwarning("showwarning", "Non-int oxidation state(s) found. Defaulting to 0 for now. Please check input file.")
                ox = 0
            self.ox_list[i] = ox
        
        
        # create list of elements, read out oxi states if existing
        self.el_list = [""] * len(self.data)
        for i in range(len(self.data)):
            tmp = self.data[i][self.labels.index("element")]
            el = ""
            num = ""
            if "+" in tmp or "-" in tmp:
                # print(123, tmp)
                extract = "1234567890+-"
                for j in tmp:
                    if j not in extract:
                        el += j
                    elif j == "+" or j == "-":
                        sign = j
                    else:
                        num += j
                # print(el,int(sign+num))
            else:
                el = tmp
                        
            
            if "val" in el:
                self.comment[i] += "valence "
                el = el.split("val")[0]
            
            self.el_list[i] = el
            if num != "":
                self.ox_list[i] = int(sign+num)
            
            
        # create list of data sources
        self.sources_list = [""] * len(self.data)
        for i in range(len(self.data)):
            source = self.data[i][self.labels.index("source")]
            self.sources_list[i] = source
            
        # create list of fitting set size
        self.set_list = [""] * len(self.data)
        for i in range(len(self.data)):
            set_type = int(self.data[i][self.labels.index("set-type")])
            self.set_list[i] = set_type
            
        self.a_list = [0] * len(self.data)
        for i in range(len(self.data)):
            tmp = []
            # print(round((self.set_list[i]-1)/2)-1,self.set_list[i])
            for j in range(1,round((self.set_list[i]-1)/2)-1):
                a_j = self.data[i][self.labels.index("a"+str(j))]
                try:
                    tmp.append(float(a_j))
                except:
                    tmp.append(0)
                    self.comment[i] += "a{} ".format(j)
            self.a_list[i] = tmp
        
        self.b_list = [0] * len(self.data)
        for i in range(len(self.data)):
            tmp = []
            for j in range(1,round((self.set_list[i]-1)/2)-1):
                b_j = self.data[i][self.labels.index("b"+str(j))]
                try:
                    tmp.append(float(b_j))
                except:
                    tmp.append(0)
                    self.comment[i] += "b{} ".format(j)
            self.b_list[i] = tmp
     
        self.c_list = [0] * len(self.data)
        for i in range(len(self.data)):
            c = self.data[i][self.labels.index("c")]
            try:
                self.c_list[i] = float(c)
            except:
                self.c_list[i] = 0
                self.comment[i] += "c ".format(j)
     

# creates the search window

class search_window:
    # initializes the class based on the csv
    def __init__(self):
        
        self.root = create_window("350x50+120+120", "Atomic Form Factor Selector")
            
        self.frame_selection_buttons()
        self.open_button()
        self.root.mainloop()
        
    
    def frame_selection_buttons(self):
        self._frame_buttons = tk.Frame(self.root)
        self._frame_buttons.pack(side=tk.TOP,fill=tk.X)
        sep = ttk.Separator(self._frame_buttons,orient='horizontal')
        sep.pack(side=tk.BOTTOM,fill=tk.X)
        
    def open_button(self):
    
        open_button = ttk.Button(
            self._frame_buttons,
            text='Open CSV',
            command = lambda: select_file()
        )
        open_button.pack(side=tk.LEFT,expand=True)
        
        def select_file():
            
            filetypes = (
                ('csv files', '*.csv'),
                ('All files', '*.*')
            )
            
            filename = fd.askopenfilename(
                title='Open CSV',
                initialdir='./',
                filetypes=filetypes)
            if os.path.isfile(filename) == True:
                self.build_rest(filename)
            else:
                messagebox.showerror("Error in input file!", "Input file could not be found!")
                
        make_button = ttk.Button(
            self._frame_buttons,
            text='Make Example CSV',
            command = lambda: save_file()
        )
    
        make_button.pack(side=tk.LEFT,expand=True)
        
        def save_file():
            Files = [('CSV File', '*.csv'),
                ('All Files', '*.*')]
            savefile = fd.asksaveasfile(filetypes = Files, defaultextension = Files)
            with savefile as f:
                f.write("source,set-type,element,ox.,a1,b1,a2,b2,a3,b3,a4,b4,a5,b5,c,comment\n")
                f.write("ITC,9,H,0,0.489918,20.6593,0.262003,7.74039,0.196767,49.5519,0.049879,2.20159,,,0.001305,This is an example\n")
    
        about_button = ttk.Button(
            self._frame_buttons,
            text='About',
            command = lambda: about()
        )
    
        about_button.pack(side=tk.RIGHT,expand=True)
        
        def about():
            about = create_window("650x400+120+120", "About FormFactorPlot")
            about.config(bg='#AAAAAA')
            
            message ='''FormFactorPlot allows the plotting of provided atomic XRD form factors.
Version 1.0.1

MIT License
Copyright (c) 2024 mhaefner-chem
Contact: michael.haefner@uni-bayreuth.de

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

            
            text_box = tk.Text(
                about
            )
            text_box.pack(expand=True,fill=tk.X)
            text_box.insert('end', message)
            text_box.config(state='disabled')
    
    def build_rest(self, filename):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.frame_selection_buttons()
        self.open_button()
        self.filename = filename
        self.data = data(filename,self.root)
        if self.data.valid == True:
            self.root.geometry("500x600")
            self.key = {}
            self._search = {}
            self.window()
        else:
            self.root.geometry("200x50")
    
        
    def stringify_data(self, data, keys, listbox):
        concatenate = ""
        
        max_len = 6
        for i in keys:
            str_len = len(data.sources_list[i])
            if str_len > max_len:
                max_len = str_len
        custom_str = "{:>"+str(max_len)+"} "
        
        for i in keys:
                    concatenate = ""
                    concatenate += "{:5} ".format(i)
                    concatenate += custom_str.format(data.sources_list[i])
                    concatenate += "{:8} ".format(data.set_list[i])
                    concatenate += "{:5} ".format(data.el_list[i])
                    if data.ox_list[i] > 0:
                        concatenate += "{:3} ".format("+"+str(data.ox_list[i]))
                    else:
                        concatenate += "{:3} ".format(str(data.ox_list[i]))
                    concatenate += "{}".format(data.comment[i])
                    listbox.insert("anchor", concatenate)
        return concatenate
    
    def window(self):
        def frame_label(text):
			#"Contains the listbox"
            self._frame_label = tk.Frame(self.root)
            self._frame_label.pack(side=tk.TOP)
            self._label = ttk.Label(self._frame_label,text=text)
            self._label.pack(side=tk.LEFT)
            
        
        # contains the search box
        def frame_search():
			#"Contains the listbox"
            self._frame_search = tk.Frame(self.root)
            self._frame_search.pack(side=tk.TOP) # adapt the frame to the window
            
        def search(setting):
            self._search_label = ttk.Label(self._frame_search)
            if setting == "el":
                self._search_label["text"] = "Filter for Element:"
            elif setting == "source":
                self._search_label["text"] = "Filter for Data Source:"
            elif setting == "index":
                self._search_label["text"] = "Filter by Index, e.g., '1,2,43':"
            if not setting == "reset":
                self._search_label.pack(side=tk.LEFT)
            
                self.key[setting] = tk.StringVar()
                self._search[setting] = ttk.Entry(
                    self._frame_search,
                    textvariable=self.key[setting]
                )
            
                self._search[setting].pack(side=tk.LEFT)
            
            
            if setting == "reset":
                self._search_button = ttk.Button(self._frame_buttons,
                           command = lambda: refresh(setting))
            else:
                self._search_button = ttk.Button(self._frame_search,
                           command = lambda: refresh(setting))
                
            if setting == "reset":
                self._search_button["text"] =  "Reset Selection & Filter"
                self._search_button.pack(side=tk.LEFT,expand=True)
            else:
                self._search_button["text"] = "Apply"
                self._search_button.pack(side=tk.LEFT)
            
            def refresh(setting):
                  
                def get_subset(str, data, setting):
                    new_data = []
                    keys = []
                    perfect_match = False
                    if setting == "el":
                        check = self.data.el_list
                        perfect_match = True
                    if setting == "source":
                        check = self.data.sources_list
                    
                    if str == "" or str == "All" or setting == "reset":
                        new_data = data
                        for i in range(len(data)):
                            keys.append(i)
                            
                    elif setting == "index":
                        for i in str.split(","):
                            try:
                                i = int(i)
                            except:
                                messagebox.showerror("Input Error", "Only numbers, spaces, and commas are valid inputs.")
                                break
                            if i > len(data):
                                messagebox.showerror("Input Error", "Numbers must be between {} and {}.".format(0,len(data)-1))
                                break
                            new_data.append(data[i])
                            keys.append(i)
                    else:
                        for i in range(len(data)):
                            if str == check[i] and perfect_match == True or str in check[i] and perfect_match == False:
                                new_data.append(data[i])
                                keys.append(i)
                                
                    return new_data, keys
                
                if setting == "reset":
                    data, keys = get_subset("",self.data.data,setting)
                else:
                    data, keys = get_subset(self._search[setting].get(),self.data.data,setting)
                    self._search[setting].delete(0, "end")
                    
                self._lbx.delete(0, "end")
                self.stringify_data(self.data,keys,self._lbx)
                
                
            
        #contains the listbox"
        def frame_listbox():
			#"Contains the listbox"
            self._frame = tk.Frame(self.root, bg="gold")
            self._frame.pack(expand=True, fill=tk.BOTH) # adapt the frame to the window
            
        def label_listbox():
            self._label_frame = tk.Frame(self._frame, bg="white")
            self._label_frame.pack(side=tk.TOP, expand=False, fill=tk.X) # adapt the frame to the window
            self._label = tk.Label(self._label_frame, bg="white")
            
            # setup for labels
            max_len = 6
            for i in range(len(self.data.data)):
                str_len = len(self.data.sources_list[i])
                if str_len > max_len:
                    max_len = str_len
            custom_str = "{:>"+str(max_len)+"} "
            
            concatenate = ""
            concatenate += "{:5} ".format("Index")
            concatenate += custom_str.format("Source")
            concatenate += "{:8} ".format("Set-size")
            concatenate += "{:5} ".format("El.")
            concatenate += "{:3} ".format("Ox.")
            concatenate += "{:}".format("Formatting Warning")
            
            
            self._label["text"] = concatenate
            self._label["font"] = "TkFixedFont"
            self._label.pack(side=tk.LEFT, expand=False)
            
        def listbox():
 			#"The list goes here"
            self._lbx = tk.Listbox(self._frame, bg="white", selectmode=tk.MULTIPLE)
            # self._lbx.bind("<Double-Button-1>",
                           # lambda x: items_selected())
            self._lbx["font"] = "TkFixedFont"
            self._lbx.pack(side=tk.LEFT, expand=True, fill=tk.BOTH) # adapt the listbox to the frame
            def additems():
                keys = range(len(self.data.data))
                self.stringify_data(self.data,keys,self._lbx)
                    
            additems()
            
            
        
        def scrollbar():
            self._scrbar = ttk.Scrollbar(
                self._frame,
                orient=tk.VERTICAL,
                command=self._lbx.yview)
            self._lbx["yscrollcommand"] = self._scrbar.set
            self._scrbar.pack(side=tk.LEFT, fill=tk.Y)
        
        def use_selection():
            self._apply_button = ttk.Button(self._frame_buttons,
                           command = lambda: items_selected())
            self._apply_button["text"] = "Plot Selected"
            self._apply_button.pack(side=tk.LEFT,expand=True)
            
            def items_selected():
                # get all selected indices
                selected_indices = self._lbx.curselection()
                print(selected_indices)
                # get selected items
                choice = []
                for i in selected_indices:
                    selected_option = self._lbx.get(i)
                    print(f'You selected: {selected_option}')
                    print(self.data.data[int(selected_option.split()[0])])
                    choice.append(int(selected_option.split()[0]))
                plot = plot_window(choice,self.data)
        
        def widgets_order():
            frame_search()
            search("el")
            frame_label("or")
            
            frame_search()
            search("source")
            frame_label("or")
            
            frame_search()
            search("index")
    
            frame_search()
            search("reset")
            use_selection()
            
            frame_listbox()
            label_listbox()
            listbox()
            scrollbar()
            
        widgets_order()
        

class plot_window:
    # initializes the class based on the csv
    def __init__(self,keys,data):
        
        self.root = create_window("1000x700+120+120", "Atomic Form Factor Plot")
            
        self.keys = keys
        self.data = data
        
        self.mode = "theta"
        self.lambda_default = 0.709319
        self.lambda_set = str(self.lambda_default)
        
        self.draw_window()
        self._entry_mode_theta.insert(tk.END, self.lambda_set)
        
    def draw_window(self):
        self.buttons_frame()
        self.plot_form_factors()
    
    def mode_switch(self,mode):
        self.mode = mode
        try:
            float(self._entry_mode_theta.get())
            self.lambda_set = self._entry_mode_theta.get()
        except:
            messagebox.showerror("Input Error", "Only numbers are valid inputs.")
            self.lambda_set = self.lambda_default
        
        for widget in self.root.winfo_children():
            widget.destroy()
        self.draw_window()
        self._entry_mode_theta.insert(tk.END, self.lambda_set)
    
    def buttons_frame(self):
        self._frame_buttons = tk.Frame(self.root)
        self._frame_buttons.pack(side=tk.TOP,fill=tk.X)
        sep = ttk.Separator(self._frame_buttons,orient='horizontal')
        sep.pack(side=tk.BOTTOM,fill=tk.X)
        
        
        def buttons():
        
            self._button_mode_q = ttk.Button(self._frame_buttons,
                           command = lambda: self.mode_switch("q"))
            self._button_mode_q["text"] = "Calculate for x in q [1/Å]"
            self._button_mode_q.pack(side=tk.LEFT)    
        
            self._label_mode_theta = ttk.Label(self._frame_buttons)
            self._label_mode_theta["text"] = "Characteristic Wavelength [Å]:"
            self._label_mode_theta.pack(side=tk.LEFT)
            
            self.angle = tk.StringVar()
            self._entry_mode_theta = ttk.Entry(
                self._frame_buttons,
                textvariable=self.angle
            )
            self._entry_mode_theta.pack(side=tk.LEFT)
            

            self._button_mode_theta = ttk.Button(self._frame_buttons,
                           command = lambda: self.mode_switch("theta"))
            self._button_mode_theta["text"] = "Calculate for x in 2θ [°]"
            self._button_mode_theta.pack(side=tk.LEFT)
            
            def save_file():
                Files = [('CSV File', '*.csv'),
                    ('All Files', '*.*')]
                self.savefile = fd.asksaveasfile(filetypes = Files, defaultextension = Files)
                with self.savefile as f:
                    if self.mode == "q":
                        f.write("q/[1/Å]")
                    elif self.mode == "theta":
                        f.write("2theta/[°]")
                    for key in self.keys:
                        f.write(" "+self.labels(key,"short"))
                    f.write("\n")
                    for i in range(len(self.x_save)):
                        if self.x_save[i] < 180.0:
                            f.write("{:6.3f}".format(self.x_save[i]))
                            for j in range(len(self.y_save)):
                                f.write(" {:8.4f}".format(self.y_save[j][i]))
                            f.write("\n")
            
            def save_plot():
                Files = [("PNG File", '*.png'),
                         ("SVG File", "*.svg"),
                         ("EPS File", "*.eps"),
                    ('All Files', '*.*')]
                filename = fd.asksaveasfilename(filetypes = Files, defaultextension = Files)
                format_type = filename.split(".")[-1]
                self.fig.savefig(filename, format=format_type,bbox_inches="tight",dpi=300)
            
            self._button_save_values = ttk.Button(self._frame_buttons, text = 'Save Data', command = lambda : save_file())
            self._button_save_values.pack(side=tk.LEFT)
            self._button_save_plot = ttk.Button(self._frame_buttons, text = 'Save Plot', command = lambda : save_plot())
            self._button_save_plot.pack(side=tk.LEFT)
            
                
        buttons()
    
    def labels(self,key,setting):
        # define the label for each plotted element
        label = ""
        if setting == "long":
            label += "item "+str(key)+" "
            label += "from "+self.data.sources_list[key]+": "
            label += self.data.el_list[key]
            if not self.data.ox_list[key] == 0:
                if self.data.ox_list[key] > 0:
                    label += "+"+str(self.data.ox_list[key])
                else:
                    label += str(self.data.ox_list[key])
            if "ale" in self.data.comment[key]:
                label += " valence"
            label += ", parameters: "+str(self.data.set_list[key])
        elif setting == "short":
            label += str(key)+"_"
            label += self.data.sources_list[key].replace(" ","_")+"_"
            label += self.data.el_list[key]
            if not self.data.ox_list[key] == 0:
                if self.data.ox_list[key] > 0:
                    label += "+"+str(self.data.ox_list[key])+"_"
                else:
                    label += str(self.data.ox_list[key])+"_"
            if "ale" in self.data.comment[key]:
                label += " val"
            label += str(self.data.set_list[key])
        return label
    
        
    def plot_form_factors(self): 
  
        # the figure that will contain the plot 
        self.fig = Figure(figsize = (8, 6), 
                     dpi = 100) 
        
        # adding the subplot 
        ax = self.fig.add_subplot()         
        self.y_save = []
        
        if self.mode == "q":
            x_base = np.linspace(0,25,num=251)
        elif self.mode == "theta":
            x_base = np.linspace(0,25,num=1001)
        for key in self.keys:
            self.x_save = []
            x = []
            y = []
            for i in x_base:
                tmp = 0
                
                for ii in range(len(self.data.a_list[key])):
                    # print(i/(4*math.pi))
                    tmp += self.data.a_list[key][ii] * math.exp(-self.data.b_list[key][ii] * (i/(4*math.pi))**2)
                tmp += self.data.c_list[key]
                
                y.append(tmp)
                
                if self.mode == "theta":
                    lambda_wl = float(self.lambda_set)

                    value = i * 90.0 * lambda_wl/math.pi
                    x.append(value)
                    self.x_save.append(value)
                else:
                    x.append(i)
                    self.x_save.append(i)
            
            
        
            ax.plot(x, y, label=self.labels(key,"long"))
            self.y_save.append(y)

        
        #determine title and labels
        ax.set_ylabel("f(q)")
        ax.set_title("Atomic Form Factors")
        if self.mode == "q":
            ax.set_xlabel("q [1/Å]")
        elif self.mode == "theta":
            ax.set_xlabel("2θ [°]")
            ax.set_xlim([0,180])
        
        ax.legend()
      
            
        # creating the Tkinter canvas 
        # containing the Matplotlib figure 
        canvas = FigureCanvasTkAgg(self.fig, master = self.root)   
        canvas.draw() 
      
        # placing the canvas on the Tkinter window 
        canvas.get_tk_widget().pack(side=tk.TOP) 
      
        # creating the Matplotlib toolbar 
        toolbar = NavigationToolbar2Tk(canvas, self.root) 
        toolbar.update() 
      
        # placing the toolbar on the Tkinter window 
        canvas.get_tk_widget().pack(side=tk.TOP) 
      
    

def window_size_limiter(avail_wxh,req_wxh,req_offset_xy):

    actual_wxh = [0,0]
    actual_offsets = [0,0]
    
    # check whether window fits on the current screen with and without offsets
    for i in range(len(avail_wxh)):
        if req_wxh[i] > avail_wxh[i]:
            actual_wxh[i] = avail_wxh[i]
            print("Caution, requested window doesn't fit the screen!")
            
        elif req_wxh[i] + req_offset_xy[i] > avail_wxh[i]:
            actual_wxh[i] = req_wxh[i]
            actual_offsets[i] = avail_wxh[i] - req_wxh[i]
            print("Caution, requested offset would move window off the screen!")
        
        else:
            actual_wxh[i] = req_wxh[i]
            actual_offsets[i] = req_offset_xy[i]
    
    return actual_wxh,actual_offsets

def create_window(dimensions="500x350+100+100", title = "Tkinter Hello World", icon = ""):
   
    w = int(dimensions.split("x")[0])
    h = dimensions.split("x")[1]
    h = int(h.split("+")[0])
    
    offset_x = int(dimensions.split("+")[1])
    offset_y = int(dimensions.split("+")[2])
    
    # initializes the Tk root window
    window = tk.Tk()
    
    # gets screen properties and centers in upper third
    screen_width = window.winfo_screenwidth()
    screen_height = window.winfo_screenheight()
    
    offset_x = int(screen_width/3 - w / 3)
    offset_y = int(screen_height/3 - h / 3)
    
    # makes sure the window stays within bounds
    actual_wxh, actual_offsets = window_size_limiter([screen_width,screen_height],[w,h], [offset_x,offset_y])
    
    # set a title
    window.title(title)
    
    # specify geometry and max and min measurements
    window.geometry(f"{actual_wxh[0]}x{actual_wxh[1]}+{actual_offsets[0]}+{actual_offsets[1]}")
    window.minsize(10,10)
    window.maxsize(screen_width,screen_height)
    if icon != "":
        window.iconbitmap(icon)
    

    return window


# make plot mock




    




# main program
if __name__ == "__main__":
    
    mpl.use("TkAgg")
    
    search = search_window()
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    