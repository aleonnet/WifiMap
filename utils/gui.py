# %%
import os
import sys
from glob import glob
from pathlib import Path
from tqdm import tqdm
import threading
from threading import Timer
from enum import Enum
from time import sleep
from datetime import datetime
import tkinter as tk
import tkinter.ttk as ttk
import tkinter.font as tkfont
import tkinter.scrolledtext as st


from .scan import *
from .roomtrain import RoomTrain
from .trajtrain import TrajTrain

# %%


def get_script_path():
    return os.path.dirname(os.path.realpath(sys.argv[0]))


dir_path = get_script_path()
# print(dir_path)

# %%


class Main:
    def __init__(self, master):
        self.master = master
        self.master.title('Wifi Floor Plan')
        self.master.geometry("600x600")
        center(self.master)

        def_font = tkfont.nametofont("TkDefaultFont")
        def_font.config(size=15)

        subfolders = [i.split('/')[-2]
                      for i in glob(get_script_path() + "/*/")]
        subfolders.remove('utils')
        self.frame = tk.Frame(self.master)
        self.label = tk.Label(
            self.frame, text="Please SELECT or ENTER the username:")
        self.label.pack()
        self.combo = ttk.Combobox(
            self.frame, values=subfolders, font=('TkDefaultFont', '15'))
        self.combo.bind('<<ComboboxSelected>>', self.display_user)
        self.combo.bind('<Return>', self.display_user)
        self.combo.pack(pady=10)
        tk.Label(self.frame, text='Working Directory:').pack()
        self.text = tk.StringVar()
        self.selectLabel = tk.Label(
            self.frame, height=2, textvariable=self.text)
        self.selectLabel.pack()
        if subfolders:
            self.combo.current(0)
            self.display_user()

        self.butnew("Room Level Training", "Room Level Training", RoomTrainGUI)
        self.butnew("Trajectory Training", "Trajectory Training", TrajTrainGUI)
        self.butnew("Floor Plan Construction",
                    "Floor Plan Construction", FloorPlan)

        self.exitButton = tk.Button(self.frame, text='Exit', fg='red', width=25,
                                    command=self.master.destroy)
        self.exitButton.pack(side=tk.BOTTOM, pady=10)

        self.frame.pack(expand=True)

    def butnew(self, text, title, _class):
        tk.Button(self.frame, text=text, width=25, pady=10,
                  command=lambda: self.new_window(title, _class)).pack(pady=10)

    def new_window(self, title, _class):
        self.newWindow = tk.Toplevel(self.master)
        _class(self.newWindow, title)
        center(self.newWindow)

    def display_user(self, *args):
        user = self.combo.get()
        # print("Your selection is", user)
        global dir_path
        dir_path = get_script_path() + "/" + user
        self.text.set(dir_path)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            subfolders = [i.split('/')[-2]
                          for i in glob(get_script_path() + "/*/")]
            self.combo['values'] = subfolders

# %%


