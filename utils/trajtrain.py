# %%
from sklearn.ensemble import RandomForestClassifier
from pickle import load

from .ml.combinetxt import combinetxt
from .ml.preprocess import *

# %%


class TrajTrain:
    def __init__(self, dir_path) -> None:
        self.dir_path = dir_path
        self.modelname = self.dir_path + '/values/model.sav'
        with open(self.modelname, 'rb') as f:
            self.train_df, self.sorted_bssid, self.rooms, self.rooms_mean, self.classifier = load(
                f)

    def combine(self):
        pattern = 'train_traj_*.txt'
        out_name = 'train_traj_combined.txt'
        self.path_filename = combinetxt(self.dir_path, pattern, out_name)
        return "Path Combined"

    def calc_pred(self, test_filename):
        test_df, _ = load_data(
            test_filename, sorted_bssid=self.sorted_bssid, process=test_process)
        X_test, _ = get_attributes(test_df, self.sorted_bssid)
        y_proba = self.classifier.predict_proba(X_test)
        return pd.DataFrame(y_proba)

    def preprocess(self):
        try:
            with open(self.path_filename) as f:
                for line1 in f:
                    line2 = next(f)
                    print(line1, line2)
        except StopIteration:
            print('End reading', self.path_filename)

        return "Preprocess Finished"

    def train(self):
        return "Trajectory Trained"
