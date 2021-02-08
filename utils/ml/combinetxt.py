# %%
import os
import shutil
from glob import glob
from pathlib import Path

# %%


def combinetxt(dir_path, pattern, out_name):
    folder = dir_path + '/values'
    Path(folder).mkdir(parents=True, exist_ok=True)

    with open(folder + '/' + out_name, 'wb') as out_file:
        for file_name in glob(os.path.join(dir_path, 'data', pattern)):
            # print(file_name)
            if file_name == out_name:
                # don't want to copy the output into the output
                continue
            with open(file_name, 'rb') as read_file:
                shutil.copyfileobj(read_file, out_file)

    return folder + '/' + out_name
