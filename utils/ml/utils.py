# Python ≥3.5 is required
import os
import numpy as np
import pandas as pd
import sklearn
import warnings
import urllib.request
import itertools
import cv2
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import datetime
from IPython.core.interactiveshell import InteractiveShell

import sys
assert sys.version_info >= (3, 5)

# Scikit-Learn ≥0.20 is required
assert sklearn.__version__ >= "0.20"


# Common imports

# To plot pretty figures
# %matplotlib inline

# plt.style.use(['seaborn-pastel','dark_background'])
mpl.rcParams['figure.facecolor'] = 'whitesmoke'
mpl.rcParams['axes.facecolor'] = 'white'
mpl.rcParams['font.family'] = 'monospace'
mpl.rcParams['font.size'] = 16
# mpl.rcParams['figure.figsize'] = 7, 10
mpl.rc('axes', labelsize=16)
mpl.rc('xtick', labelsize=14)
mpl.rc('ytick', labelsize=14)

# show multiple outputs
InteractiveShell.ast_node_interactivity = "all"

# pd.set_option('display.max_columns', None)
# pd.set_option('display.max_rows', None)

# download images

# Where to save the figures
PROJECT_ROOT_DIR = "."
CHAPTER_ID = datetime.datetime.now().strftime('%m_%d')
IMAGES_PATH = os.path.join(PROJECT_ROOT_DIR, "images", CHAPTER_ID)
os.makedirs(IMAGES_PATH, exist_ok=True)


def save_fig(fig_id, tight_layout=True, fig_extension="png", resolution=300):
    path = os.path.join(IMAGES_PATH, fig_id + "." + fig_extension)
    print("Saving figure", fig_id)
    if tight_layout:
        plt.tight_layout()
    plt.savefig(path, format=fig_extension, dpi=resolution)


def download_fig(fig_id, fig_url, fig_extension="jpg"):
    print("Downloading", fig_url)
    req = urllib.request.Request(url)
    # Customize the default User-Agent header value:
    req.add_header('User-Agent', 'Mozilla/5.0')
    response = urllib.request.urlopen(req)
    image = response.read()
    filename = fig_id + "." + fig_extension
    with open(os.path.join(IMAGES_PATH, filename), "wb") as file:
        file.write(image)


def plot_confusion_matrix(cm, target_names, title='Confusion matrix', cmap=None, normalize=True):
    """Citiation
    ---------
    http://scikit-learn.org/stable/auto_examples/model_selection/plot_confusion_matrix.html

    """
    accuracy = np.trace(cm) / float(np.sum(cm))
    misclass = 1 - accuracy

    if cmap is None:
        cmap = plt.get_cmap('Blues')

    width = 6
    height = 8
    plt.figure(figsize=(height, width))
    plt.imshow(cm, interpolation='nearest', cmap=cmap)
    plt.title(title)
    plt.colorbar()

    if target_names is not None:
        tick_marks = np.arange(len(target_names))
        plt.xticks(tick_marks, target_names, rotation=45)
        plt.yticks(tick_marks, target_names)

    if normalize:
        cm = cm.astype('float') / cm.sum(axis=1)[:, np.newaxis]

    thresh = cm.max() / 1.5 if normalize else cm.max() / 2
    for i, j in itertools.product(range(cm.shape[0]), range(cm.shape[1])):
        if normalize:
            plt.text(j, i, "{:0.4f}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")
        else:
            plt.text(j, i, "{:,}".format(cm[i, j]),
                     horizontalalignment="center",
                     color="white" if cm[i, j] > thresh else "black")

    plt.tight_layout()
    plt.ylabel('True label')
    plt.xlabel('Predicted label\naccuracy={:0.4f}; misclass={:0.4f}'.format(
        accuracy, misclass))
    return plt


# Ignore useless warnings (see SciPy issue #5998)
warnings.filterwarnings(action="ignore", message="^internal gelsd")

print("Setup finished!")
