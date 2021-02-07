# %%
import os
import shutil
from glob import glob
from utils.gui import dir_path

# %%


def combinetxt():
    pattern = 'train_room_*.txt'
    out_name = 'test_raw_combined.txt'

    with open('values/' + out_name, 'wb') as out_file:
        print(os.path.join(dir_path, pattern))
        for file_name in glob(os.path.join(dir_path, pattern)):
            print(file_name)
            if file_name == out_name:
                # don't want to copy the output into the output
                continue
            with open(file_name, 'rb') as read_file:
                shutil.copyfileobj(read_file, out_file)
