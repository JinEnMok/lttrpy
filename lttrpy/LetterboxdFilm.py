from lxml import html
from typing import Optional


class LetterboxdFilm:
    def __init__(
        self,
        film_id: str,
        session,
        title: str = '',
        year: int = 0,
        rating: str = '',
        liked: bool = False,
        review: Optional[tuple[bool, str]] = None,
    ) -> None:
        self.film_id: str = film_id
        self.session = session
        self.title: str = title
        self.year: int = year
        self.rating: str = rating
        self.liked: bool = liked
        self.review: Optional[tuple[bool, str]] = review
        self.main_page: Optional[html.HtmlElement] = None
        self.user_page: Optional[html.HtmlElement] = None

    def __repr__(self):
        return f"Film({self.title!r}, {self.film_id!r}, {self.session!r})"

    def __str__(self):
        return f"{self.title} ({self.year})"

    async def get_page(self, user='', refresh=False) -> html.HtmlElement:
        url = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(url.format(user, self.film_id)) as resp:
            page = await resp.text()
        tree: html.HtmlElement = html.document_fromstring(page)
        return tree

    async def get_title(self, user='', refresh=False) -> str:
        if self.title and not refresh:
            return self.title
        if not self.main_page:
            self.main_page = await self.get_page(user=user)
        xpath = "//meta[@property='og:title'][1]"
        title = self.main_page.xpath(xpath)[0].get('content')[:-1]
        return title

    async def get_year(self, refresh=False) -> int:
        if self.year and not refresh:
            return self.year
        if not self.main_page:
            self.main_page = await self.get_page()
        xpath = "//meta[@property='og:title'][1]"
        year: str = self.main_page.xpath(xpath)[0].get("content")[-5:-1]
        return int(year)

    async def get_review(self, user, refresh=False) -> tuple[bool, str]:
        if self.review and not refresh:
            return self.review
        if not self.user_page:
            self.user_page = await self.get_page(user=user)
        xpath = "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
        tree = await self.get_page(user=user)
        if "This review may contain spoilers" in self.user_page.xpath(
            "//meta[@name='description'][1]"
        )[0].get("content"):
            spoiler = True
            review = "\n".join(tree.xpath(xpath)[1:])
        else:
            spoiler = False
            review = "\n".join(tree.xpath(xpath))
        return spoiler, review

    async def get_rating(self, user, refresh=False) -> str:
        if self.rating and not refresh:
            return self.rating
        if not self.user_page:
            self.user_page = await self.get_page(user=user)
        xpath = "//meta[@name='twitter:data2'][1]"
        rating: str | list = self.user_page.xpath(xpath)
        if rating:
            return rating[0].get('content')
        else:
            return 'n/r'

    async def populate(self, user: str, refresh=False) -> None:
        self.title = await self.get_title()
        self.review = await self.get_review(user)
        self.year = await self.get_year()
        self.rating = await self.get_rating(user)

    @staticmethod
    async def initialise(film, user, session):
        film_obj = LetterboxdFilm(film, session)
        await film_obj.populate(user)
        return film_obj
