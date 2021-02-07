# %%
# important imports


from sklearn.decomposition import PCA
import sklearn.preprocessing as preprocessing
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import json
from sklearn.ensemble import AdaBoostClassifier
from IPython.core.interactiveshell import InteractiveShell
from sklearn.svm import SVC
import utils
import preprocess
import datetime
import sys
from scipy import stats
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import cross_val_predict, cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import VotingClassifier
from sklearn.tree import DecisionTreeClassifier
import pickle

# %%
# train data load


sorted_bssid = None
load = False
# load = True
save = False
save = True
bssidfilename = 'values/bssids.txt'
username = 'qin'
prefix = username + '_'
surfix = '_' + username
modelname = 'models/' + username + '_model.sav'
feature_num = 30
# train_filename = 'data/trainMac.txt'
# test_filename = 'data/testMac.txt'
train_filename = 'data/trainAndroid.txt'
# test_filename = 'data/testAndroid.txt'
# train_filename = 'data/train_small_android.txt'
train_filename = 'data/train_raw' + surfix + '.txt'
test_filename = 'data/test_raw' + surfix + '.txt'
# test_filename = 'data/raw_train_room_12_01_03_18_04.txt'
# test_filename = '/Users/mili/Documents/WifiScanML/rawdata/jeff/train_room_8_12_12_17:07.txt'
# test_filename = '/Users/mili/Documents/WifiScanML/rawdata/jeff/train_room_9_12_12_17:13.txt'
# test_filename = '/Users/mili/Documents/WifiScanML/rawdata/jeff/train_room_10_12_12_17:16.txt'
# 8 1 -> 5
# 9 1 -> 5 -> 4
# 10 1 -> 5 -> 4 -> 3
# test_filename = 'data/test_raw' + surfix + '.txt'
# train_filename = 'data/train_raw_Ji.txt'
# test_filename = 'data/test_raw_Ji.txt'
# train_filename = 'data/train_raw_Jeff.txt'
# train_filename = 'data/trainAndroid.txt'
if load:
    with open(bssidfilename, 'r') as filehandle:
        sorted_bssid = json.load(filehandle)

train_df, sorted_bssid = preprocess.load_data(
    train_filename, sorted_bssid=sorted_bssid, process=preprocess.train_process)
rooms, rooms_mean = preprocess.get_room_mean(train_df)
X_train, y_train = preprocess.get_attributes(train_df, sorted_bssid)


# %%
# test data process function


test_df, _ = preprocess.load_data(
    test_filename, sorted_bssid=sorted_bssid, process=preprocess.test_process)
X_test, y_test = preprocess.get_attributes(test_df, sorted_bssid)


# %%
# pca analysis


pca = PCA(n_components=0.95)
X_reduced = pca.fit_transform(X_train)
# X_recovered = pca.inverse_transform(X_reduced)
print(pca.explained_variance_ratio_)

# %%
# define ML classifier


knn_clf = KNeighborsClassifier(n_neighbors=3)

softmax_reg = LogisticRegression(solver='lbfgs', C=1000, random_state=42)
tree_clf = DecisionTreeClassifier(random_state=42, min_samples_leaf=40)

log_clf = LogisticRegression(solver='lbfgs', random_state=42)
rnd_clf = RandomForestClassifier(n_estimators=500, random_state=42)
svm_clf = SVC(kernel='linear', gamma='auto', random_state=42)
# print(svm_clf.get_params)

ada_clf = AdaBoostClassifier(DecisionTreeClassifier(
    max_depth=2), n_estimators=200, algorithm='SAMME.R', learning_rate=0.5)
voting_clf = VotingClassifier(
    estimators=[('lr', log_clf), ('rf', rnd_clf),
                ('svc', svm_clf), ('knn', knn_clf)],
    voting='hard')


# %%
# choose ML classifier

# classifier = knn_clf
# classifier = svm_clf
classifier = rnd_clf
# classifier = softmax_reg
# classifier = tree_clf
# classifier = ada_clf
# classifier = voting_clf


# %%
# start training


train_predict = cross_val_predict(
    classifier, X_train, y_train, cv=3)

conf_mx = confusion_matrix(y_train, train_predict)
plt = utils.plot_confusion_matrix(cm=conf_mx, normalize=False,
                                  target_names=rooms,
                                  title=train_filename + ' cross validation')
