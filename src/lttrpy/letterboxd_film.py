"""Letterboxd film info container and fetcher class"""

import contextlib
import re

# from dataclasses import dataclass
from typing import Self

from aiohttp import ClientSession
from lxml import html
from lxml.html import HtmlElement

# from typing_extensions import Self

# TODO: implement getter method for year, etc


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
        lazy: bool = False,
        user: str = "",
    ) -> None:
        self.film_id: str = film_id  # in Letterboxd's own "string" format
        self.session: ClientSession = session
        self.lazy: bool = lazy  # won't update data if lazy
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

    async def get_page(self, refresh: bool = False) -> HtmlElement:
        if self.html_page:
            return self.html_page

        page_url: str = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(page_url.format(self.user, self.film_id)) as resp:
            page: str = await resp.text()
        tree: HtmlElement = html.document_fromstring(page)
        return tree

    async def get_title(self, refresh: bool = False) -> str:
        if self.title and not refresh:
            return self.title

        xpath: str = "//meta[@property='og:title'][1]"
        title: str = (await self.get_page()).xpath(xpath)[0].get("content")[:-1]
        return title

    async def get_year(self, refresh: bool = False) -> int:
        if self.year and not refresh:
            return self.year

        xpath: str = "//meta[@property='og:title'][1]"
        year: str = (await self.get_page()).xpath(xpath)[0].get("content")[-5:-1]
        return int(year)

    async def get_review(
        self,
        refresh: bool = False,
    ) -> str:
        if self.review and not refresh:
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

    async def get_rating(self, refresh: bool = False) -> str:
        if self.rating and not refresh:
            return self.rating

        rating_xpath: str = "//meta[@name='twitter:data2'][1]"
        rating: list[HtmlElement] = (await self.get_page()).xpath(rating_xpath)
        if rating:
            str_rating: str = rating[0].get("content")[0]
        else:
            str_rating: str = ""

        return str_rating

    @classmethod
    def star2float(cls, rating: str) -> float:
        return sum([rating.count("★"), rating.count("½") / 2])

    async def get_activity(self) -> tuple[str, bool]:
        section_xpath: str = "/html/body/div[1]/div/div/section/div[2]/div/section"
        # year_xpath: str = "/html/body/div[1]/div/div/section/header/div/h1/small/a"

        async with (
            self.session as session,
            session.get(
                f"https://letterboxd.com/{self.user}/film/{self.film_id}/activity/",
            ) as resp,
        ):
            page = await resp.text()
            # match a sequence of stars NOT followed by "review"
            # because that'd be an entry for a liked comment
            rated = re.compile(r"([★½])+(?!.*review)")
            # ditto
            liked = re.compile(r"(liked)+(?!.*review)")

            tree = html.fromstring(page)
            sections = tree.xpath(section_xpath)
            for entry in (_.text_content() for _ in sections[:-1]):
                # print(entry)
                with contextlib.suppress(AttributeError):
                    if rating := rated.search(entry):
                        user_rating = rating.group()
                    if liked.search(entry):
                        is_liked: bool = True

            return user_rating, is_liked

    async def populate(
        self,
        refresh: bool = False,
        unlazy: bool = False,
    ) -> None:
        self.title = await self.get_title(refresh=refresh)
        self.rating = await self.get_rating(refresh=refresh)
        if (not self.lazy) or unlazy:
            self.review = await self.get_review(refresh=refresh)
            self.year = await self.get_year(refresh=refresh)

    @classmethod
    async def initialise(cls, user: str, unlazy: bool, **kwargs) -> Self:
        film_object: Self = cls(**kwargs)
        await film_object.populate(user, unlazy)
        return film_object
