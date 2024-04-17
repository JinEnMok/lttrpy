"""Letterboxd user profile data container and fetcher class"""

from typing import Self, Iterator

from aiohttp import ClientResponseError, ClientSession
from lxml import html

from .LetterboxdFilm import LetterboxdFilm

import asyncio


class LetterboxdProfile:
    def __init__(self, username: str, session) -> None:
        self.username: str = username
        self.link: str = f"https://letterboxd.com/{self.username}"
        self.session: ClientSession = session
        self.films: dict[str, LetterboxdFilm] = dict()

    def __repr__(self) -> str:
        return f"LetterboxdProfile({self.username!r}, {self.session!r})"

    def __getitem__(self, key) -> tuple[LetterboxdFilm, ...] | LetterboxdFilm:
        if isinstance(key, str):
            return self.films[key]
        elif isinstance(key, (int, slice)):
            return tuple(self.films.values())[key]

    def __iter__(self) -> Iterator[LetterboxdFilm]:
        yield from self.films.values()

    def __contains__(self, film: str) -> bool:
        return film in self.films

    def __len__(self) -> int:
        return len(self.films)

    def __add__(self, *others) -> set[str]:
        return self.common(self, *others)

    async def get_user_page(self, pagenum: int) -> html.HtmlElement:
        url: str = "https://letterboxd.com/{}/films/page/{}"
        async with self.session.get(url.format(self.username, pagenum)) as resp:
            page: str = await resp.text()
        return html.document_fromstring(page)

    async def get_all_pages(self) -> list[html.HtmlElement]:
        page1: html.HtmlElement = await self.get_user_page(1)
        last_page: int = int(
            page1.xpath("//li[@class='paginate-page'][last()]/a/text()")[0]
        )
        pages: list[html.HtmlElement] = [page1] + [
            (await self.get_user_page(page)) for page in range(2, last_page + 1)
        ]
        return pages

    def find_films(self, page: html.HtmlElement) -> dict[str, LetterboxdFilm]:
        films: dict[str, LetterboxdFilm] = dict(
            [
                (
                    film_id := poster.xpath("./div")[0].get("data-film-slug"),
                    LetterboxdFilm(
                        film_id=film_id,
                        session=self.session,
                        title=poster.xpath("./div[1]/img")[0].get("alt"),
                        rating=(
                            rating[0]
                            if (rating := poster.xpath("./p/span[1]/text()"))
                            else ""
                        ),
                        liked=(True if poster.xpath("./p/span[2]") else False),
                        reviewed=(True if poster.xpath("./p/a") else False),
                    ),
                )
                for poster in page.xpath("//ul/li[@class='poster-container']")
            ]
        )
        return films

    async def populate_films(
        self, page: html.HtmlElement, unlazy: bool
    ) -> dict[str, LetterboxdFilm]:
        initialise_films: tuple = tuple(
            LetterboxdFilm.initialise(
                user=self.username,
                unlazy=unlazy,
                film_id=poster.xpath("./div")[0].get("data-film-slug"),
                session=self.session,
                title=poster.xpath("./div[1]/img")[0].get("alt"),
                rating=(
                    rating[0] if (rating := poster.xpath("./p/span[1]/text()")) else ""
                ),
                liked=(True if poster.xpath("./p/span[2]") else False),
                reviewed=(True if poster.xpath("./p/a") else False),
            )
            for poster in page.xpath("//ul/li[@class='poster-container']")
        )
        film_objs = await asyncio.gather(*initialise_films)
        return dict((film.film_id, film) for film in film_objs)

    async def populate_profile(self) -> None:
        """
        Here we're simply unpacking all the pages' info
        """
        self.films: dict[str, LetterboxdFilm] = {
            film_id: film_data
            for page in await self.get_all_pages()
            # for film_id, film_data in self.find_films(page).items()
            for film_id, film_data in (
                await self.populate_films(page, unlazy=True)
            ).items()
        }

    @classmethod
    async def exists(cls, username: str, session: ClientSession) -> bool:
        try:
            await session.get(
                f"https://letterboxd.com/{username}", raise_for_status=True
            )
            return True
        except ClientResponseError:
            return False

    @classmethod
    def common(cls, *profiles) -> set[str]:
        return set.intersection(*(set(prof.films.keys()) for prof in profiles))

    @classmethod
    def diff(cls, *profiles) -> set[str]:
        return set.difference(*(set(prof.films.keys()) for prof in profiles))

    @classmethod
    async def initialise(cls, username: str, session: ClientSession) -> Self:
        """
        If user exists, create, populate, and return its profile object.

        Args:
            username: username
            session: aiohttp session

        Returns:
            LetterboxProfile(username) object
        """
        if await cls.exists(username, session):
            profile = cls(username, session)
            print(f"Found user {username}")
            await profile.populate_profile()
            return profile
        else:
            print(f"Could not initialise {username}")