if save:
    utils.save_fig(prefix + 'train_cfm_cv_' +
                   datetime.datetime.now().strftime('%m_%d_%H:%M'))
else:
    plt.show()

# sys.exit(0)

# %%
# train


classifier.fit(X_train, y_train)


# %%
# save the model to disk


pickle.dump(classifier, open(modelname, 'wb'))


# %%
# feature importance


def plotImportance(sorted_bssid, classifier):
    rooms_mean['feature_importances'] = classifier.feature_importances_
    df = pd.DataFrame(rooms_mean, index=sorted_bssid)
    x = df.values   # returns a numpy array
    min_max_scaler = preprocessing.MinMaxScaler()
    x_scaled = min_max_scaler.fit_transform(x)
    imp_df = pd.DataFrame(
        x_scaled, columns=rooms_mean.keys(), index=sorted_bssid)
    plt.figure(figsize=(8, 20))
    ax = sns.heatmap(imp_df, fmt='g', cmap='plasma')
    ax.set_xticklabels(rooms_mean.keys(), rotation=45)
    plt.title(str(feature_num) + ' out of ' +
              str(len(sorted_bssid)) + ' bssids chosen')
    if save:
        utils.save_fig(prefix +
                       'feature_importance', fig_extension='jpg')
    else:
        plt.show()


if not load or load:
    # for name, score in zip(sorted_bssid, classifier.feature_importances_):
    #     print(name, score)
    plotImportance(sorted_bssid, classifier)
    important_bssid = sorted(
        zip(sorted_bssid, classifier.feature_importances_), reverse=True, key=lambda x: x[1])[:feature_num]
    with open(bssidfilename, 'w') as filehandle:
        json.dump([i[0] for i in important_bssid], filehandle)

# sys.exit(0)

# %%
# train and test


# y_proba = classifier.predict_proba(X_test)
# InteractiveShell.ast_node_interactivity = 'all'
# tmp = utils.np.round(y_proba, 1)
# print(tmp)

window = 4

y_predict = classifier.predict(X_test)


def plotPred(y_predict, y_test, y_voted):
    cols = ['target', 'predict', 'voted']
    df = pd.DataFrame({'target': y_test, 
    'predict': y_predict, 'voted': y_voted}, columns=cols)
    df.reset_index().plot(x='index', y=cols, kind ='line', legend=True, 
                 subplots = True,sharex = True, figsize = (20,10), ls='none', marker='o')
    if save:
        utils.save_fig(prefix +
                       'voted_' + str(window) + '_' +
                       datetime.datetime.now().strftime('%m_%d_%H:%M'), fig_extension='jpg')
    else:
        plt.show()



n = len(y_predict)
y_voted = []
for i in range(1,n+1):
    y_voted.append(stats.mode(y_predict[max(0,i-window):i])[0][0])


plotPred(y_predict, y_test, y_voted)
y_predict = y_voted

y_proba = classifier.predict_proba(X_test)


def plotProb(y_proba, rooms):
    # df = pd.DataFrame(rooms_mean, index=sorted_bssid)
    # x = df.values   # returns a numpy array
    # min_max_scaler = preprocessing.MinMaxScaler()
    # x_scaled = min_max_scaler.fit_transform(x)
    imp_df = pd.DataFrame(
        y_proba, columns=rooms, index=range(len(y_proba)))
    plt.figure(figsize=(5, 15))
    ax = sns.heatmap(imp_df, fmt='g', cmap='plasma')
    ax.set_xticklabels(rooms, rotation=45)
    plt.title('Prediction Probabilities')
    if save:
        utils.save_fig(prefix +
                       'proba_' +
                       datetime.datetime.now().strftime('%m_%d_%H:%M'), fig_extension='jpg')
    else:
        plt.show()


plotProb(y_proba, rooms)

# sys.exit(0)

# %%
# plot confusion matrix
conf_mx = confusion_matrix(y_test, y_predict)
plt = utils.plot_confusion_matrix(cm=conf_mx, normalize=False,
                                  target_names=rooms,
                                  title='Confusion Matrix')
if save:
    utils.save_fig(prefix + 'train_cfm_svm_' +
                   datetime.datetime.now().strftime('%m_%d_%H:%M'))
else:
    plt.show()

# %%



for i, j in enumerate(y_predict):
    # if j == 4 and y_predict[i+1] == 5:
    if j == 2 and y_predict[i:i+5] == [2]*5:
        print(i)
        break
# %%