class RoomTrainGUI:
    def __init__(self, master, title):
        self.master = master
        self.master.title(title)
        self.master.geometry("600x600")
        self.frame = tk.Frame(self.master)
        self.file_path = dir_path + "/roomMap.txt"
        if not os.path.exists(self.file_path):
            with open(self.file_path, 'w') as f:
                f.write(
                    'Feel free to edit the room map here.\nClick the SAVE button for future reference.\n\n1 bedroom\n2 studyroom\n3 livingroom\n4 kitchen')
        tk.Label(self.frame, text="Room Map",
                 anchor="e", justify=tk.LEFT).grid(row=0, column=0)
        self.room_label = st.ScrolledText(
            self.frame, width=30, height=9, font=('TkDefaultFont', '15'))
        self.room_label.grid(row=1, column=0, padx=10, pady=10)
        self.edit_file()
        btn_save = tk.Button(self.frame, text="Save",
                             command=self.save_file)
        btn_save.grid(row=2, column=0)

        self.room_form = RoomForm(self.frame)
        self.room_form.grid(row=1, column=1, padx=10, pady=10)

        self.pbar_label = tk.Label(self.frame, text="", height=2)

        self.pbar_label.grid(row=3, column=0, columnspan=2, pady=10)
        self.scan_flag = False
        self.scan_btn = tk.Button(self.frame, text='Start Scan', width=25, pady=10,
                                  command=self.scan_click)
        self.scan_btn.grid(row=4, column=0, columnspan=2, pady=5)

        self.train_info = tk.StringVar()
        self.train_label = tk.Label(self.frame, textvariable=self.train_info)

        self.train_label.grid(row=5, column=0, columnspan=2, pady=10)
        self.train_btn = tk.Button(self.frame, text='Room-Level Train', width=25, pady=10,
                                   command=self.room_train)
        self.train_btn.grid(row=6, column=0, columnspan=2, pady=5)

        self.exitButton = tk.Button(self.frame, text='Exit', fg='red', width=25,
                                    command=self.exit_train)
        self.exitButton.grid(row=7, column=0, columnspan=2, pady=10)
        self.frame.pack(expand=True)

    def exit_train(self):
        if self.scan_flag:
            self.stop_scan()
        self.master.destroy()

    def room_train(self):
        self.train = RoomTrain(dir_path)
        x = threading.Thread(target=self.train1)
        x.start()

    def train1(self):
        s = self.train.combine()
        self.train_info.set(s)
        x = threading.Thread(target=self.train2)
        x.start()

    def train2(self):
        s = self.train.preprocess()
        self.train_info.set(s)
        x = threading.Thread(target=self.train3)
        x.start()

    def train3(self):
        s = self.train.train()
        self.train_info.set(s)

    def doWork(self):
        if self.scan_flag:
            try:
                self.f = open(self.file_name, 'w')
                self.f.write('room ' + str(self.room_id) +
                             ' ' + str(datetime.now()) + '\n')
                self.f.write(scan())
                self.f.write('\n\n')
                self.count += 1
                self.pbar.update(1)
                self.update_pbar()
                self.f.close()
            except (RuntimeError, TypeError, NameError) as err:
                print('End Wifi Scanning')

            if self.count == self.count_stop:
                self.stop_scan()

    def update_pbar(self):
        progress = str(self.pbar).split('|')
        if len(progress) == 1:
            self.pbar_label['text'] = str(self.pbar)
        elif len(progress) == 3:
            self.pbar_label['text'] = progress[0] + \
                ' ' + progress[1] + '\n' + progress[2]

    def stop_scan(self):
        self.scan_flag = False
        self.rt.stop()
        if self.f:
            self.f.close()
        self.pbar.close()
        self.scan_btn['text'] = 'Start Scan'

    def thread(self):
        self.count = 0
        totaltime = 60 * self.room_form.get_duration()
        self.count_stop = totaltime // self.interval  # Stop condition
        self.pbar = tqdm(total=self.count_stop,
                         bar_format='{l_bar}{bar:10}{r_bar}')
        self.update_pbar()
        self.rt = RepeatedTimer(self.interval, self.doWork)

    def scan_click(self):
        self.scan_flag = not self.scan_flag
        if self.scan_flag:
            self.room_id = self.room_form.get_room()
            self.interval = self.room_form.get_interval()
            folder = dir_path + '/data'
            Path(folder).mkdir(parents=True, exist_ok=True)
            self.file_name = folder + '/train_room_' + self.room_id + \
                '_' + datetime.now().strftime('%m_%d_%H:%M')+'.txt'

            x = threading.Thread(target=self.thread)
            x.start()
            self.scan_btn['text'] = 'Stop Scan'
        else:
            self.stop_scan()

    def edit_file(self):
        self.room_label.delete(1.0, tk.END)
        with open(self.file_path, "r") as input_file:
            text = input_file.read()
            self.room_label.insert(tk.END, text)

    def save_file(self):
        with open(self.file_path, "w") as output_file:
            text = self.room_label.get(1.0, tk.END)
            output_file.write(text)


