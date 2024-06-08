"""Letterboxd film info container and fetcher class"""

from typing import Self

from aiohttp import ClientSession
from lxml import html
from lxml.html import HtmlElement

from .utils import retry


class LetterboxdFilm:
    def __init__(
        self,
        film_id: str,
        session: ClientSession,
        title: str = "",
        year: int = 0,
        rating: str = "",
        liked: bool = False,
        reviewed: bool = False,
        user: str = "",
    ) -> None:
        self.film_id: str = film_id  # in Letterboxd's own "string" format
        self.session: ClientSession = session
        self.title: str = title  # human-readable title
        self.year: int = year  # film year
        self.rating: str = rating  # rating, in "stars"
        self.rating_numeric: float = self.star2float(self.rating)  # numerc rating
        self.liked: bool = liked
        self.reviewed: bool = reviewed
        self.review_spoiler: bool = False
        self.review: str = ""
        self.html_page: HtmlElement | None = None
        self.user: str = ""

    def __str__(self) -> str:
        return f"{self.title} ({self.year})"

    @retry()
    async def get_page(self) -> HtmlElement:
        if self.html_page:
            return self.html_page

        page_url: str = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(page_url.format(self.user, self.film_id)) as resp:
            page: str = await resp.text()
        tree: HtmlElement = html.document_fromstring(page)
        return tree

    async def get_year(self) -> int:
        if self.year:
            return self.year

        xpath: str = "//meta[@property='og:title'][1]"
        year: str = (await self.get_page()).xpath(xpath)[0].get("content")[-5:-1]
        return int(year)

    async def get_review(self) -> str:
        if self.review:
            return self.review
        elif not self.reviewed:  # noqa: RET505
            return ""

        try:  # TODO: fix this hack
            spoiler: bool = "This review may contain spoilers" in (await self.get_page()).xpath(
                "//meta[@name='description'][1]",
            )[0].get("content")
        except IndexError:
            return ""
        review_xpath: str = "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
        review_elem = (await self.get_page()).xpath(review_xpath)

        if spoiler:
            self.review_spoiler = True
            review: str = "\n".join(review_elem[1:])
        else:
            review: str = "\n".join(review_elem)

        return review

    @classmethod
    def star2float(cls, rating: str) -> float:
        return sum([rating.count("★"), rating.count("½") / 2])

    async def populate(self) -> None:
        # self.year = await self.get_year()
        if self.reviewed:
            self.review = await self.get_review()

    @classmethod
    async def initialise(cls, **kwargs) -> Self:
        film_object: Self = cls(**kwargs)
        await film_object.populate()
        return film_object
