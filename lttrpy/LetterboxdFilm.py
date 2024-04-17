"""Letterboxd film info container and fetcher class"""

import re
from typing import Self
from lxml import html
from aiohttp import ClientSession


class LetterboxdFilm:
    REVIEWED_RE: re.Pattern = re.compile(r"", flags=(re.IGNORECASE | re.VERBOSE))

    section_xpath = "/html/body/div[1]/div/div/section/div[2]/div/section"

    # async with ClientSession() as session:
    # ...:     async with session.get("https://letterboxd.com/kurstboy/film/everything-everywhere-all-at-once/activity
    # ...: /") as resp:
    # ...:         karst_page = await resp.text()
    # ...: 
    # ...: karst_tree = html.fromstring(karst_page)
    # ...: karst_sections = karst_tree.xpath(section_xpath)
    # ...: for section in karst_sections[:-1]:
    # ...:     print(section.text_content().split())


    ratings_dict: dict[str, int] = {
        "½": 1,
        "★": 2,
        "★½": 3,
        "★★": 4,
        "★★½": 5,
        "★★★": 6,
        "★★★½": 7,
        "★★★★": 8,
        "★★★★½": 9,
        "★★★★★": 10,
    }

    def __init__(
        self,
        film_id: str,
        session: ClientSession,
        title: str = "",
        year: int = 0,
        rating: str = "",
        liked: bool = False,
        reviewed: bool = False,
        lazy: bool = False,
    ) -> None:
        self.film_id: str = film_id
        self.session: ClientSession = session
        self.lazy: bool = lazy
        self.title: str = title
        self.year: int = year
        self.rating: str = rating
        self.rating_int: int = self.ratings_dict.get(self.rating, 0)
        self.liked: bool = liked
        self.reviewed: bool = reviewed
        self.review: dict[str, bool | str] = {"spoiler": False, "text": ""}
        self.main_page: html.HtmlElement | None = None
        self.user_page: html.HtmlElement | None = None

    def __repr__(self) -> str:
        return f"Film({self.title!r}, {self.film_id!r}, {self.session!r})"

    def __str__(self) -> str:
        return f"{self.title} ({self.year})"

    async def get_page(self, user: str = "", refresh: bool = False) -> html.HtmlElement:
        url: str = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(url.format(user, self.film_id)) as resp:
            page: str = await resp.text()
        tree: html.HtmlElement = html.document_fromstring(page)
        return tree

    async def get_title(self, user: str = "", refresh: bool = False) -> str:
        if self.title and not refresh:
            return self.title
        if self.main_page is None:
            self.main_page: html.HtmlElement = await self.get_page(user=user)

        xpath: str = "//meta[@property='og:title'][1]"
        title: str = self.main_page.xpath(xpath)[0].get("content")[:-1]
        return title

    async def get_year(self, refresh: bool = False) -> int:
        if self.year and not refresh:
            return self.year
        if self.main_page is None:
            self.main_page: html.HtmlElement = await self.get_page()

        xpath: str = "//meta[@property='og:title'][1]"
        year: str = self.main_page.xpath(xpath)[0].get("content")[-5:-1]
        return int(year)

    async def get_review(
        self, user: str = "", refresh: bool = False
    ) -> dict[str, bool | str]:
        if self.review and not refresh:
            return self.review
        elif not self.reviewed:
            return {"spoiler": False, "text": ""}

        if not self.user_page:
            self.user_page: html.HtmlElement = await self.get_page(user=user)

        review_xpath: str = (
            "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
        )
        spoiler: bool = "This review may contain spoilers" in self.user_page.xpath(
            "//meta[@name='description'][1]"
        )[0].get("content")

        if spoiler:
            review: str = "\n".join(self.user_page.xpath(review_xpath)[1:])
        else:
            review: str = "\n".join(self.user_page.xpath(review_xpath))

        return {"spoiler": spoiler, "text": review}

    async def get_rating(self, user: str = "", refresh: bool = False) -> str:
        if self.rating and not refresh:
            return self.rating
        if not self.user_page:
            self.user_page: html.HtmlElement = await self.get_page(user=user)

        rating_xpath: str = "//meta[@name='twitter:data2'][1]"
        rating: list = self.user_page.xpath(rating_xpath)
        if rating:
            return rating[0].get("content")[0]
        else:
            return ""

    async def populate(
        self, user: str, refresh: bool = False, unlazy: bool = False
    ) -> None:
        self.title = await self.get_title(refresh=refresh)
        self.rating = await self.get_rating(user, refresh=refresh)
        if (not self.lazy) or unlazy:
            self.review = await self.get_review(user, refresh=refresh)
            self.year = await self.get_year(refresh=refresh)

    @classmethod
    async def initialise(cls, user: str, unlazy: bool, **kwargs) -> Self:
        film_object: LetterboxdFilm = LetterboxdFilm(**kwargs)
        await film_object.populate(user, unlazy)
        return film_object
