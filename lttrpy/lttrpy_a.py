# !/usr/bin/env python

# MIT License
# Copyright (c) 2024 Said Sattarov
# See https://mit-license.org/ for the full text of the license

# Inspired by Sena Bayram's script

# TODO: optional: different output formats, common ratings, film year, output sorting
# film year's gonna be tricky since the users' film galleries don't contain it and often neither do
# their review pages, meaning we'd have to parse the film's own page
# TODO: optional: display only liked
# TODO: optional: display only common ratings
# TODO: optional: display reviews
# TODO: optional: interactive mode
# TODO: more verbosity during stages
# TODO: a prettier table? (screw that I'm not importing another damn dependency into this)

# probably should rewrite this so that profiles contain instances of the film class
# but who's got the time


import sys


# import trio as asyn
import asyncio as asyn

# h2 needs to be present because we're making extensive use of it here
# from httpx import AsyncClient as ClientSession
from aiohttp import ClientSession as ClientSession
from lxml import html


assert (
    sys.version_info[0] >= 3 and sys.version_info[1] >= 9
), "This script requires Python 3.9 or newer to run. Exiting."


class LetterboxdFilm:
    # will work on this later
    def __init__(self, film_id, session=None, ratings=[], reviews=[], liked=set()):

        self.string_id = film_id
        self.film_page = f"https://letterboxd.com/film/{self.string_id}"
        self.tvdb_id = None
        # it's more of a client if we're using httpx but whatever
        self.session = session
        # get title here
        self.title = None
        # also get film year
        self.year = None
        self.watched_by = set()
        self.ratings = ratings
        self.reviews = reviews

    def __repr__(self):
        return f"Film({self.title!r})"

    def __str__(self):
        return f"{self.title} ({self.year})"

    def add_user(self, user):
        if user not in self.watched_by:
            self.watched_by.add(user)
            self.update(self, user)
            print(f"{self.title} ({self.year}) watched by {user}")

    async def get_review(self, username):
        REVIEW_PAGE = "https://letterboxd.com/{}/film/{}/"
        page = (
            await self.session.get(REVIEW_PAGE.format(username, self.string_id))
        ).text
        tree = html.document_fromstring(page)
        spoiler = (
            True
            if (
                "This review may contain spoilers"
                in tree.xpath("//meta[@name='description'][1]")[0].get("content")
            )
            else None
        )
        review = "\n".join(
            tree.xpath(
                "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
            )
        )
        return spoiler, review

    def update(self, username):
        pass


class LetterboxdProfile:
    def __init__(self, username, session):
        self.username = username
        self.link = f"https://letterboxd.com/{self.username}"
        self.session = session
        self.films = dict()

    def __repr__(self):
        return f"Profile({self.username!r})"

    def __getitem__(self, key):
        if type(key) is str:
            return self.films[key]
        elif type(key) in (slice, int):
            return tuple(self.films.values())[key]

    def __iter__(self):
        return iter(self.films)

    def __contains__(self, item):
        return item in self.films

    def __len__(self):
        return len(self.films)

    def __add__(self, *others):
        return self.commons(self, *others)

    @classmethod
    def commons(*profiles):
        return set.intersection(*profiles)

    async def get_review(self, film):
        REVIEW_PAGE = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(REVIEW_PAGE.format(self.username, film)) as resp:
            page = await resp.text()
        tree = html.document_fromstring(page)
        spoiler = (
            True
            if (
                "This review may contain spoilers"
                in tree.xpath("//meta[@name='description'][1]")[0].get("content")
            )
            else False
        )
        review = "\n".join(
            tree.xpath(
                "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
            )
        )
        return spoiler, review

    def find_films(self, page):
        films = {
            node.xpath("./div")[0].get("data-film-slug"): {
                "html": node,
                "title": node.xpath("./div[1]/img")[0].get("alt"),
                "rating": node.xpath("./p/span[1]/text()"),
                "liked": True if node.xpath("./p/span[2]") else False,
                "reviewed": True if node.xpath("./p/a") else False,
            }
            for node in page.xpath("//ul/li[@class='poster-container']")
        }
        return films

    async def get_all_pages(self):
        page1 = await self.get_user_page(1)
        last_page = int(page1.xpath("//li[@class='paginate-page'][3]/a/text()")[0])
        return [page1] + [
            (await self.get_user_page(page)) for page in range(2, last_page + 1)
        ]

    async def get_user_page(self, pagenum):
        LIST_PAGE = "https://letterboxd.com/{}/films/page/{}"
        async with self.session.get(LIST_PAGE.format(self.username, pagenum)) as resp:
            page = await resp.text()
        return html.document_fromstring(page)

    async def update(self):
        self.films = {
            film: data
            for page in await self.get_all_pages()
            for film, data in self.find_films(page).items()
        }
        # self.reviews = {
        #     film: review
        #     for film in self.films
        #     for _, review in await self.get_review(film)
        #     if film["reviewed"]
        # }


def format_output(profiles, outfile):
    """
    The fuck is going on here :'(
    """
    common_ids = profiles[0].overlap(*profiles)

    # flexible column width
    # some magic numbers here, tune according to taste
    FILM_PADDING = 5
    col_w = {
        "film": (
            FILM_PADDING
            + max(len(profiles[0].get(film_id)['title']) for film_id in common_ids)
        )
    }

    USER_PADDING = 5 + 9  # the 9 accounts for the word "rating" itself
    for profile in profiles:
        user = profile.username
        col_w.update(
            {
                user: USER_PADDING
                + (max(len(f"{user}"),
                       len("(liked)")))
            }
        )

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(f"There are {len(common_ids)} common films for those users.\n")
        f.write("n/r stands for 'no rating'\n\n")

        f.write("Film name".ljust(col_w["film"]))

        for user in profiles:
            f.write(f"{user.username}'s rating".center(col_w[user.username]))
        f.write("\n\n")

        # TODO: alphabetic (or other) ordering for the films
        for film_id in common_ids:
            f.write(profiles[0].film_data[film_id][0].ljust(col_w["film"]))
            for user in profiles:
                if user.film_data[film_id][2]:
                    f.write(
                        f"{user.film_data[film_id][1]} (liked)".center(
                            col_w[user.username]
                        )
                    )
                else:
                    f.write(
                        f"{user.film_data[film_id][1]}".center(col_w[user.username])
                    )
            f.write("\n")


async def main():
    # async with ClientSession(http2=True, follow_redirects=True) as client:
    async with ClientSession() as client:
        users = sys.argv[1:]
        print(f"Users: {users}")
        profiles = [LetterboxdProfile(user, client) for user in set(users)]
        for profile in profiles:
            await profile.update()
            print(f"{profile.username}: {len(profile)} films")


if __name__ == "__main__":
    asyn.run(main())
