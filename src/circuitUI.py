import _tkinter
import tkinter as tk
from tkinter import filedialog as fd
import json
import numpy as np

jd = '{"Gate":{"X":{"n":"Pauli-X","c":"x","bg":"#e6b8af","prm":false},"Y":{"n":"Pauli-Y","c":"y","bg":"#f4cccc","prm":'\
     'false},"Z":{"n":"Pauli-Z","c":"z","bg":"#fce5cd","prm":false},"H":{"n":"Hadamard","c":"h","bg":"#fff2cc","prm":'\
     'false},"T":{"n":"pi/8 phase","c":"t","bg":"#c9daf8","prm":false},"T+":{"n":"pi/8 phase adjoint","c":"tdg","bg":' \
     '"#cfe2f3","prm":false},"S":{"n":"Phase","c":"s","bg":"#d9ead3","prm":false},"S+":{"n":"Phase adjoint","c":"sdg",'\
     '"bg":"#d0e0e3","prm":false},"RX(θ)":{"n":"X-Rotate","c":"rx","bg":"#d9d2e9","prm":true},"RY(θ)":{"n":"Y-Rotate",'\
     '"c":"ry","bg":"#d9d2e9","prm":true},"RZ(θ)":{"n":"Z-Rotate","c":"rz","bg":"#d9d2e9","prm":true}},"1st":{"SWAP":' \
     '{"n":"Swap","c":"swap","bg":"#d9d2e9","prm":false},"CZ":{"n":"Controlled-phase","c":"cz","bg":"#ead1dc","prm":' \
     'false}},"Ctrl":{"CNOT":{"n":"Controlled-NOT","c":"cx","bg":"#f7e7e6","prm":false}},"Read":{"READ":{"n":"Measure"'\
     ',"c":"","bg":"","prm":false}}}'


class ScrollFrame(tk.Frame):  # allows both scrollbars, used as the main frame to hold all widgets
    def __init__(self, parent):
        self.outer = tk.Frame(parent)
        self.canvas = tk.Canvas(self.outer)
        self.scroll_y, self.scroll_x = tk.Scrollbar(self.outer, command=self.canvas.yview), \
            tk.Scrollbar(self.outer, orient="horizontal", command=self.canvas.xview)
        tk.Frame.__init__(self, self.canvas)
        self.contentWindow = self.canvas.create_window((0, 0), window=self, anchor="nw")
        self.scroll_y.pack(side="right", fill="y")
        self.scroll_x.pack(side="bottom", fill="x")
        self.canvas.config(yscrollcommand=self.scroll_y.set, xscrollcommand=self.scroll_x.set)

        def resizeCanvas():
            self.canvas.config(scrollregion=self.canvas.bbox("all"))
            self.canvas.itemconfig(self.contentWindow)
        self.bind("<Configure>", lambda x: resizeCanvas())
        self.canvas.pack(fill="both", expand=True, side="left")
        self.pack, self.place, self.grid = self.outer.pack, self.outer.place, self.outer.grid
        self.a = None


class Wire:  # Create class for all wires created
    def __init__(self, frame, row, type):
        self.label = tk.Label(frame, text="{1}  {0}".format(str(row), type))  # create label
        if type == "c":  # classic protocol
            self.wire, row = tk.Label(frame, text="_ " * 500000), row + frame.a.cur["q"]  # create wire, overwrite row
        if type == "q":  # quantum protocol
            self.wire = tk.Frame(frame, background="dark grey")  # create and place the wire itself
        self.label.place(x=5*frame.a.c, y=(20*row+31)*frame.a.c)
        self.wire.place(x=13*frame.a.c, y=4*(5*row+8)*frame.a.c, w=1000000, h=2*frame.a.c)


class Spot:  # Create class for creating spots
    def __init__(self, row, col, spot_type, a):
        self.k, self.t, self.col, self.row = "{}{}:{}".format(spot_type, row, col), spot_type, col, row  # save ind data
        if spot_type == 'c':
            row = row + a.cur['q']
        self.x, self.y = range(a.c*(17+16*col), a.c*(17+16*(col+1))), range(a.c*(27+20*row), a.c*(27+20*(row+1)))
        self.full, self.obj = False, None  # is the spot filled, and if so, what is attached?
        if spot_type == "":  # overwrite the x and y ranges
            self.x, self.y = range(4*a.c*(4*col+2), 4*a.c*(4*col+2)+1), range((4+14*row)*a.c, (4+14*row)*a.c+1)

    def empty(self):
        self.full, self.obj = False, None


