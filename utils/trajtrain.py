# %%
from scipy import stats
from .ml.preprocess import *
from .ml.combinetxt import combinetxt
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg,
                                               NavigationToolbar2Tk)
from matplotlib.figure import Figure
from sklearn.ensemble import RandomForestClassifier
from pickle import load, dump
from glob import glob
import os
import numpy as np
from astropy import modeling
from matplotlib import cm

import tkinter as tk
import matplotlib
matplotlib.use("TkAgg")


# %%


class TrajTrain:
    def __init__(self, dir_path, master) -> None:
        self.dir_path = dir_path
        self.master = master
        self.modelname = self.dir_path + '/values/model.sav'
        try:
            with open(self.modelname, 'rb') as f:
                self.train_df, self.sorted_bssid, self.rooms, self.rooms_mean, self.classifier = load(
                    f)
            self.colors = cm.jet(np.linspace(0, 1, len(self.rooms)))
            for i in range(len(self.rooms)):
                print(self.colors[i])
            for i in range(len(self.rooms)):
                print(self.colors[i])
        except:
            print('You must do room-level training first.')

    def combine(self):
        pattern = 'train_traj_*.txt'
        out_name = 'train_traj_combined.txt'
        self.combined_file_name = combinetxt(self.dir_path, pattern, out_name)
        return 'Path Combined'

    def calc_pred(self, test_file_name):
        test_df, _ = load_data(
            test_file_name, sorted_bssid=self.sorted_bssid, process=test_process)
        # print(test_df)
        X_test, _ = get_attributes(test_df, self.sorted_bssid)

        y_proba = self.classifier.predict_proba(X_test)
        return pd.DataFrame(y_proba)
        # return y_proba

    def preprocess(self):
        self.all_trajs = set(
            glob(os.path.join(self.dir_path, 'data', 'traj_*.txt')))
        # print(self.all_trajs)
        self.valid_trajs = []
        try:
            with open(self.combined_file_name) as f:
                for line1 in f:
                    line2 = next(f)
                    test_file_name = os.path.join(self.dir_path, 'data', 'traj_' + line1.strip(
                        '\n')+'_'+line2.strip('\n')+'.txt')
                    if test_file_name in self.all_trajs:
                        self.valid_trajs.append(test_file_name)
                    else:
                        print('Wifi data not collected for traj',
                              line2.strip('\n'))

        except StopIteration:
            print('End reading', self.combined_file_name)

        return 'Preprocess Finished'

    def train(self):
        fitter = modeling.fitting.LevMarLSQFitter()
        model = modeling.models.Gaussian1D()
        for test_file_name in self.valid_trajs:
            short_name = test_file_name.split('/')[-1][:-4]
            print(short_name)
            sim_df = self.calc_pred(test_file_name)
            n_steps = len(sim_df)
            # print(sim_df.shape, n_steps)
            # print(sim_df)
            fitted = []
            models = []
            X = np.atleast_2d(np.linspace(1, n_steps, num=n_steps)).T
            x = np.atleast_2d(np.linspace(1, n_steps, num=n_steps*10)).T
            # print(X, x)
            for i in range(len(self.rooms)):
                y = np.atleast_2d(sim_df[i]).T
                fitted_model = fitter(model, X, y)
                # if 0 < fitted_model.mean.value < len(sim_df)*2 and fitted_model.stddev.value < len(sim_df)+1:
                models.append((i, fitted_model.mean.value,
                               fitted_model.stddev.value))
                y_pred = fitted_model(x)
                # print(y_pred.shape)
                fitted.append(y_pred.flatten())
            self.plot_guassian_fit(X, sim_df, x, fitted, short_name)
            dump([fitted, models], open(
                '/Users/mili/Desktop/test/' + short_name+'.txt', 'wb'))
            order_result = self.calc_order(fitted, short_name, 4)
            # print(fitted)

        self.master.lift()
        return 'Trajectory Trained'

    def calc_order(self, fitted, short_name, window):

        order_df = pd.DataFrame(fitted)
        order = order_df.idxmax().values.tolist()
        voted = []
        voted_r = []
        for i in range(len(order)):
            voted.append(stats.mode(order[max(0, i-window+1):i+1])[0][0])
            voted_r.append(stats.mode(
                order[i:min(i+window, len(order))])[0][0])
        result = [stats.mode([order[i], voted[i], voted_r[i]])[0][0]
                  for i in range(len(order))]
        # print(order)
        # print(voted)
        # print(voted_r)
        # print(result)
        return result

    def plot_guassian_fit(self, X, sim_df, x, fitted, short_name):

        window = tk.Toplevel(self.master)
        window.title(short_name)

        fig = Figure(figsize=(5, 5))

        plot1 = fig.add_subplot(111)

        for i in range(len(self.rooms)):
            y = np.atleast_2d(sim_df[i]).T
            y_pred = fitted[i]
            plot1.scatter(
                X, y, s=10, color=self.colors[i], label=self.rooms[i] + ' Raw')
            plot1.plot(
                x, y_pred, color=self.colors[i], label=self.rooms[i] + ' Gaussian')

        plot1.set_xlabel('Time')
        plot1.set_ylabel('Similarity Score')
        plot1.set_ylim(0, 1)
        plot1.legend(loc='upper left')

        canvas = FigureCanvasTkAgg(fig,
                                   master=window)
        canvas.get_tk_widget().pack()
        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.update()
        canvas.get_tk_widget().pack()

        button = tk.Button(master=window, text="Exit",
                           fg='red', command=window.destroy)
        button.pack(side=tk.BOTTOM, fill=tk.BOTH)
