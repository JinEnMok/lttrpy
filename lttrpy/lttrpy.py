# !/usr/bin/env python

# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license

# Inspired by Sena Bayram's script

# TODO: different output formats, common ratings, concurrency, display film year, output sorting
# TODO: display only liked
# TODO: display only common ratings
# TODO: display reviews
# TODO: more verbosity during stages
# TODO: interactive mode
# TODO: a prettier table?

# TODO: replace importlib

# concurrency: https://realpython.com/python-download-file-from-url/#using-the-asynchronous-aiohttp-library

import argparse
import importlib.util
import os
import sys

# from concurrent.futures import ThreadPoolExecutor


if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 9):
    print("This script requires Python 3.9 or newer to run. Exiting.")
    quit()

try:
    from bs4 import BeautifulSoup, SoupStrainer
    import requests
except ImportError:
    print("BeautifulSoup or requests not found. Exiting.")
    quit()


class LetterboxdProfile:
    def __init__(self,
                 username,
                 session,
                 parser,
                 verb=False, quiet=False):
                 
        self.username = username
        self.session = session
        self.parser = parser

        # TODO: replace those with iterators to save space
        # gotta come up with a creative way to iterate over them
        self.__pages = self.get_pages()
        self.__soups = tuple(self.__soupify())
        self.__snippets = tuple(snip for soup in self.__soups
                                     for snip in soup.find_all("p", class_="poster-viewingdata"))

        self.ids = tuple(id for soup in self.__soups
                            for id in self.__get_ids(soup))

        self.film_names = tuple(film for soup in self.__soups
                                     for film in self.__get_film_names(soup))

        self.ratings = tuple(self.__get_rating(snip) for snip in self.__snippets)
        self.likes = tuple(self.__get_likes(snip) for snip in self.__snippets)
        self.film_data = dict(zip(self.ids,
                                  zip(self.film_names,
                                      self.ratings,
                                      self.likes)))

    def __len__(self):
        return len(self.film_data)

    def __str__(self):
        return f"User {self.username}: {len(self)} watched films."

    def __repr__(self):
        return f"Profile({self.username!r})"

    def __eq__(self, other):
        return self.film_data == other.film_data

    def __ne__(self, other):
        return self.film_data != other.film_data

    def __getitem__(self, key):
        if type(key) is str:
            return self.film_data[key]
        elif type(key) in (slice, int):
            return tuple(self.film_data.values())[key]

    #def __iter__(self):
    #    return iter(self.film_data)

    def __contains__(self, item):
        return item in self.film_data

    def __bool__(self):
        return len(self.film_data) > 0

    # TODO: find a way to reuse this page
    def __get_max_page(self):
        page = self.session.get(f"https://letterboxd.com/{self.username}/films")
        if page.status_code != 200:
            # TODO: implement a more graceful skip
            print(f"Could not find {self.username}'s page. Exiting")
            quit()
        soup = BeautifulSoup(page.text,
                             self.parser,
                             parse_only=SoupStrainer(class_="paginate-page"))
        return int(tuple(soup.strings)[-1])

    # TODO: make this faster
    def get_pages(self):
        page_url = f"https://letterboxd.com/{self.username}/films/page/"
        return (self.session.get(page_url + str(page_num)).text
                for page_num in range(1, 1 + self.__get_max_page()))

    def __soupify(self):
        return (BeautifulSoup(page,
                              self.parser,
                              parse_only=SoupStrainer(class_="poster-container"))
                for page in self.__pages)

    # TODO: make this faster
    def __get_film_names(self, soup):
        return (img["alt"] for img in soup.find_all("img"))

    def __get_ids(self, soup):
        return (film["data-film-id"] for film in soup.find_all("div"))

    def __get_rating(self, snippet):
        if snippet.find("span") and snippet.find(class_="rating"):
            rating = snippet.find("span").attrs["class"][-1].removeprefix("rated-") \
                     + "/10"
        else:
            rating = "n/r"
        return rating

    def __get_likes(self, snippet):
        if snippet.find(class_="like"):
            return True
        else:
            return False

    def overlap(self, *users):
        return set(self.ids).intersection(*(set(user.ids) for user in users))


def get_args():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose",
                        help="increase output verbosity",
                        action="store_true")
    group.add_argument("-q", "--quiet",
                        help='print output to stdout',
                        action="store_true")

    parser.add_argument("-f", "--file",
                        dest="output",
                        nargs="?",
                        help="name and path of the output file",
                        default="common films.txt")

    parser.add_argument("users",
                        type=str,
                        # action="append",
                        nargs="+")

    return parser.parse_args()

def main():
    args = get_args()
    
    if importlib.util.find_spec("lxml"):
        parser = "lxml"
    else:
        parser = "html.parser"
        if args.verbose:
            print("lxml not found. Using html.parser instead.\n"
                  + "lxml is a significantly faster alternative.\n")

    if not importlib.util.find_spec("cchardet"):
        if args.verbose:
            print("The faust-cchardet library can make this script faster.\n")

    with requests.Session() as session:
        profiles = tuple(LetterboxdProfile(user,
                                           session,
                                           parser=parser,
                                           verb=args.verbose,
                                           quiet=args.quiet) for user in args.users)

    common_ids = profiles[0].overlap(*profiles)

    #flexible column width
    #some magic numbers here, tune according to taste
    col_w = {"film":(max(len(profiles[0].film_data[film_id][0]) for film_id in common_ids) + 5)}
    for user in args.users:
        col_w.update({user:(max(len(f"{user}'s rating") + 5, len("no rating" + "(liked)") + 5))})


    with open(args.output, "w", encoding="utf-8") as f:
        f.write(f"There are {len(common_ids)} common films for those users.\n")
        f.write("n/r stands for 'no rating'\n\n")

        f.write("Film name".ljust(col_w["film"]))

        for user in args.users:
            f.write(f"{user}'s rating".center(col_w[user]))
        f.write("\n\n")

        # TODO: alphabetic (or other) ordering for the films
        for film_id in common_ids:
            f.write(profiles[0].film_data[film_id][0].ljust(col_w["film"]))
            for user in profiles:
                if user.film_data[film_id][2]:
                    f.write(f"{user.film_data[film_id][1]} (liked)".center(col_w[user.username]))
                else:
                    f.write(f"{user.film_data[film_id][1]}".center(col_w[user.username]))
            f.write("\n")

        if args.verbose:
            print(f"Wrote output to {os.getcwd()}/{args.output}")


if __name__ == "__main__":
    main()