class Obj:  # Create a class for creating items (gates, detectors, and connectors)
    def __init__(self, frame, key, gate_dict, type, spot, rels, rel_no, custom, custom_type):
        self.f, self.k, self.dict, self.t, self.s, self.r, self.r_no, self.cstm, self.ct = \
            frame, key, gate_dict, type, spot, rels, rel_no, custom, custom_type  # save input vals
        self.c, self.last_s, self.lnks, self.undragged = gate_dict["c"], spot, [], True  # save non-input key values
        if type in ["Rec", "Read"]:
            self.widget = tk.Label(frame, text=self.k, relief="ridge", borderwidth=5)  # build the label
        else:
            self.widget = tk.Label(frame, text=self.k, background=self.dict["bg"], relief="raised")  # build the label
        self.widget.place(x=spot.x[0], y=spot.y[0], h=12 * self.f.a.c, w=12 * self.f.a.c)  # standard
        if type in ["Target", "Rec", "Read"]:  # other placements
            self.widget.place(h=8*self.f.a.c)  # adjust placement for reader
            if type != "Read":  # either a target or receptor
                self.widget.place(x=spot.x[0]+2*self.f.a.c, y=spot.y[0]+2*self.f.a.c, w=8*self.f.a.c)
            if type == "Rec":  # receptor only
                self.widget.place(x=spot.x[0]+4*self.f.a.c)

        def drag_start(event):
            frame.a.g_to_c = True
            event.widget._drag_start_x, event.widget._drag_start_y, self.last_s = event.x, event.y, self.s  # drag data
            if self.undragged and len(self.r) == 0:
                Obj(self.f, self.k, self.dict, self.t, self.s, [], self.r_no, self.cstm, self.ct)
        self.widget.bind("<Button-1>", drag_start)  # clicking the mouse begins dragging

        def on_drag_motion(event):
            self.widget.place(x=event.widget.winfo_x()-event.widget._drag_start_x+event.x,
                              y=event.widget.winfo_y()-event.widget._drag_start_y+event.y)  # use co-ord fix
        self.widget.bind("<B1-Motion>", on_drag_motion)  # dragging enables drag motion
        self.widget.bind("<ButtonRelease-1>", self.drag_end)  # releasing the mouse (even after one click)
        self.widget.bind("<Double-Button-1>", lambda x: self.delete())  # double-clicking deletes the widget

    def drag_end(self, event):
        t = "q"
        if self.t == "Rec":
            t = "c"
        row = col = 0
        while row < self.f.a.cur[t] and col < self.f.a.cur["lyr"]:
            if not self.f.a.g_to_c:
                sel_y = 4 * (5 * event + 8) * self.f.a.c
            elif self.last_s.t != "" and self.t != "Rec" and row == self.last_s.row:
                row += 1
                continue  # skip over this row as it is invalid
            else:
                sel_y = self.widget.winfo_y()
            s, read = self.f.a.d['s']["{}{}:{}".format(t, row, col)], False  # assign spot, and currently not valid read
            if self.t == "Read":
                read = True
                for i in range(col, self.f.a.cur["lyr"]):  # see if the spot is a valid place for a reader
                    if self.f.a.d['s']["{}{}:{}".format(t, row, i)].full:
                        read = False
            if ((self.t in ['Rec', '2nd', 'Target'] and col == self.r[0].s.col) or read or self.t in
               ["Gate", "1st", "Ctrl"]) and sel_y in s.y and not s.full:
                if not self.undragged:
                    self.last_s.empty()
                self.widget.place(x=s.x[0], y=s.y[0])  # place in generic current spot
                s.full, s.obj, self.s = True, self, s  # mark the spot as filled, save obj and spot to each other
                if len(self.r) != 0 and self.r[-1].t in ["Target", "2nd", "Rec"]:  # anything with prior placements
                    for i in range(len(self.r)):
                        self.r[i].widget.destroy()  # destroy previous target
                        for n in range(len(self.r[i].lnks)):
                            self.r[i].lnks[n].destroy()  # destroy previous links
                        if self.t == "Read":  # only for readers with prior placements
                            if self.last_s is not None:
                                for n in range(self.last_s.col, self.f.a.cur["lyr"]):
                                    self.f.a.d['s']["{}{}:{}".format(t, self.last_s.row, n)].empty()
                                self.f.a.d['s'][self.r[i].s.k].empty()
                        if self.t in ["Ctrl", "1st"]:  # only for controls and doubles with prior placements
                            for n in range(s.row, self.r[i].s.row + 1):
                                self.f.a.d['s']["{}{}:{}".format(t, n, self.r[i].s.col)].empty()
                    self.r = []
                if self.t in ["Target", "2nd", "Rec"]:  # if it is the second, attach and place
                    if self.undragged:
                        self.lnks = [tk.Label(self.f, background="dark grey")]  # build the link
                    self.lnks[0].place(x=self.r[0].s.x[0]+6*self.f.a.c, y=self.r[0].s.y[0]+12*self.f.a.c, w=2,
                                       h=abs(self.r[0].s.y[0]-s.y[0])-10*self.f.a.c)
                    if self.t != "Rec":  # control and target changes
                        for i in range(self.r[-1].s.row + 1, s.row):  # keep between empty
                            self.f.a.d['s']["{}{}:{}".format(t, i, s.col)].full = True
                        if self.t == "Target":
                            self.widget.place(x=s.x[0] + 2 * self.f.a.c, y=s.y[0] + 2 * self.f.a.c)
                            if row < self.r[-1].s.row:
                                self.lnks[0].place(y=s.y[0] + 10 * self.f.a.c)
                        elif self.t == "2nd":
                            self.lnks[0].place(h=abs(self.r[-1].s.y[0]-s.y[0])-12*self.f.a.c)
                            if row < self.r[-1].s.row:
                                self.lnks[0].place(y=s.y[0] + 12 * self.f.a.c)
                            if self.r_no > 1:
                                nw = Obj(self.f, self.k, self.dict, "2nd", s, self.r+[self], self.r_no-1, self.cstm,
                                         self.ct)
                                for obj in self.r:
                                    obj.r += [nw]
                                self.r += [nw]
                    else:  # attach links and shift receptor properly
                        if self.undragged:
                            self.lnks += [tk.Label(self.f, bg="dark grey")]
                        for i in range(len(self.lnks)):
                            self.lnks[i].place(x=self.r[0].s.x[0]+10*self.f.a.c+5*i, y=self.r[0].s.y[0]+10*self.f.a.c,
                                               h=abs(s.y[0]-self.r[0].s.y[0])-8*self.f.a.c, w=2)
                            self.widget.place(x=self.last_s.x[0] + 4 * self.f.a.c, y=s.y[0] + 2 * self.f.a.c)
                self.undragged = False
                if self.t in ["Ctrl", "Read", "1st"]:
                    gate_t = "2nd"
                    if self.t == "Ctrl":
                        gate_t = "Target"
                    if self.t == "Read":
                        self.widget.place(y=s.y[0] + 2 * self.f.a.c)
                        for i in range(s.col, self.f.a.cur["lyr"]):
                            self.f.a.d['s']["{}{}:{}".format(t, s.row, i)].full = True
                        gate_t = "Rec"
                    self.r += [Obj(self.f, self.k, self.dict, gate_t, s, self.r+[self], self.r_no-1, self.cstm,
                                   self.ct)]
                if self.dict["prm"] and self.f.a.g_to_c and self.c == self.dict["c"]:
                    ent = tk.Entry(self.f, textvariable=tk.StringVar(self.f, value="θ"), bg=self.dict["bg"])
                    ent.place(x=s.x[0] + self.f.a.c, y=s.y[0] + 4 * self.f.a.c, w=10 * self.f.a.c)

                    def get_param(entry):
                        ent_string = "("+entry.get()+")"
                        self.c, self.widget["text"] = self.dict["c"]+ent_string, self.k[0:self.k.index("(")]+ent_string
                        self.f.a.rewrite_code()
                        entry.destroy()
                    ent.bind('<Return>', lambda x: get_param(ent))
                    return  # cut short to avoid no theta being written into the code
                self.f.a.rewrite_code()  # rewrite the code
                return  # once it happens once, end the function's call
            else:
                col += 1
                if col == self.f.a.cur["lyr"]:
                    row += 1
                    col = 0
        self.widget.place(x=self.last_s.x[0], y=self.last_s.y[0])  # standard placement for the returnable
        if self.undragged and not (self.t in ["Target", "Rec", "2nd"]):
            self.widget.destroy()  # destroy if it's the first drag to avoid too many gates
        elif self.t in ["Target", "Rec", "Read"]:
            self.widget.place(y=self.last_s.y[0]+2*self.f.a.c)
            if self.t == "Target":  # target size
                self.widget.place(x=self.last_s.x[0]+2*self.f.a.c)
            if self.t == "Rec":
                self.widget.place(x=self.last_s.x[0]+4*self.f.a.c)

    def delete(self):
        for obj in ([self] + self.r):  # deleting one piece of a system deletes it all
            if obj.t in ["Target", "2nd", "Rec"]:
                for link in obj.lnks:
                    link.destroy()
                else:
                    rnge = range(self.s.row + 1, obj.s.row + 1)
                    if self.s.row > obj.s.row:
                        rnge = range(obj.s.row + 1, self.s.row + 1)
                    for i in rnge:
                        if i < self.f.a.cur["q"]:
                            self.f.a.d['s']["{}{}:{}".format("q", i, obj.s.col)].empty()
                        else:
                            self.f.a.d['s']["{}{}:{}".format("c", i-self.f.a.cur["q"], obj.s.col)].empty()
            elif obj.t == "Read":
                for i in range(obj.s.col, self.f.a.cur["lyr"]):
                    self.f.a.d['s']["{}{}:{}".format("q", obj.s.row, i)].empty()
            self.f.a.d['s'][obj.s.k].empty()
            obj.widget.destroy()
        self.f.a.rewrite_code()  # rewrite code to match board


