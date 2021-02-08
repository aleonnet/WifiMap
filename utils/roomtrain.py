# %%
from sklearn.ensemble import RandomForestClassifier
from pickle import dump

from .ml.combinetxt import combinetxt
from .ml.preprocess import *


# %%


class RoomTrain:
    def __init__(self, dir_path) -> None:
        self.dir_path = dir_path

    def combine(self):
        pattern = 'train_room_*.txt'
        out_name = 'train_raw_combined.txt'
        self.train_filename = combinetxt(self.dir_path, pattern, out_name)
        return "Data Combined"

    def preprocess(self):
        self.train_df, self.sorted_bssid = load_data(
            self.train_filename, process=train_process)

        self.rooms, self.rooms_mean = get_room_mean(self.train_df)
        self.X_train, self.y_train = get_attributes(
            self.train_df, self.sorted_bssid)
        # print(self.train_df.head())
        return "Preprocess Finished"

    def train(self):
        self.modelname = self.dir_path + '/values/model.sav'
        self.classifier = RandomForestClassifier(
            n_estimators=500, random_state=42)

        self.classifier.fit(self.X_train, self.y_train)
        dump([self.train_df, self.sorted_bssid, self.rooms, self.rooms_mean, self.classifier],
             open(self.modelname, 'wb'))
        return "Model Trained"
