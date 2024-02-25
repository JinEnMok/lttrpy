from lxml import html


class LetterboxdFilm:
    def __init__(
        self,
        film_id: str,
        session,
        title: str = None,
        year: int = None,
        rating: str = None,
        liked: bool = None,
        review: tuple(bool, str) = None,
    ):
        self.film_id: str = film_id
        self.session = session
        self.title: str = title
        self.year: int = year
        self.rating: str = rating
        self.liked: bool = liked
        self.review: tuple(bool, str) = review

    def __repr__(self):
        return f"Film({self.title!r}, {self.film_id!r}, {self.session!r})"

    def __str__(self):
        return f"{self.title} ({self.year})"

    async def get_page(self, user='', refresh=False):
        url = "https://letterboxd.com/{}/film/{}/"
        async with self.session.get(url.format(user, self.film_id)) as resp:
            page = await resp.text()
        tree = html.document_fromstring(page)
        return tree

    async def get_year(self, refresh=False) -> int:
        if self.year and not refresh:
            return self.year
        xpath = "//meta[@property='og:title'][1]"
        tree = await self.get_page()
        year = tree.xpath(xpath)[0].get("content")[-5:-1]
        return int(year)

    async def get_review(self, user, refresh=False) -> tuple(bool, str):
        if self.review and not refresh:
            return self.review
        xpath = "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
        tree = await self.get_page(user=user)
        if "This review may contain spoilers" in tree.xpath(
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
        xpath = "//meta[@name='twitter:data2'][1]"
        tree = await self.get_page(user=user)
        rating = tree.xpath(xpath)
        if rating:
            return rating[0].get('content')
        else:
            return rating

    async def populate(self, user: str, refresh=False):
        self.title = await self.get_title()
        self.review = await self.get_review(user)
        self.year = await self.get_year()
        self.rating = await self.get_rating(user)

    @staticmethod
    async def initialise(film, user, session):
        film_obj = LetterboxdFilm(film, session)
        await film_obj.populate(user)
        return film_obj