class App(tk.Frame):
    def __init__(self, a, menu):
        self.c = round(a.winfo_screenheight() / 160)  # standard separations to configure the app
        self.d = {'s': {}, 'w': {}, 'i': json.loads(jd)}  # all dicts, for spots, wires, and items
        self.cur = {'q': 3, 'c': 2, 'lyr': len(self.d['i']['Gate'])+len(self.d['i']['1st'])+len(self.d['i']['Ctrl'])}
        self.init = {'q': self.cur['q'], 'c': self.cur['c'], 'lyr': self.cur['lyr']}  # initial counts
        tk.Frame.__init__(self, a)  # create app
        a.title("Wires and Gates Simulation")  # set the title
        a.geometry(str(a.winfo_screenwidth()) + "x" + str(round(a.winfo_screenheight()*0.9)))  # center the screen
        self.f_d = {"g": {}, "c": {}}  # build dictionary for the frames (g = grid, c = code)
        for frame in ["g", "c"]:  # build the frame dictionaries
            self.f_d[frame]["f"] = ScrollFrame(a)  # f = frame
            self.f_d[frame]["f"].a = self
            self.f_d[frame]["f"].place(relheight=1.0, relwidth=0.8)
            self.f_d[frame]["b"] = tk.Frame(self.f_d[frame]["f"])  # b = box
        self.f_d["c"]["f"].place(x=round(0.8 * a.winfo_screenwidth()))
        self.f_d["c"]["b"].grid(ipady=round(0.5 * a.winfo_screenheight()), ipadx=round(0.1 * a.winfo_screenwidth()))
        self.code, self.bnk, self.g_to_c = tk.Text(self.f_d["c"]["f"], background="dark grey"), \
            tk.LabelFrame(self.f_d["g"]["f"], text="Item Bank"), True
        self.code.bind("<Key>", self.code_to_grid)
        self.code.place(x=0, y=0, relwidth=1.0, relheight=1.0)
        self.bnk.place(x=5 * self.c, h=28 * self.c, w=4 * self.c * (4 * self.cur['lyr'] + 1))
        for i in range(max(self.cur['q'], self.cur['c'])):  # all wires
            for n in range(self.cur['lyr']):  # all layers
                for tp in ['q', 'c']:  # both types
                    if i < self.cur[tp]:  # create spots and wires
                        if n == 0:
                            self.d['w'][tp + str(i)] = Wire(self.f_d["g"]["f"], i, tp)
                        self.d['s']["{}{}:{}".format(tp, i, n)] = Spot(i, n, tp, self)
        file_menu, edit_menu = tk.Menu(menu), tk.Menu(menu)  # create menus
        menu.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label='Save to File', command=self.save_code)
        file_menu.add_command(label='Exit', command=a.destroy)
        menu.add_cascade(label="Edit", menu=edit_menu)
        custom_submenu, add_submenu, del_submenu = tk.Menu(edit_menu), tk.Menu(edit_menu), tk.Menu(edit_menu)  # submenu
        edit_menu.add_command(label="Copy Code", command=self.copy_code)
        edit_menu.add_cascade(label="Custom Gate", menu=custom_submenu)
        edit_menu.add_cascade(label="Adding", menu=add_submenu)
        edit_menu.add_cascade(label="Deleting", menu=del_submenu)
        custom_submenu.add_command(label="Custom Matrix Gate", command=self.custom_mtrx)
        custom_submenu.add_command(label="Grouped Gate", command=self.grouped)
        add_submenu.add_command(label="Add Qubit", command=lambda: self.add_element("q"))
        add_submenu.add_command(label="Add Classic Bit", command=lambda: self.add_element("c"))
        del_submenu.add_command(label="Delete Qubit", command=lambda: self.delete_element("q"))
        del_submenu.add_command(label="Delete Classic Bit", command=lambda: self.delete_element("c"))
        self.i_b = {}
        x = y = rn = 0
        for dct in self.d['i']:
            if dct != 'Gate':
                rn = 1
                if dct == 'Read':
                    x, y = 0, 1
            for k in self.d['i'][dct]:
                self.i_b[k] = Obj(self.f_d["g"]["f"], k, self.d['i'][dct][k], dct, Spot(y, x, "", self), [], rn, False,
                                  None)
                x += 1
        self.rewrite_code()

    def rewrite_code(self):  # simplify the code writing for the semicolons and commas
        c = 'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{}];\ncreg c[{}];\n\n'.format(str(self.cur['q']),
                                                                                        str(self.cur['c']))
        if self.g_to_c:
            final_layer = 0
            for g in self.i_b:
                if self.i_b[g].cstm:
                    c += self.i_b[g].dict["def"]
            col = row = 0
            while col < self.cur['lyr'] and row < self.cur["q"]:
                obj = self.d['s']["{}{}:{}".format("q", row, col)].obj
                if obj is not None and obj.s.full:  # only add if filled
                    final_layer = col
                    if obj.t == "Read" and obj.r[0].s.t == "c":
                        c += "\nmeasure q[{}] -> c[{}];".format(str(row), obj.r[0].s.row)
                    if obj.t == "Gate" or (obj.t in ["1st", "Ctrl"] and obj.s != obj.r[-1].s):
                        start_text = "\n{} "
                        if obj.cstm and obj.ct == "mtrx":
                            start_text = "\n// pragma custom_gate_action {} "
                        c += start_text.format(obj.c)
                        for item in ([obj] + obj.r):
                            location_text = "q[{}]; "
                            if len(obj.r) != 0 and item != obj.r[-1]:
                                location_text = "q[{}], "
                            c += location_text.format(str(item.s.row))
                col += 1
                if col == self.cur["lyr"]:
                    row += 1
                    col = 0
            self.code.delete(1.0, tk.END)
            self.code.insert(1.0, c)
            if final_layer >= self.cur['lyr'] - 1:
                App.add_element(self, 'lyr')
            elif final_layer + self.init["lyr"] < self.cur['lyr']:
                for i in range(final_layer+1, self.cur['lyr']):
                    App.delete_element(self, 'lyr')
            self.f_d["g"]["b"].grid(ipady=12*self.c*(self.cur["q"]+self.cur["c"]), ipadx=8*self.c*(self.cur['lyr']+1))

    def find(self, start):
        if self.code.get(self.code.search("[", start) + "+1c", self.code.search("]", start)) is not None:
            return int(self.code.get(self.code.search("[", start) + "+1c", self.code.search("]", start)))

    def code_to_grid(self, event):  # when enter is clicked, modify the visual simulation to match
        cd = self.code
        if event.widget.search("INVALID FORMATTING\n", 1.0) == "1.0":
            event.widget.delete('1.0', '1.0+' + str(len("INVALID FORMATTING\n")) + "c")
        self.g_to_c = False
        try:
            for wire_type in ["q", "c"]:  # correct wire counts
                count_find = str(cd.search(wire_type + "reg", '1.0'))
                if self.cur[wire_type] > self.find(count_find) >= self.init[wire_type]:
                    for i in range(self.find(count_find), self.cur[wire_type] + 1):
                        self.delete_element(wire_type)
                elif self.cur[wire_type] < self.find(count_find):
                    for i in range(self.cur[wire_type] + 1, self.find(count_find) + 1):
                        self.add_element(wire_type)
            for k in self.d['s']:  # delete all current widgets
                if self.d['s'][k].obj is not None:
                    self.d['s'][k].obj.delete()
            mdp = int(cd.search("\n\n", tk.END, backwards=True)[0:cd.search("\n\n", tk.END, backwards=True).index(".")])
            for i in range(6, cd.get("1.0", tk.END).count("\n")+1):
                line = str(i) + ".0"
                if i < mdp:
                    if cd.search("// pragma custom_gate_matrix", line, str(i+1)+".0") != "":  # overwrite custom mtrces
                        for k in self.i_b:
                            if self.i_b[k].cstm and self.i_b[k].ct == "mtrx" and cd.search(self.i_b[k].c, line) != "":
                                mtrx = []
                                for n in range(len(self.i_b[k].dict["mtrx"])):
                                    v = str(i+n+1)+".0"
                                    lst = []
                                    for m in range(len(self.i_b[k].dict["mtrx"])):
                                        if m == 0:
                                            ent = cd.get(cd.search("[", v), cd.search("j", v)+"+1c").strip("[")
                                        elif m == len(self.i_b[k].dict["mtrx"]) - 1:
                                            ent = cd.get(cd.search(" ", v)+"+1c", cd.search("]", v)).strip("]")
                                        else:
                                            ent = cd.get(cd.search(" ", v)+"+1c", cd.search("j", v)+"+1c")
                                        lst += [complex(ent)]
                                        v = cd.search("j", v)
                                    mtrx += [lst]
                                self.i_b[k].dict["mtrx"] = np.array(mtrx)
                                self.i_b[k].dict["def"] = "\n// pragma custom_gate_matrix {}\n// {}\n\n".\
                                    format(k, str(np.array(mtrx)).replace('\n', '\n// '))
                    elif cd.search("gate", line, str(i+1)+".0") != "":
                        for k in self.i_b:
                            if self.i_b[k].cstm and self.i_b[k].ct == "group" and cd.search(self.i_b[k].c, line) != "":
                                self.i_b[k].dict["def"] = cd.get(line, cd.search("}", line)+"+1c") + "\n"
                else:
                    opn = cd.search("(", line)
                    if cd.search(";", str(i)+".0", str(i+1)+".0") != "":
                        g = None
                        if cd.search("measure", line, str(i + 1) + ".0") != "":
                            g = self.i_b["READ"]
                        elif cd.search("//", line) != "":
                            if cd.search("custom_gate_action", line) != "":
                                g = self.i_b[cd.get(cd.search("custom_gate_action", line)+"+19c",
                                                    cd.search("q", line)+"-1c")]
                        else:
                            for k in self.i_b:
                                it = self.i_b[k]
                                if (it.t == "Gate" or (it.t in ["Ctrl", "1st"] and
                                                       ("," == cd.get(cd.search("]", line)+"+1c")))) and \
                                   (it.dict["c"] == (cd.get(line, cd.search(" ", line))) or
                                    (it.dict["prm"] and opn != "" and it.dict["c"] == (cd.get(line, opn)))) and \
                                        (len(cd.get(cd.search("[", line)+"+1c", cd.search("]", line))) != 0):
                                    g = it
                                    break
                        if g is not None:
                            new = Obj(g.f, g.k, g.dict, g.t, g.s, [], g.r_no, g.cstm, g.ct)
                            new.undragged = False
                            new.drag_end(self.find(line))
                            if g.dict["prm"]:
                                new.c = g.dict["c"]+cd.get(opn, cd.search(")", line) + "+1c")
                                new.widget["text"] = g.k[0:g.k.index("(")] + \
                                    cd.get(opn, cd.search(")", line)+"+1c")
                            if len(new.r) != 0:
                                new.r[0].last_s = new.s
                                if g == self.i_b["READ"]:
                                    new.r[0].drag_end(self.find(str(cd.search("c", line))) + self.cur["q"])
                                else:
                                    new.r[0].drag_end(self.find(cd.search("]", line) + "+1c"))
        except ValueError or _tkinter.TclError:
            if event.widget.search("INVALID FORMATTING\n", 1.0) == "1.0":
                event.widget.delete('1.0', '1.0+' + str(len("INVALID FORMATTING\n")) + "c")
            event.widget.insert(1.0, "INVALID FORMATTING\n")
            event.widget.tag_config("start", foreground="dark red")
            event.widget.tag_add("start", "1.0", '1.0+' + str(len("INVALID FORMATTING\n")) + "c")
        self.f_d["g"]["b"].grid(ipady=12*self.c*(self.cur['q']+self.cur['c']), ipadx=8*self.c*(self.cur['lyr']+1))
        self.g_to_c = True

    def copy_code(self):  # copy the sidebar text to clipboard
        self.clipboard_clear()
        self.clipboard_append(self.code.get("1.0", tk.END))

    def save_code(self):
        with open(fd.asksaveasfilename(filetypes=(("QASM files", "*.qasm"), ("All files", "*.*"))), 'w') as f:
            f.write(self.code.get("1.0", tk.END))

    def grouped(self):
        fr = tk.Toplevel(self)
        fr.title("Custom Gate Creation")
        fr.geometry(str(self.c*50)+"x"+str(self.c*55))
        gs, t = tk.Listbox(fr, selectmode="multiple"), tk.Text(fr)
        gs.place(x=self.c, y=self.c, h=self.c*40, w=self.c*20)
        t.place(x=25*self.c, y=self.c, w=24*self.c, h=self.c*43)
        i = 0
        for item in self.i_b:
            gs.insert(i, item)
            i += 1

        def lst(frame, txt, opts, q_no):
            selected, cname = [], opts.curselection()
            for val in cname:
                selected.append(opts.get(val))
            txt.delete("1.0", tk.END)
            txt.insert("1.0", "Use these variables as qubits:\n"+str(['q', 'r', 's', 't', 'u', 'v'][0:q_no])+"\n")
            for val in selected:
                if val in self.i_b:
                    if self.i_b[val].t == "Gate":
                        txt.insert(tk.END, val+" ()\n")
                    elif self.i_b[val].cstm:
                        txt.insert(tk.END, val+" ()"+" ()"*self.i_b[val].dict["N"]+"\n")
                    else:
                        txt.insert(tk.END, val+" () ()\n")

            def create(nm):
                dta = "gate "+nm+" "+str(['q', 'r', 's', 't', 'u', 'v'][0:q_no])[1:][:-1].replace("'", "")+" {\n"
                try:
                    for vl in range(3, int(txt.index('end-1c').split('.')[0])):
                        for k in self.i_b:
                            if k == (txt.get(str(vl)+".0", txt.search(" ", str(vl)+".0"))):
                                dta += "  " + self.i_b[k].c
                                ln = 2
                                if self.i_b[k].t == "Gate":
                                    ln = 1
                                n = str(vl)+".0"
                                for num in range(ln):
                                    dta += " "+txt.get(txt.search("(", n)+"+1c", txt.search(")", n))
                                    if num+1 == ln:
                                        dta += ";\n"
                                    else:
                                        dta += ","
                                        n = txt.search(")", n)+"+1c"
                                break
                    dta += "}\n"
                    self.init["lyr"] += 1
                    self.add_element('lyr')
                    self.bnk.place(w=4*self.c*(4*self.init["lyr"]+1))
                    gate_type = "Gate"
                    if q_no != 1:
                        gate_type = "1st"
                    self.i_b[nm] = Obj(self.f_d["g"]["f"], nm, {"n": nm, "c": nm, "bg": None, "prm": False, "def": dta},
                                       gate_type, Spot(0, self.init["lyr"]-1, "", self), [], q_no-1, True, "group")
                    frame.destroy()
                    self.rewrite_code()
                except ValueError:
                    if txt.search("Improper formatting") == "":
                        txt.insert(1.0, "Improper formatting, try again\n")
            name = tk.Entry(frame, textvariable=tk.StringVar(value="Custom"))
            name.place(x=self.c * 22, y=self.c * 42, w=self.c * 28, h=self.c * 4)
            tk.Button(frame, text="Create Gate", command=lambda: create(name.get())).place(x=self.c*30, y=self.c*48)
        tk.Label(fr, text="Qubit Number").place(x=0, y=self.c*42)
        qn = tk.Entry(fr)
        qn.place(x=self.c*16, y=self.c*42, w=self.c*5, h=self.c*4)
        tk.Button(fr, text="Make Template", command=lambda: lst(fr, t, gs, int(qn.get()))).place(x=self.c, y=self.c*48)

    def custom_mtrx(self):
        fr = tk.Toplevel(self)
        fr.title("Custom Gate Creation")
        fr.geometry(str(self.c*45)+"x"+str(self.c*50))
        tk.Label(fr, text="     n    =").place(x=self.c, y=self.c * 2)
        ets, vs = {"n": tk.Entry(fr), "nm": tk.Entry(fr), "mtrx": None}, {"n": None, "nm": None, "mtrx": None}
        ets["n"].place(y=self.c*2, x=self.c*11, w=self.c*4)
        ets["nm"].place(y=self.c*8, x=self.c*15, w=self.c*25)
        tk.Label(fr, text="Gate Name: ").place(x=0, y=self.c*8)

        def new_n(f, e, v):
            v["n"] = int(e["n"].get())
            if e["mtrx"] is not None:
                for i in range(len(e["mtrx"])):
                    for n in range(len(e["mtrx"][i])):
                        e["mtrx"][i][n].destroy()
            e["mtrx"] = []
            if v["n"] <= self.cur['q']:
                for a in range(2 ** v["n"]):
                    new_list = []
                    for b in range(2 ** v["n"]):
                        new_list += [tk.Entry(f)]
                        new_list[-1].place(x=self.c*(3+8*b), y=self.c*(18+8*a), w=self.c*8, h=self.c*8)
                    ets["mtrx"] += [new_list]
        tk.Button(fr, text="Submit n", command=lambda: new_n(fr, ets, vs)).place(x=self.c * 17, y=self.c * 2)

        def new_mtrx(f, e, v):
            def newgate(warn):
                if warn is not None:
                    warn.destroy()
                self.init["lyr"] += 1
                self.add_element("lyr")
                self.bnk.place(w=4*self.c*(4*self.init["lyr"]+1))
                vs["nm"], t = e["nm"].get(), "Gate"  # save name and default gate type
                if v["n"] != 1:
                    t = "1st"
                df = "\n// pragma custom_gate_matrix {}\n// {}\n\n".format(
                    v["nm"], str(np.array(v["mtrx"])).replace('\n', '\n// '))
                self.i_b[v["nm"]] = \
                    Obj(self.f_d['g']['f'], v["nm"], {"n": v["nm"], "bg": None, "c": v["nm"], "mtrx":
                        np.array(v["mtrx"]), "N": v["n"], "prm": False, "def": df}, t,
                        Spot(0, self.init["lyr"]-1, "", self), [], v["n"]-1, True, "mtrx")
                self.rewrite_code()
                f.destroy()
            try:
                v["mtrx"] = []
                for a in range(len(e["mtrx"])):
                    new_list = []
                    for b in range(len(e["mtrx"][a])):
                        new_list += [complex(e["mtrx"][a][b].get().replace(" ", ""))]
                    v["mtrx"] += [new_list]
                if np.linalg.norm(np.array(v["mtrx"]).transpose().conjugate()-np.identity(2 ** v["n"])) < 1*10**(-14):
                    newgate(None)
                else:
                    w = tk.Toplevel(self)
                    w.title("WARNING!")
                    w.geometry(str(self.c * 40) + "x" + str(self.c * 15))
                    tk.Label(w, text="NON-UNITARY matrix submitted.\n Click OK to create").place(x=self.c, y=self.c)
                    tk.Button(w, text="OK", command=lambda: newgate(w)).place(x=self.c*19, y=self.c*10)
            except ValueError:
                tk.Label(f, text="Input must be in format '{Real}+{Im}j'").place(x=self.c * 4, y=self.c * 14)
        tk.Button(fr, text="Create", command=lambda: new_mtrx(fr, ets, vs)).place(x=self.c * 30, y=self.c * 2)

    def add_element(self, t):
        self.cur[t] += 1
        rnge = self.cur['q'] + self.cur["c"]
        if t in ["q", "c"]:
            rnge = self.cur['lyr']
        for i in range(rnge):
            if t in ["q", "c"]:
                if t == "q":
                    self.d['s']["{}{}:{}".format(t, self.cur[t] - 1, i)] = Spot(self.cur[t]-1, i, t, self)
                    for n in range(self.cur["c"]):
                        if i == 0:
                            self.d['w']["c" + str(n)].wire.place(y=4 * self.c * (5 * (n + self.cur[t]) + 8))
                            self.d['w']["c" + str(n)].label.place(y=4 * self.c * (5 * (n + self.cur[t]) + 8))
                        s = self.d['s']["{}{}:{}".format("c", n, i)]
                        s.y = range(self.c*(27+20*(n + self.cur[t])), self.c*(27+20*(n + self.cur[t] + 1)))
                        if s.full:
                            for v in range(len(s.obj.lnks)):
                                s.obj.lnks[v].place(y=s.obj.r[0].s.y[0]+10*self.c, h=s.y[0]-s.obj.r[0].s.y[0]-8*self.c)
                            s.obj.widget.place(y=s.y[0] + self.c * 2)
                else:
                    self.d['s']["{}{}:{}".format(t, self.cur[t] - 1, i)] = Spot(self.cur['q']+self.cur[t]-1, i, t, self)
                if i == 0:
                    self.d['w'][t+str(self.cur[t]-1)] = Wire(self.f_d["g"]["f"], self.cur[t]-1, t)
            else:
                w = "q"
                if i >= self.cur["q"]:
                    i -= self.cur["q"]
                    w = "c"
                self.d['s']["{}{}:{}".format(w, i, self.cur[t]-1)] = Spot(i, self.cur[t]-1, w, self)
                if self.d['s']["{}{}:{}".format(w, i, self.cur[t]-2)].obj is not None and \
                        self.d['s']["{}{}:{}".format(w, i, self.cur[t]-2)].obj.t == "Read":
                    self.d['s']["{}{}:{}".format(w, i, self.cur[t]-1)].full = True
        self.rewrite_code()

    def delete_element(self, t):
        if self.cur[t] > self.init[t]:
            rnge = max(self.cur['q'], self.cur["c"])
            if t in ["q", "c"]:
                rnge = self.cur['lyr']
            for i in range(rnge):  # only delete if empty
                for p in ['q', 'c']:
                    if (len(t) > 1 and i < self.cur[p] and self.d['s']['{}{}:{}'.format(p, i, self.cur[t]-1)].obj
                       is not None) or (len(t) < 3 and self.d['s']["{}{}:{}".format(t, self.cur[t]-1, i)].full):
                        return
            self.cur[t] -= 1
            for i in range(rnge):
                if t in ["q", "c"]:
                    if t == "q":
                        for n in range(self.cur["c"]):
                            self.d['w']["c" + str(n)].wire.place(y=4 * self.c * (5 * (n + self.cur['q']) + 8))
                            self.d['w']["c" + str(n)].label.place(y=self.c * (20 * (n + self.cur['q']) + 31))
                            s = self.d['s']["{}{}:{}".format("c", n, i)]
                            s.y = range(self.c*(27+20*(n + self.cur[t])), self.c*(27+20*(n + self.cur[t] + 1)))
                            if s.obj is not None:
                                for v in range(len(s.obj.lnks)):
                                    s.obj.lnks[v].place(y=s.obj.r[0].s.y[0]+10*self.c,
                                                        h=s.y[0]-s.obj.r[0].s.y[0]-8*self.c)
                                s.obj.widget.place(y=s.y[0] + self.c * 2)
                    if i == 0:
                        self.d['w'][t+str(self.cur[t])].wire.destroy()
                        self.d['w'][t+str(self.cur[t])].label.destroy()
                        self.d['w'].pop(t+str(self.cur[t]))
                    self.d['s'].pop("{}{}:{}".format(t, self.cur[t], i))
                else:
                    if i < self.cur['q']:
                        self.d['s'].pop("{}{}:{}".format(t, i, self.cur[t]))
                    else:
                        self.d['s'].pop("{}{}:{}".format(t, i-self.cur['q'], self.cur[t]))
        self.rewrite_code()


if __name__ == "__main__":
    root = tk.Tk()
    main_menu = tk.Menu(root)
    root.config(menu=main_menu)
    App(root, main_menu).pack(side="top", fill="both", expand=True)
    root.mainloop()