class TrajTrainGUI:
    def __init__(self, master, title):
        self.master = master
        self.master.title(title)
        self.master.geometry('1000x800')
        self.line_start = None

        self.paths = []

        self.canvas = tk.Canvas(
            self.master, bg="white", width=600, height=800)
        self.canvas.bind("<Button-1>", self.draw)
        self.canvas.bind("<Motion>", self.mouse_motion)

        x1 = 0
        x2 = 600
        for k in range(0, 900, 50):
            y1 = k
            y2 = k
            self.canvas.create_line(
                x1, y1, x2, y2, fill='#eeeeee')

        y1 = 0
        y2 = 800
        for k in range(0, 700, 50):
            x1 = k
            x2 = k
            self.canvas.create_line(x1, y1, x2, y2, fill='#eeeeee')

        self.canvas.pack(side=tk.LEFT)

        self.canvas.tag_bind("draggable", "<ButtonPress-1>",
                             self.button_press)
        self.canvas.tag_bind("draggable", "<Button1-Motion>",
                             self.button_motion)

        self.v = tk.IntVar(self.master, 0)

        values = {"Draw": Mode.DRAW,
                  "Reverse": Mode.REVERSE,
                  "Delete": Mode.DELETE
                  }

        frame = tk.Frame(self.master)
        self.label = tk.Label(frame)
        self.label.pack(expand=True, fill=tk.BOTH)
        self.radios = []
        for (text, value) in values.items():
            rd = tk.Radiobutton(frame, text=text, variable=self.v, pady=10,
                                value=value.value, indicator=0,
                                command=self.changeMode)
            self.radios.append(rd)
            rd.pack(fill=tk.X, pady=10)
        self.draw_mode = self.v.get()

        self.pbar_label = tk.Label(frame, text="", height=2,
                                   anchor="e", justify=tk.LEFT)

        self.pbar_label.pack()

        self.monitor_mode = False
        self.monitor_btn = tk.Button(frame, text="Start Scan", pady=10, highlightbackground='black',
                                     command=self.monitor)
        self.monitor_btn.pack(expand=True, fill=tk.BOTH)

        self.path_label = st.ScrolledText(
            frame, width=30, height=10, pady=10, font=('TkDefaultFont', '15'))
        self.path_label.pack()

        self.train_info = tk.StringVar()
        self.train_label = tk.Label(frame, textvariable=self.train_info)
        self.train_label.pack(pady=10)
        self.train_btn = tk.Button(
            frame, text='Trajectory Train', pady=10, command=self.traj_train)
        self.train_btn.pack(pady=10)

        self.exitButton = tk.Button(
            frame, text='Exit', fg='red', command=self.exit_train)
        self.exitButton.pack(pady=10)

        frame.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        self.folder = dir_path + '/data'
        Path(self.folder).mkdir(parents=True, exist_ok=True)
        self.f, self.path_f = None, None
        self.path_name = self.folder + '/train_traj_' + \
            datetime.now().strftime('%m_%d_%H:%M')+'.txt'

    def exit_train(self):
        if self.f:
            self.f.close()
        if self.path_f:
            self.path_f.close()
        self.master.destroy()

    def traj_train(self):
        self.train = TrajTrain(dir_path)
        x = threading.Thread(target=self.train1)
        x.start()

    def train1(self):
        s = self.train.combine()
        self.train_info.set(s)
        x = threading.Thread(target=self.train2)
        x.start()

    def train2(self):
        s = self.train.preprocess()
        self.train_info.set(s)
        x = threading.Thread(target=self.train3)
        x.start()

    def train3(self):
        s = self.train.train()
        self.train_info.set(s)

    def clear_radio(self):
        self.monitor_btn.configure(highlightbackground='red')
        self.draw_mode = Mode.MOVE.value
        for rd in self.radios:
            rd.deselect()

    def update_path(self):
        path_info = '\n'.join([str(i[0]) + '\n' + str(i[1])
                               for i in self.paths])

        self.path_label.configure(state='normal')
        self.path_label.delete('1.0', tk.END)
        self.path_label.insert(tk.INSERT, path_info)
        self.path_label.configure(state='disabled')
        self.path_f = open(self.path_name, 'w')
        self.path_f.write(path_info + '\n')
        self.path_f.close()

    def update_pbar(self):
        progress = str(self.pbar).split('|')
        if len(progress) == 1:
            self.pbar_label['text'] = str(self.pbar)
        elif len(progress) == 3:
            self.pbar_label['text'] = progress[0] + \
                ' ' + progress[1] + '\n' + progress[2]

    def doWork(self):
        self.pbar = tqdm(total=0,
                         bar_format='{l_bar}{bar:10}{r_bar}')
        self.update_pbar()
        while self.monitor_mode:
            try:
                self.f = open(self.file_name, 'w')
                self.f.write('room unkown ' + str(datetime.now()) + '\n')
                self.f.write(scan())
                self.f.write('\n\n')
                self.pbar.update(1)
                self.update_pbar()
                self.f.close()
            except (RuntimeError, TypeError, NameError) as err:
                print('End Wifi Scanning')

    def changeMode(self):
        self.draw_mode = self.v.get()

    def mouse_motion(self, event):
        x, y = event.x, event.y
        text = "Mouse position: ({}, {})".format(x, y)
        self.label.config(text=text)

    def monitor(self):
        self.monitor_mode = not self.monitor_mode
        if self.monitor_mode and self.paths:
            if self.f:
                self.f.close()
            self.file_name = self.folder + '/' + str(self.paths[-1]) + '.txt'
            self.monitor_btn['text'] = 'Stop Scan'
            self.monitor_btn.configure(highlightbackground='black')
            x = threading.Thread(target=self.doWork)
            x.start()
        else:
            self.monitor_btn['text'] = 'Start Scan'

    def compare(self, c1, c2):
        return sum([abs(c1[i]-c2[i]) for i in range(len(c1))]) < 1

    def button_press(self, event):
        item = self.canvas.find_withtag(tk.CURRENT)
        self.dnd_item = (item, event.x, event.y)

        if self.draw_mode == Mode.REVERSE.value:
            items = self.canvas.find_withtag("draggable")
            for i in items:
                self.canvas.itemconfig(i, fill=self.color)
            c = self.canvas.coords(item)
            self.paths.append([str(datetime.now()), (c[2], c[3], c[0], c[1])])
            self.canvas.create_line(c[2], c[3], c[0], c[1], arrow=self.arrow, arrowshape=(16, 20, 6),
                                    fill='blue', width=self.width, tags="draggable")
            self.clear_radio()
        elif self.draw_mode == Mode.DELETE.value:
            delete_c = self.canvas.coords(item)
            pre_t = 0
            for i in range(len(self.paths)):
                t, c = self.paths[i]
                if self.compare(c, delete_c):
                    del self.paths[i]
                    break
            self.canvas.delete(item)

            items = self.canvas.find_withtag("draggable")
            for i in items:
                self.canvas.itemconfig(i, fill=self.color)
            if len(items) > 0:
                item = items[-1]
                self.canvas.itemconfig(item, fill='blue')
            self.clear_radio()

        self.update_path()

    def button_motion(self, event):
        if self.draw_mode == Mode.MOVE.value:
            x, y = event.x, event.y
            item, x0, y0 = self.dnd_item
            pre_c = self.canvas.coords(item)
            self.canvas.move(item, x - x0, y - y0)
            self.dnd_item = (item, x, y)
            for i in range(len(self.paths)):
                t, c = self.paths[i]
                if self.compare(c, pre_c):
                    del self.paths[i]
                    self.paths.append([t, self.canvas.coords(item)])
                    break
            self.canvas.tag_raise(item, 'all')
            items = self.canvas.find_withtag("draggable")
            for i in items:
                self.canvas.itemconfig(i, fill=self.color)
            if len(items) > 0:
                item = items[-1]
                self.canvas.itemconfig(item, fill='blue')
        self.update_path()

    def draw(self, event):
        if self.draw_mode == Mode.DRAW.value:
            items = self.canvas.find_withtag("draggable")
            for i in items:
                self.canvas.itemconfig(i, fill=self.color)
            x, y = event.x, event.y
            if not self.line_start:
                self.line_start = (x, y)
            else:
                x_origin, y_origin = self.line_start
                self.line_start = None
                line = (x_origin, y_origin, x, y)
                self.paths.append([str(datetime.now()), line])
                self.arrow = tk.LAST
                self.color = 'black'
                self.width = 4
                self.canvas.create_line(*line, arrow=self.arrow, arrowshape=(16, 20, 6),
                                        fill='blue', width=self.width, tags="draggable")
                self.clear_radio()
                self.update_path()


