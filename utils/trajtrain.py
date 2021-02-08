# %%
from sklearn.ensemble import RandomForestClassifier
from pickle import load
from glob import glob
import os

from .ml.combinetxt import combinetxt
from .ml.preprocess import *

# %%


class TrajTrain:
    def __init__(self, dir_path) -> None:
        self.dir_path = dir_path
        self.modelname = self.dir_path + '/values/model.sav'
        try:
            with open(self.modelname, 'rb') as f:
                self.train_df, self.sorted_bssid, self.rooms, self.rooms_mean, self.classifier = load(
                    f)
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
        X_test, _ = get_attributes(test_df, self.sorted_bssid)
        y_proba = self.classifier.predict_proba(X_test)
        return pd.DataFrame(y_proba)

    def preprocess(self):
        self.all_trajs = set(
            glob(os.path.join(self.dir_path, 'data', 'traj_*.txt')))
        print(self.all_trajs)
        self.valid_trajs = []
        try:
            with open(self.combined_file_name) as f:
                for line1 in f:
                    line2 = next(f)
                    test_file_name = os.path.join(self.dir_path, 'data', 'traj_' + line1.strip(
                        '\n')+'_'+line2.strip('\n')+'.txt')
                    if test_file_name in self.all_trajs:
                        print(test_file_name)
                        self.valid_trajs.append(test_file_name)
                    else:
                        print('Wifi data not collected for traj',
                              line2.strip('\n'))

        except StopIteration:
            print('End reading', self.combined_file_name)

        return 'Preprocess Finished'

    def train(self):
        for test_file_name in self.valid_trajs:
            df = self.calc_pred(test_file_name)
            print(df)
        return 'Trajectory Trained'
