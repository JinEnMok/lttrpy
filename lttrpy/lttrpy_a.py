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

# h2 needs to be present because we're making extensive use of it here
from httpx import AsyncClient
from lxml import html
import sys


assert (
    sys.version_info[0] >= 3 and sys.version_info[1] >= 9
), "This script requires Python 3.9 or newer to run. Exiting."


async def get_page(session, url):
    """
    General-purpose async page-downloading function
    """
    async with session.get(url) as page:
        return await page.text()


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
        self.films_watched = dict()

    def __repr__(self):
        return f"Profile({self.username!r})"

    def __getitem__(self, key):
        if type(key) is str:
            return self.films_watched[key]
        elif type(key) in (slice, int):
            return tuple(self.films_watched.values())[key]

    def __iter__(self):
        return iter(self.films_watched)

    def __contains__(self, item):
        return item in self.films_watched

    async def get_review(session, username, film):
        REVIEW_PAGE = "https://letterboxd.com/{}/film/{}/"
        page = (await session.get(REVIEW_PAGE.format(username, film))).text
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

    def find_films(page):
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

    async def get_all_pages(session, username):
        page1 = await get_page(session, username, 1)
        last_page = int(page1.xpath("//li[@class='paginate-page'][3]/a/text()")[0])
        return [page1] + [
            (await get_page(session, username, page))
            for page in range(2, last_page + 1)
        ]

    async def get_page(session, username, pagenum):
        LIST_PAGE = "https://letterboxd.com/{}/films/page/{}"
        page = (await session.get(LIST_PAGE.format(username, pagenum))).text
        return html.document_fromstring(page)


async def main():
    async with AsyncClient(http2=True, follow_redirects=True) as client:
        ALL_FILMS = {}
        users = (user1, user2)
        profiles = [LetterboxdProfile(user, client) for user in users]


if __name__ == "__main__":
    trio.run(main)
