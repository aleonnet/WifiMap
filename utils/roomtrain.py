# %%
from .ml.combinetxt import combinetxt
from .ml.preprocess import *
from sklearn.ensemble import RandomForestClassifier
from pickle import dump

# %%


class RoomTrain:
    def __init__(self, dir_path) -> None:
        self.dir_path = dir_path

    def combine(self):
        self.train_filename = combinetxt(self.dir_path)
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
        dump(self.classifier, open(self.modelname, 'wb'))
        return "Model Trained"
