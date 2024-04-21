"""Letterboxd user profile data container and fetcher class"""

import asyncio
from typing import TYPE_CHECKING

from aiohttp import ClientResponseError
from lxml import html

from lttrpy.letterboxd_film import LetterboxdFilm

if TYPE_CHECKING:
    from typing import Iterator, Self

    from aiohttp import ClientSession
    from lxml.html import HtmlElement


class LetterboxdProfile:
    def __init__(self, username: str, session: ClientSession) -> None:
        self.username: str = username
        self.link: str = f"https://letterboxd.com/{self.username}"
        self.session: ClientSession = session
        self.films: dict[str, LetterboxdFilm] = {}

    def __repr__(self) -> str:
        return f"LetterboxdProfile({self.username!r}, {self.session!r})"

    def __getitem__(self, key: str | int | slice) -> tuple[LetterboxdFilm, ...] | LetterboxdFilm:
        if isinstance(key, str):
            return self.films[key]
        elif isinstance(key, (int, slice)):  # noqa: RET505
            return tuple(self.films.values())[key]
        else:
            raise KeyError
        return None

    def __iter__(self) -> Iterator[LetterboxdFilm]:
        yield from self.films.values()

    def __contains__(self, film: str) -> bool:
        return film in self.films

    def __len__(self) -> int:
        return len(self.films)

    async def get_user_page(self, pagenum: int) -> HtmlElement:
        url: str = "https://letterboxd.com/{}/films/page/{}"
        async with self.session.get(url.format(self.username, pagenum)) as resp:
            page: str = await resp.text()
        return html.document_fromstring(page)

    async def get_all_pages(self) -> list[HtmlElement]:
        page1: HtmlElement = await self.get_user_page(1)
        last_page: int = int(page1.xpath("//li[@class='paginate-page'][last()]/a/text()")[0])
        pages: list[HtmlElement] = [page1] + [
            (await self.get_user_page(page)) for page in range(2, last_page + 1)
        ]
        return pages

    def find_films(self, page: HtmlElement) -> dict[str, LetterboxdFilm]:
        films: dict[str, LetterboxdFilm] = {
            (film_id := poster.xpath("./div")[0].get("data-film-slug")): LetterboxdFilm(
                film_id=film_id,
                session=self.session,
                title=poster.xpath("./div[1]/img")[0].get("alt"),
                rating=(rating[0] if (rating := poster.xpath("./p/span[1]/text()")) else ""),
                liked=(bool(poster.xpath("./p/span[2]"))),
                reviewed=(bool(poster.xpath("./p/a"))),
            )
            for poster in page.xpath("//ul/li[@class='poster-container']")
        }
        return films

    async def populate_films(self, page: HtmlElement, unlazy: bool) -> dict[str, LetterboxdFilm]:
        initialise_films: tuple = tuple(
            LetterboxdFilm.initialise(
                user=self.username,
                unlazy=unlazy,
                film_id=poster.xpath("./div")[0].get("data-film-slug"),
                session=self.session,
                title=poster.xpath("./div[1]/img")[0].get("alt"),
                rating=(rating[0] if (rating := poster.xpath("./p/span[1]/text()")) else ""),
                liked=(bool(poster.xpath("./p/span[2]"))),
                reviewed=(bool(poster.xpath("./p/a"))),
            )
            for poster in page.xpath("//ul/li[@class='poster-container']")
        )
        film_objs = await asyncio.gather(*initialise_films)
        return {film.film_id: film for film in film_objs}

    async def populate_profile(self) -> None:
        """
        Here we're simply unpacking all the pages' info
        """
        self.films: dict[str, LetterboxdFilm] = {
            film_id: film_data
            for page in await self.get_all_pages()
            # for film_id, film_data in self.find_films(page).items()
            for film_id, film_data in (await self.populate_films(page, unlazy=True)).items()
        }

    @classmethod
    async def exists(cls, username: str, session: ClientSession) -> bool:
        try:
            await session.get(f"https://letterboxd.com/{username}", raise_for_status=True)
            return True
        except ClientResponseError:
            return False

    @classmethod
    def common(cls, *profiles: Self) -> set[str]:
        return set.intersection(*(set(prof.films.keys()) for prof in profiles))

    @classmethod
    def diff(cls, *profiles: Self) -> set[str]:
        return set.difference(*(set(prof.films.keys()) for prof in profiles))

    @classmethod
    async def initialise(cls, username: str, session: ClientSession) -> Self | None:
        """
        If user exists, create, populate, and return its profile object.

        Args:
            username: username
            session: aiohttp session

        Returns:
            LetterboxProfile(username) object
        """
        if not (await cls.exists(username, session)):
            print(f"Could not initialise {username}")
            return None

        profile: Self = cls(username, session)
        print(f"Found user {username}")
        await profile.populate_profile()
        return profile
