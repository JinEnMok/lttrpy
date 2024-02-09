# !/usr/bin/env python

# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license

# Inspired by Sena Bayram's script

# TODO: different output formats, common ratings,  film year, output sorting
# TODO: display only liked
# TODO: display only common ratings
# TODO: display reviews
# TODO: more verbosity during stages
# TODO: interactive mode
# TODO: a prettier table?

import trio
# import httpx
from httpx import AsyncClient
import lxml
import sys


if not (sys.version_info[0] >= 3 and sys.version_info[1] >= 9):
    print("This script requires Python 3.9 or newer to run. Exiting.")
    quit()

ALL_FILMS = {}


class LetterboxdFilm:
    def __init__(self,
                 film_id,
                 session=None,
                 ratings=[],
                 reviews=[],
                 liked=set()):

        self.id = film_id
        self.session = session
        # get title here
        self.title = None
        # also get film year
        self.year = None
        self.watched_by = set()

        def add_user(self, user):
            if user not in self.watched_by:
                self.watched_by.add(user)
                self.update(self, user)

        def update(self, username):
            FILM_PAGE = f"https://letterboxd.com/{username}/film/the-love-witch/"
            pass


class LetterboxdProfile:
    def __init__(self,
                 username,
                 session):

        self.username = username
        self.session = session

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

    def __iter__(self):
        return iter(self.film_data)

    def __contains__(self, item):
        return item in self.film_data

    def __bool__(self):
        return len(self.film_data) > 0

    def get_page(self, pagenum):
        LIST_PAGE = "https://letterboxd.com/{}/films/page/{}"
        return await self.session.get(LIST_PAGE.format(self.username, pagenum)).text()
