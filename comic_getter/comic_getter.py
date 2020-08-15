import argparse
import json
import operator
import os
from pathlib import Path
import sys
import time

from config_generator import ConfigJSON
from RCO_links import RCO_Comic

# Create terminal UI
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

# Check if config.json exists
if not ConfigJSON().config_exists():
    msg = "\nThere was no config.json file so let's create one.\n"
    print(msg)
    ConfigJSON().config_create()
    sys.exit()

# Download comic from link.
if args.input:
    comic = RCO_Comic(args.input[0])
    issues_links = list(comic.get_issues_links())
    issues_links.reverse()

    # Ignore determined links.
    if args.skip[0]:
        issues_links = issues_links[args.skip[0]:]

    # Delete already downloaded issues links
    issues_identifiers = [comic.get_comic_and_issue_name(
        link) for link in issues_links]
    downloaded_issues = filter(comic.is_comic_downloaded, issues_identifiers)
    links_fetcher = operator.itemgetter(0)
    downloaded_issues_links = [links_fetcher(
        issue) for issue in downloaded_issues]
    for link in issues_links[:]:
        if link in downloaded_issues_links:
            issues_links.remove(link)

    # Continue downloading remaining links.
    print("Issues will be downloaded one by one " 
        "and a browser will be opened for each issue.")
    time.sleep(2)
    for issue_link in issues_links:
        issue_data = comic.get_pages_links(issue_link)
        comic.download_all_pages(issue_data)

    print("\nFinished download.", flush=True)

if args.config:
    ConfigJSON().edit_config()

if args.single:
    print("Single issue will be downloaded", flush=True)
    if(args.create_zip):
        comic = RCO_Comic(args.single[0], args.create_zip)
    else:
        comic = RCO_Comic(args.single[0])
    issue_link = args.single[0]
    issue_data = comic.get_pages_links(issue_link)
    comic.download_all_pages(issue_data)

    print("Finished download.", flush=True)
