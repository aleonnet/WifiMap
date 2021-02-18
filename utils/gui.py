# %%
import os
import sys
from glob import glob
from pathlib import Path
from tkinter.constants import HORIZONTAL, VERTICAL
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
from pickle import load, dump
from PIL import Image, ImageDraw, ImageTk
import numpy as np
from matplotlib import cm, colors
from collections import defaultdict
import cv2 as cv
from numpy.lib.function_base import median
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

        self.exitButton = tk.Button(self.frame, bg='grey', fg='red', text='Exit', width=25,
                                    command=self.master.destroy)
        self.exitButton.pack(side=tk.BOTTOM, pady=10)

        self.frame.pack(expand=True)

    def butnew(self, text, title, _class):
        tk.Button(self.frame, bg='grey', fg='black', text=text, width=25, pady=10,
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
        btn_save = tk.Button(self.frame, bg='grey', fg='black', text="Save",
                             command=self.save_file)
        btn_save.grid(row=2, column=0)

        self.room_form = RoomForm(self.frame)
        self.room_form.grid(row=1, column=1, padx=10, pady=10)

        self.pbar_label = tk.Label(self.frame, text="", height=2)

        self.pbar_label.grid(row=3, column=0, columnspan=2, pady=10)
        self.scan_flag = False
        self.scan_btn = tk.Button(self.frame, bg='grey', fg='black', text='Start Scan', width=25, pady=10,
                                  command=self.scan_click)
        self.scan_btn.grid(row=4, column=0, columnspan=2, pady=5)

        self.train_info = tk.StringVar()
        self.train_label = tk.Label(self.frame, textvariable=self.train_info)

        self.train_label.grid(row=5, column=0, columnspan=2, pady=10)
        self.train_btn = tk.Button(self.frame, bg='grey', fg='black', text='Room-Level Train', width=25, pady=10,
                                   command=self.room_train)
        self.train_btn.grid(row=6, column=0, columnspan=2, pady=5)

        self.exitButton = tk.Button(self.frame, bg='grey', fg='red', text='Exit', width=25,
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
                self.f = open(self.file_name, 'a')
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
                '_' + datetime.now().strftime('%m_%d_%H_%M')+'.txt'

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
        self.width = 600
        self.height = 800

        self.canvas = tk.Canvas(
            self.master, bg="white", width=self.width, height=self.height)
        self.canvas.bind("<Button-1>", self.draw)
        self.canvas.bind("<Motion>", self.mouse_motion)

        self.draw_grid()

        self.canvas.pack(side=tk.LEFT)

        self.canvas.tag_bind("draggable", "<ButtonPress-1>",
                             self.button_press)
        self.canvas.tag_bind("draggable", "<Button1-Motion>",
                             self.button_motion)

        self.v = tk.IntVar(self.master, 0)

        values = {"Draw": self.Mode.DRAW,
                  "Reverse": self.Mode.REVERSE,
                  "Delete": self.Mode.DELETE
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
        self.monitor_btn = tk.Button(frame, bg='grey', fg='black', text="Start Scan", pady=10, highlightbackground='black',
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
        self.train_btn.pack(pady=10, expand=True, fill=tk.BOTH)

        self.exitButton = tk.Button(
            frame, text='Exit', fg='red', command=self.exit_train)
        self.exitButton.pack(pady=10, expand=True, fill=tk.BOTH)

        frame.pack(side=tk.LEFT, padx=10, pady=10, expand=True)

        self.folder = dir_path + '/data'
        Path(self.folder).mkdir(parents=True, exist_ok=True)
        self.f, self.path_f = None, None
        self.path_name = self.folder + '/train_traj_' + \
            datetime.now().strftime('%m_%d_%H_%M')+'.txt'

    def draw_grid(self):
        grid_size = 50
        x1 = 0
        x2 = self.width
        for k in range(0, self.height+grid_size, grid_size):
            y1 = k
            y2 = k
            self.canvas.create_line(
                x1, y1, x2, y2, fill='#eeeeee')

        y1 = 0
        y2 = self.height
        for k in range(0, self.width+grid_size, grid_size):
            x1 = k
            x2 = k
            self.canvas.create_line(x1, y1, x2, y2, fill='#eeeeee')

    def exit_train(self):
        if self.f:
            self.f.close()
        if self.path_f:
            self.path_f.close()
        self.master.destroy()

    def traj_train(self):
        self.train = TrajTrain(dir_path, self.master)
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
        self.draw_mode = self.Mode.MOVE.value
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
                self.f = open(self.file_name, 'a')
                self.f.write('room unknown ' + str(datetime.now()) + '\n')
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
            self.file_name = self.folder + '/traj_' + \
                str(self.paths[-1][0]) + '_' + str(self.paths[-1][1]) + '.txt'
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

        if self.draw_mode == self.Mode.REVERSE.value:
            items = self.canvas.find_withtag("draggable")
            for i in items:
                self.canvas.itemconfig(i, fill=self.color)
            c = self.canvas.coords(item)
            self.paths.append([datetime.now().strftime(
                '%m_%d_%H_%M'), (c[2], c[3], c[0], c[1])])
            self.canvas.create_line(c[2], c[3], c[0], c[1], arrow=self.arrow, arrowshape=(16, 20, 6),
                                    fill='blue', width=self.width, tags="draggable")
            self.clear_radio()
        elif self.draw_mode == self.Mode.DELETE.value:
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
        if self.draw_mode == self.Mode.MOVE.value:
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
        if self.draw_mode == self.Mode.DRAW.value:
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
                self.paths.append(
                    [datetime.now().strftime('%m_%d_%H_%M'), line])
                self.arrow = tk.LAST
                self.color = 'black'
                self.width = 4
                self.canvas.create_line(*line, arrow=self.arrow, arrowshape=(16, 20, 6),
                                        fill='blue', width=self.width, tags="draggable")
                self.clear_radio()
                self.update_path()

    class Mode(Enum):
        DRAW = 1
        SELECT = 2
        REVERSE = 3
        MOVE = 4
        DELETE = 5


# %%
class FloorPlan:
    class Direction(Enum):
        VERTICAL = 1
        HORIZONTAL = 2

    def __init__(self, master, title):
        self.master = master
        self.master.title(title)
        self.master.geometry('850x800')
        self.width = 600
        self.height = 800

        self.canvas = tk.Canvas(
            self.master, bg="white", width=self.width, height=self.height)

        self.draw_grid()

        self.canvas.pack(side=tk.LEFT)

        self.frame = tk.Frame(self.master)

        self.drawButton = tk.Button(self.frame, bg='grey', fg='black', text='Draw Raw Floorplan',
                                    command=self.draw_raw, pady=10)
        self.drawButton.pack(expand=True, fill=tk.BOTH, pady=10)

        self.drawButton = tk.Button(self.frame, bg='grey', fg='black', text='Draw Shifted Floorplan',
                                    command=self.draw_shifted, pady=10)
        self.drawButton.pack(expand=True, fill=tk.BOTH, pady=10)

        self.drawButton = tk.Button(self.frame, bg='grey', fg='black', text='Draw Final Floorplan',
                                    command=self.draw_final, pady=10)
        self.drawButton.pack(expand=True, fill=tk.BOTH, pady=10)

        self.exitButton = tk.Button(self.frame, bg='grey', fg='red', text='Exit',
                                    command=self.master.destroy)
        self.exitButton.pack(expand=True, fill=tk.BOTH, pady=10)

        self.frame.pack(expand=True)

        self.load_raw()
        self.colors = cm.get_cmap('jet', len(self.rooms))
        self.hex_colors = []
        self.cv_colors = []
        for i in self.room_range:
            rgb = self.colors(i)
            self.hex_colors.append(colors.rgb2hex(rgb))
            self.cv_colors.append(
                (int(255*rgb[2]), int(255*rgb[1]), int(255*rgb[0])))

    def load_raw(self):
        self.rooms, self.result = load(open(
            dir_path + '/values/traj.sav', 'rb'))
        self.room_range = range(len(self.rooms))
        self.rooms_raw = defaultdict(list)
        self.rooms_center_raw = defaultdict(list)
        self.rooms_path_direction = defaultdict(list)
        self.rooms_shift = defaultdict(list)
        self.paths = []
        for path, x, order, guassian_room_sizes in self.result:
            path = [int(''.join([c for c in i if c.isdigit()]))
                    for i in path.split(' ')]
            self.paths.append(path)

            start_points = {}
            end_points = {}
            for i, j in zip(x, order):
                if j not in start_points:
                    start_points[j] = i
                end_points[j] = i
            # print(start_points)
            # print(end_points)

            x1, y1, x2, y2 = path
            delta_x = x2-x1
            delta_y = y2-y1
            direction = self.Direction.HORIZONTAL
            if abs(delta_y/delta_x) > 1:
                direction = self.Direction.VERTICAL

            x_length = x[-1]
            room_widths = {}
            for i in start_points.keys():
                room_height = end_points[i]-start_points[i]
                room_size = guassian_room_sizes[i]
                while room_size > x_length:
                    room_size /= 2
                room_width = (room_size + room_height) / 2
                room_widths[i] = room_width
                coords, center_coords, shift = self.calc_raw_coords(
                    start_points[i]/x_length, end_points[i]/x_length, room_width/x_length, x1, y1, delta_x, delta_y, direction)
                self.rooms_raw[i].append(coords)
                self.rooms_center_raw[i].append(center_coords)
                self.rooms_path_direction[i].append(direction)
                self.rooms_shift[i].append(shift)
            # print(room_widths)
        # print(self.rooms_raw)
        self.shift_calced = False
        self.rooms_shifted = defaultdict(list)
        self.rooms_center_shifted = defaultdict(list)
        self.final_calced = False
        self.rooms_final = defaultdict(list)
        self.rooms_center_final = defaultdict(list)

    def draw_grid(self):
        grid_size = 50
        x1 = 0
        x2 = self.width
        for k in range(0, self.height+grid_size, grid_size):
            y1 = k
            y2 = k
            self.canvas.create_line(
                x1, y1, x2, y2, fill='#eeeeee')

        y1 = 0
        y2 = self.height
        for k in range(0, self.width+grid_size, grid_size):
            x1 = k
            x2 = k
            self.canvas.create_line(x1, y1, x2, y2, fill='#eeeeee')

    def draw_path(self):
        for path in self.paths:
            self.canvas.create_line(path)

    def reset_canvas(self):
        self.canvas.delete("all")
        self.draw_grid()
        self.draw_path()
        self.images = []

    def draw_raw(self):
        self.reset_canvas()
        self.draw_polys(self.rooms_raw, self.rooms_center_raw, 0.2, 2)

    def draw_polys(self, rooms, room_lables, ap, w):
        # print(rooms, room_lables)
        for i in rooms.keys():
            for coords in rooms[i]:
                self.create_polygon(*coords,
                                    fill=self.hex_colors[i], outline=self.hex_colors[i], alpha=ap, width=w)
            for coords in room_lables[i]:
                self.canvas.create_text(*coords, text=self.rooms[i])

    def draw_shifted(self):
        self.reset_canvas()
        self.calc_shifted()
        self.draw_polys(self.rooms_shifted, self.rooms_center_shifted, 0.2, 2)

    def calc_shifted(self):
        if not self.shift_calced:
            for i in self.rooms_raw.keys():
                coords = self.rooms_raw[i]
                center_coords = self.rooms_center_raw[i]
                directions = self.rooms_path_direction[i]
                shifts = self.rooms_shift[i]
                length = len(directions)
                avg_x = sum([x[0] for x in center_coords])/length
                avg_y = sum([x[1] for x in center_coords])/length
                for j in range(length):
                    direction = directions[j]
                    x1, y1, x2, y2, x3, y3, x4, y4 = coords[j]
                    x, y = center_coords[j]
                    shift = shifts[j]
                    if direction == self.Direction.VERTICAL:
                        if x > avg_x:
                            shift = -shift
                        elif x == avg_x:
                            shift = 0
                        x1 += shift
                        x2 += shift
                        x3 += shift
                        x4 += shift
                        x += shift
                    else:
                        if y > avg_y:
                            shift = -shift
                        elif y == avg_y:
                            shift = 0
                        y1 += shift
                        y2 += shift
                        y3 += shift
                        y4 += shift
                        y += shift
                    self.rooms_shifted[i].append(
                        (x1, y1, x2, y2, x3, y3, x4, y4))
                    self.rooms_center_shifted[i].append((x, y))
            self.shift_calced = True

    def draw_final(self):
        self.reset_canvas()
        self.calc_shifted()
        self.calc_final()
        self.draw_full_image()
        self.draw_polys(self.rooms_final, self.rooms_center_final, 0.2, 5)

    def calc_final(self):
        if not self.final_calced:
            b_images = self.calc_image((1, 0, 0))
            g_images = self.calc_image((0, 1, 0))

            # images = {}
            self.full_image = np.zeros([self.height, self.width, 3],
                                       dtype=np.uint8)
            for i in self.room_range:
                image = np.zeros([self.height, self.width, 3],
                                 dtype=np.uint8) + b_images[i]
                for j in self.room_range:
                    if j != i:
                        image += g_images[j]
                rowbounds = defaultdict(list)
                colbounds = defaultdict(list)
                area_sum = 0
                x, y = 0, 0
                for p in range(self.height):
                    for q in range(self.width):
                        if image[p][q][0] > image[p][q][1]:
                            scale = image[p][q][0]
                            image[p][q] = scale
                            rowbounds[p].append(q)
                            colbounds[q].append(p)
                            area_sum += scale
                            x += scale*q
                            y += scale*p
                        else:
                            image[p][q] = (0, 0, 0)
                x = int(x/area_sum)
                y = int(y/area_sum)
                center = (x, y)
                rows = [max(ii)-min(ii) for ii in rowbounds.values()]
                cols = [max(ii)-min(ii) for ii in colbounds.values()]
                rows = [ii for ii in rows if ii != 0]
                cols = [ii for ii in cols if ii != 0]
                rows.sort()
                cols.sort()
                rows = rows[(len(rows)//3):]
                cols = cols[(len(cols)//3):]
                row_median, col_median = median(rows), median(cols)
                row_median, col_median = sum(
                    rows)/len(rows), sum(cols)/len(cols)
                row_median = int(row_median/2)
                col_median = int(col_median/2)

                norm_img = np.zeros((self.height, self.width))
                image = cv.normalize(image,  norm_img, 0, 255, cv.NORM_MINMAX)
                cv_color = self.cv_colors[i]
                for p in range(800):
                    for q in range(600):
                        scale = image[p][q][0]
                        image[p][q] = tuple([int(tmp*scale/255)
                                             for tmp in cv_color])

                # radius = int((row_median + col_median)/2)
                # cv.circle(image, center, radius, cv_color, 2)
                # images[i] = image
                self.full_image += image
                self.rooms_final[i].append((x-row_median, y-col_median,
                                            x+row_median, y-col_median,
                                            x+row_median, y+col_median,
                                            x-row_median, y+col_median,))
                self.rooms_center_final[i].append(center)
            self.calc_full_image()
            # cv.imshow('full_image', self.full_image)
            self.final_calced = True

    def calc_full_image(self):
        image = cv.cvtColor(self.full_image, cv.COLOR_BGR2RGB)
        image = Image.fromarray(image)
        image.putalpha(64)
        # dump(image, open('/Users/mili/Desktop/test/full_image.sav', 'wb'))
        self.imgtk = ImageTk.PhotoImage(image=image)

    def draw_full_image(self):
        self.canvas.create_image(
            self.width//2, self.height//2, image=self.imgtk)

    def calc_image(self, color):
        images = {}
        for i in self.room_range:
            images[i] = np.zeros([self.height, self.width, 3], dtype=np.uint8)
        for i in self.rooms_shifted.keys():
            image = images[i]
            for coords in self.rooms_shifted[i]:
                pts = np.array(coords).reshape((-1, 1, 2))
                tmp = np.zeros([self.height, self.width, 3], dtype=np.uint8)
                cv.fillPoly(tmp, [pts], color, cv.LINE_8)
                image += tmp
            images[i] = image
        return images

    def calc_raw_coords(self, start, end, width, x1, y1, delta_x, delta_y, direction):
        x11 = x1 + start*delta_x
        y11 = y1 + start*delta_y
        x22 = x1 + end*delta_x
        y22 = y1 + end*delta_y
        h = width/2
        x1 = int(x22 - h*delta_y)
        y1 = int(y22 + h*delta_x)
        x2 = int(x11 - h*delta_y)
        y2 = int(y11 + h*delta_x)
        x3 = int(x11 + h*delta_y)
        y3 = int(y11 - h*delta_x)
        x4 = int(x22 + h*delta_y)
        y4 = int(y22 - h*delta_x)
        shift = (abs(h*delta_x))
        if direction == self.Direction.VERTICAL:
            shift = abs(h*delta_y)
        return (x1, y1, x2, y2, x3, y3, x4, y4), ((x11+x22)//2, (y11+y22)//2), int(shift)

    def create_polygon(self, *args, **kwargs):
        if "alpha" in kwargs:
            if "fill" in kwargs:
                # Get and process the input data
                fill = self.master.winfo_rgb(kwargs.pop("fill"))\
                    + (int(kwargs.pop("alpha") * 255),)
                outline = kwargs.pop(
                    "outline") if "outline" in kwargs else None
                width = kwargs.pop(
                    "width") if "width" in kwargs else None

                # We need to find a rectangle the polygon is inscribed in
                # (max(args[::2]), max(args[1::2])) are x and y of the bottom right point of this rectangle
                # and they also are the width and height of it respectively (the image will be inserted into
                # (0, 0) coords for simplicity)
                image = Image.new("RGBA", (max(args[::2]), max(args[1::2])))
                ImageDraw.Draw(image).polygon(
                    args, fill=fill)
                ImageDraw.Draw(image).line(
                    args, fill=outline, width=width)

                # prevent the Image from being garbage-collected
                self.images.append(ImageTk.PhotoImage(image))
                # insert the Image to the 0, 0 coords
                return self.canvas.create_image(0, 0, image=self.images[-1], anchor="nw")
            raise ValueError("fill color must be specified!")
        return self.canvas.create_polygon(*args, **kwargs)


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
