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
import asyncio

if sys.platform[:4] in ("linux", "darwin"):
    try:
        import uvloop

        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except ImportError:
        print("uvloop library not found. It could provide some speedups.")
        pass

from aiohttp import ClientSession, ClientResponseError
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
        self.username: str = username
        self.link = f"https://letterboxd.com/{self.username}"
        self.session = session
        self.films = dict()

    def __repr__(self):
        return f"LetterboxdProfile({self.username!r})"

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
        return self.common(self, *others)

    @staticmethod
    async def exists(username, session):
        try:
            await session.get(
                f"https://letterboxd.com/{username}", raise_for_status=True
            )
            print(f"Found user {username}")
            return username
        except ClientResponseError:
            print(f"User {username} not found.")

    @staticmethod
    def common(*profiles) -> set:
        return set.intersection(*(set(prof.films.keys()) for prof in profiles))

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

    def find_films(self, page) -> dict:
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

    async def get_all_pages(self) -> str:
        page1 = await self.get_user_page(1)
        # TODO: make a fix for when there are only 2 pages
        last_page = int(page1.xpath("//li[@class='paginate-page'][last()]/a/text()")[0])
        pages = [page1] + [
            (await self.get_user_page(page)) for page in range(2, last_page + 1)
        ]
        print(f"Downloaded {last_page} pages for {self.username}")
        return pages

    async def get_user_page(self, pagenum):
        LIST_PAGE = "https://letterboxd.com/{}/films/page/{}"
        async with self.session.get(LIST_PAGE.format(self.username, pagenum)) as resp:
            page = await resp.text()
        return html.document_fromstring(page)

    async def update(self) -> None:
        self.films: dict = {
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
        print(f"Populated {self.username}'s profile with {len(self)} films")


def write_output(profiles, outfile):
    # markdown table format is like so
    # | Tables   |      Are      |  Cool |
    # |----------|:-------------:|------:|
    # | col 1 is |  left-aligned | $1600 |
    # | col 2 is |    centered   |   $12 |
    # | col 3 is | right-aligned |    $1 |

    common_films: set = LetterboxdProfile.common(*profiles)

    def newline(num_lines, file_name):
        lines: str = "\n" * num_lines
        file_name.write(lines)

    # flexible column width
    # some magic numbers here, tune according to taste
    FILM_PADDING: int = 5
    film_width: int = FILM_PADDING + max(
        len(profiles[0][film_id]["title"]) for film_id in common_films
    )

    USER_PADDING: int = 5 + 9  # the 9 accounts for the word "rating" itself
    user_width: int = {
        user.username: USER_PADDING + (max(len(f"{user.username}"), 7))
        for user in profiles
    }

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(
            f"## {len(common_films)} common films for {', '.join(_.username for _ in profiles)}.\n\n"
        )

        f.write("|" + "Film title".center(film_width - 2) + "|")
        for user in profiles:
            f.write(f"{user.username}'s rating".center(user_width[user.username]) + "|")
        f.write("\n")

        f.write("|" + "-" * (film_width - 2) + "|")
        for user in profiles:
            f.write(":" + "-" * (user_width[user.username] - 2) + ":|")
        f.write("\n")

        # TODO: alphabetic (or other) ordering for the films
        for film_id in common_films:
            f.write(
                "|" + profiles[0].films[film_id]["title"].ljust(film_width - 2) + "|"
            )
            for user in profiles:
                if user.films[film_id]["rating"]:
                    rating = user.films[film_id]["rating"][0]
                else:
                    rating = "n/r"

                if user.films[film_id]["liked"]:
                    f.write(f"{rating} (liked)".center(user_width[user.username] - 1) + "|")
                else:
                    f.write(rating.center(user_width[user.username] - 1) + "|")
            f.write("\n")
    print(f"Wrote output to {outfile}")


async def main():
    async with ClientSession(raise_for_status=True) as client:
        users = [await LetterboxdProfile.exists(user, client) for user in sys.argv[1:]]
        profiles = [LetterboxdProfile(user, client) for user in set(users)]
        tasks = (profile.update() for profile in profiles)
        await asyncio.gather(*tasks)

    write_output(profiles, f"{'_'.join(users)}.md")


if __name__ == "__main__":
    asyncio.run(main())