class FloorPlan:
    def __init__(self, master, title):
        self.master = master
        self.master.title(title)
        self.master.geometry('1000x800')

        self.frame = tk.Frame(self.master)

        self.exitButton = tk.Button(self.frame, text='Exit', fg='red', width=25,
                                    command=self.master.destroy)
        self.exitButton.pack(pady=10)

        self.frame.pack(expand=True)

# %%


class RoomForm(tk.LabelFrame):
    def __init__(self, master):
        super().__init__(master, text="Room-level Training Options")

        room_label = tk.Label(self, text="Room ID")
        self.room = tk.Spinbox(self, values=(1, 2, 3, 4), width=5)

        interval_label = tk.Label(self, text="Scan Interval (s)")
        self.interval = tk.Spinbox(self, values=(5, 6, 7, 8), width=5)

        duration_label = tk.Label(self, text="Scan Duration (m)")
        self.duration = tk.Spinbox(self, values=(
            'infinite', 0.2, 1, 5, 10, 15, 30), width=5)
        room_label.grid(sticky=tk.W, row=0, column=0)
        self.room.grid(row=0, column=1, pady=10)
        interval_label.grid(sticky=tk.W, row=1, column=0)
        self.interval.grid(row=1, column=1, pady=10)
        duration_label.grid(sticky=tk.W, row=2, column=0)
        self.duration.grid(row=2, column=1, pady=10)

    def get_room(self):
        return self.room.get()

    def get_interval(self):
        return int(self.interval.get())

    def get_duration(self):
        if self.duration.get() == 'infinite':
            return 0
        return float(self.duration.get())


class Mode(Enum):
    DRAW = 1
    SELECT = 2
    REVERSE = 3
    MOVE = 4
    DELETE = 5


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def center(win):
    """
    centers a tkinter window
    :param win: the main window or Toplevel window to center
    """
    win.update_idletasks()
    width = win.winfo_width()
    frm_width = win.winfo_rootx() - win.winfo_x()
    win_width = width + 2 * frm_width
    height = win.winfo_height()
    titlebar_height = win.winfo_rooty() - win.winfo_y()
    win_height = height + titlebar_height + frm_width
    x = win.winfo_screenwidth() // 2 - win_width // 2
    y = win.winfo_screenheight() // 2 - win_height // 2
    win.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    win.deiconify()
