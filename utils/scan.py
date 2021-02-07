# %%
import os
import subprocess

# %%
AIRPORT_PATH = [os.environ.get(
    'AIRPORT_PATH',
    '/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport')]


def build_airport_cmd(params):
    return AIRPORT_PATH + params


def call_cmd(*args):
    return subprocess.run(args, capture_output=True, text=True).stdout


def scan():
    cmd = build_airport_cmd(params=['-s'])
    results = call_cmd(*cmd)
    return results
