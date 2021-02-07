# %%
# imports


import pandas as pd
import re

test = False
# test = True


# %%
# function txt_to_dict(file_name)


def txt_to_dict(file_name):
    filef = open(file_name, 'r')
    data_dict = {'room': [], 'time': [], 'bssid': [], 'rssi': []}
    bssid_set = set()
    while True:
        headline = filef.readline().split()
        if not headline:
            break
        bssid_list = []
        rssi_list = []
        line = filef.readline()  # skip the title line
        while "BSSID" not in line:
            headline = line.split()
            line = filef.readline()  # skip the empty line
            if not line:
                break
        line = filef.readline().split()  # first data line
        pattern = '([0-9A-F]{2}[:-]){5}([0-9A-F]{2})'
        flags = re.I  # ignore case
        valid = True
        while line:
            for i in range(len(line)):
                match = re.search(pattern, line[i], flags)
                if match:
                    try:
                        bssid_set.add(line[i])
                        bssid_list.append(line[i])
                        rssi_list.append(int(line[i + 1]))
                    except ValueError as e:
                        valid = False
                        print(e)
                    break
            line = filef.readline().split()
        if "raw" in file_name:
            line = filef.readline()  # skip empty line
        if bssid_list and valid:
            data_dict['room'].append(int(headline[1]))  # int
            data_dict['time'].append(headline[2] + "-" + headline[3])
            data_dict['bssid'].append(bssid_list)
            data_dict['rssi'].append(rssi_list)  # int
    filef.close()
    return data_dict, sorted(bssid_set)


# %%
# test txt_to_dict


def test_data_dict(data_dict, sorted_bssid):
    print("all bssid nums:", len(sorted_bssid))
    print("instance nums:", len(data_dict['room']))
    print(data_dict['bssid'][0])
    print(data_dict['rssi'][0], "\n")


if test:
    file_name = 'data/testMac.txt'
    file_name2 = 'data/test_raw_Ji.txt'
#     data_dict, sorted_bssid = txt_to_dict(file_name)
#     data_dict2, sorted_bssid2 = txt_to_dict(file_name2)
#     test_data_dict(data_dict, sorted_bssid)
#     test_data_dict(data_dict2, sorted_bssid2)


# %%
# function dict_to_data_frame(data_dict, sorted_bssid)


def dict_to_data_frame(data_dict, sorted_bssid):
    cols = ['room'] + sorted_bssid
    data_frame = pd.DataFrame(columns=cols, index=data_dict['time'])
    for i in range(len(data_frame)):
        data_frame['room'].iloc[i] = data_dict['room'][i]
        bssid_list = data_dict['bssid'][i]
        rssi_list = data_dict['rssi'][i]
        for j, bssid in enumerate(bssid_list):
            if bssid in sorted_bssid:
                data_frame[bssid].iloc[i] = rssi_list[j]
    return data_frame


# %%
# test dict_to_data_frame


# if test:
#     data_frame = dict_to_data_frame(data_dict, sorted_bssid)
#     data_frame2 = dict_to_data_frame(data_dict2, sorted_bssid2)
#     print(data_frame.info(), "\n")
#     print(data_frame2.info())


# %%
# function load_data(file_name, sorted_bssid=None, process=no_process, value=-100)


def no_process(data_frame, value):
    pass


def test_process(data_frame, value):
    data_frame.fillna(value, inplace=True)


def train_process(data_frame, value):
    rooms = set(data_frame['room'])
    for i in range(1, len(rooms) + 1):
        data_frame.loc[data_frame['room'] == i].fillna(
            data_frame.loc[data_frame['room'] == i].mean(), inplace=True)
    data_frame.fillna(value, inplace=True)


def get_room_mean(data_frame):
    rooms = ["room" + str(i) for i in set(data_frame['room'])]
    rooms_mean = {}
    for i in range(1, len(rooms) + 1):
        room_mean = data_frame.loc[data_frame['room'] == i].mean()
        rooms_mean["room" + str(i)] = room_mean.to_dict()
    return rooms, rooms_mean


def load_data(file_name, sorted_bssid=None, process=no_process, value=-100):
    data_dict, origin_sorted_bssid = txt_to_dict(file_name)
    if not sorted_bssid:
        sorted_bssid = origin_sorted_bssid
    data_frame = dict_to_data_frame(data_dict, sorted_bssid)
    process(data_frame, value)
    return data_frame, sorted_bssid


# %%
# test load_data

if test:
    data_frame, sorted_bssid = load_data(file_name, sorted_bssid=[
        '84:d4:7e:4a:4c:02', '84:d4:7e:4a:4c:00'], process=test_process)
    data_frame2, sorted_bssid2 = load_data(file_name2, process=train_process)
    rooms, rooms_mean = get_room_mean(data_frame)
    print(rooms_mean)


# %%
# function get_attributes(data_frame, sorted_bssid)


def get_attributes(data_frame, sorted_bssid):
    features = data_frame[sorted_bssid].to_numpy()
    labels = data_frame['room']
    return features, labels
