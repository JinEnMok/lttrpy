from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from lxml import html
    from aiohttp import ClientSession

# https://stackoverflow.com/questions/795190/how-to-perform-common-post-initialization-tasks-in-inherited-classes

class LetterboxdFilm:
    def __init__(
        self,
        film_id: str,
        session: "ClientSession",
        title: str = "",
        year: int = 0,
        rating: str = "",
        liked: bool = False,
        reviewed: bool = False,
        lazy: bool = False,
    ) -> None:
        self.film_id: str = film_id
        self.session: "ClientSession" = session
        self.lazy: bool = lazy
        self.title: str = title
        self.year: int = year
        self.rating: str = rating
        self.liked: bool = liked
        self.reviewed: bool = reviewed
        self.review: dict[str, bool | str] = {"spoiler": False, "text": ""}
        self.main_page: "html.HtmlElement" | None = None
        self.user_page: "html.HtmlElement" | None = None

    def __repr__(self) -> str:
        return f"Film({self.title!r}, {self.film_id!r}, {self.session!r})"

    def __str__(self) -> str:
        return f"{self.title} ({self.year})"

    async def get_page(self, user="", refresh=False) -> "html.HtmlElement":
        url: str = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(url.format(user, self.film_id)) as resp:
            page: str = await resp.text()
        tree: "html.HtmlElement" = html.document_fromstring(page)
        return tree

    async def get_title(self, user="", refresh=False) -> str:
        if self.title and not refresh:
            return self.title
        if not self.main_page:
            self.main_page: "html.HtmlElement" = await self.get_page(user=user)
        xpath: str = "//meta[@property='og:title'][1]"
        title: str = self.main_page.xpath(xpath)[0].get("content")[:-1]
        return title

    async def get_year(self, refresh=False) -> int:
        if self.year and not refresh:
            return self.year
        if not self.main_page:
            self.main_page: "html.HtmlElement" = await self.get_page()
        xpath: str = "//meta[@property='og:title'][1]"
        year: str = self.main_page.xpath(xpath)[0].get("content")[-5:-1]
        return int(year)

    async def get_review(self, user, refresh=False) -> dict[str, bool | str]:
        if self.review and not refresh:
            return self.review
        elif not self.reviewed:
            return {"spoiler": False, "text": ""}
        if not self.user_page:
            self.user_page: "html.HtmlElement" = await self.get_page(user=user)
        xpath: str = (
            "/html/body/div[1]/div/div/" "section/section/div[1]/div/div/p/text()"
        )
        if "This review may contain spoilers" in self.user_page.xpath(
            "//meta[@name='description'][1]"
        )[0].get("content"):
            spoiler: bool = True
            review: str = "\n".join(self.user_page.xpath(xpath)[1:])
        else:
            spoiler: bool = False
            review: str = "\n".join(self.user_page.xpath(xpath))
        return {"spoiler": spoiler, "text": review}

    async def get_rating(self, user, refresh=False) -> str:
        if self.rating and not refresh:
            return self.rating
        if not self.user_page:
            self.user_page: "html.HtmlElement" = await self.get_page(user=user)
        xpath: str = "//meta[@name='twitter:data2'][1]"
        rating: list = self.user_page.xpath(xpath)
        if rating:
            return rating[0].get("content")[0]
        else:
            return ""

    async def populate(self, user: str, refresh: bool = False) -> None:
        self.title = await self.get_title(refresh=refresh)
        self.rating = await self.get_rating(user, refresh=refresh)
        if not self.lazy:
            self.review = await self.get_review(user, refresh=refresh)
            self.year = await self.get_year(refresh=refresh)

    @staticmethod
    async def initialise(
        film: str, user: str, session: "ClientSession"
    ) -> "LetterboxdFilm":
        film_obj: LetterboxdFilm = LetterboxdFilm(film, session)
        await film_obj.populate(user)
        return film_obj
