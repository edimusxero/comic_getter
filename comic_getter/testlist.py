import bs4 as bs
import re
import os
import urllib
import os.path
import shutil
import sys
import requests
import time
import argparse

parser = argparse.ArgumentParser(
    prog="comic_getter",
    description="comic_getter is a command line tool "
    "to download comics from readcomiconline.to.")

parser.add_argument("-i", "--input",  nargs=1, dest="input",
                    help="Get comic and all of it's issues from main link.")
parser.add_argument('-c', '--config', action='store_true', dest="config",
                    help='Edit config file.')
parser.add_argument('-x', "--single",  nargs=1, dest="single",
                    help="Get a single issue from a certain comic from it's link.")
parser.add_argument('-s', "--skip", nargs=1, type=int, default=[""],
                    dest="skip", help='Number of issues to skip.')
parser.add_argument('-r', '--rng', type=str, required=False, dest="range",
                        help='Issue range <1-10>')
parser.add_argument('-z', '--zip', dest="create_zip", action='store_true',
                        help='Create Zip File From Downloaded Issue')

args = parser.parse_args()

comics = [
'https://readcomiconline.to/Comic/Batman-2011/Annual-2?id=10683',
'https://readcomiconline.to/Comic/Batman-2011/Annual-3?id=10684',
'https://readcomiconline.to/Comic/Batman-2011/Issue-7?id=10679',
'https://readcomiconline.to/Comic/Batman-2011/Issue-8?id=10680'
]

args.rng = 'Annual'
rng = args.rng

new_list = []

def check_if_exists(x, ls):
    for text in ls:
        if x in text:
            new_list.append(text)

if rng == 'Annual':
    check_if_exists(rng, comics)
    comics = new_list

else:
    issue_range = rng.split('-')
    start = int(issue_range[0])
    stop = int(issue_range[1]) + 1
    series_range = range(start, stop)
    
    for dl_range in series_range:
        issue_range = (f'/Issue-{dl_range}?')
        check_if_exists(issue_range, comics)
    
    comics = new_list

print(*comics, sep='\n', flush=True)