from aiohttp import ClientResponseError, ClientSession
from lxml import html
from LetterboxdFilm import LetterboxdFilm
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from typing import Iterator


class LetterboxdProfile:
    def __init__(self, username: str, session) -> None:
        self.username: str = username
        self.link: str = f"https://letterboxd.com/{self.username}"
        self.session: ClientSession = session
        self.films: dict[str, LetterboxdFilm] = dict()

    def __repr__(self) -> str:
        return f"LetterboxdProfile({self.username!r}, {self.session!r})"

    def __getitem__(self, key) -> Union[tuple, LetterboxdFilm]:
        if type(key) is str:
            return self.films[key]
        elif type(key) in (slice, int):
            return tuple(self.films.values())[key]

    def __iter__(self) -> "Iterator":
        return iter(self.films)

    def __contains__(self, film: str) -> bool:
        return film in self.films

    def __len__(self) -> int:
        return len(self.films)

    def __add__(self, *others) -> set[str]:
        return self.common(self, *others)

    async def get_user_page(self, pagenum) -> html.HtmlElement:
        url: str = "https://letterboxd.com/{}/films/page/{}"
        async with self.session.get(url.format(self.username, pagenum)) as resp:
            page: str = await resp.text()
        return html.document_fromstring(page)

    async def get_all_pages(self) -> list[html.HtmlElement]:
        page1: html.HtmlElement = await self.get_user_page(1)
        last_page: int = int(
            page1.xpath("//li[@class='paginate-page'][last()]/a/text()")[0]
        )
        pages: list = [page1] + [
            (await self.get_user_page(page)) for page in range(2, last_page + 1)
        ]
        print(f"Downloaded {last_page} pages for {self.username}")
        return pages

    def find_films(self, page) -> dict[str, LetterboxdFilm]:
        films: dict[str, LetterboxdFilm] = dict(
            [
                (
                    slug := poster.xpath("./div")[0].get("data-film-slug"),
                    LetterboxdFilm(
                        film_id=slug,
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

    async def populate(self) -> None:
        """
        Here we're simply unpacking all the pages' info
        """
        self.films: dict[str, dict] = {
            film_id: film_data
            for page in await self.get_all_pages()
            for film_id, film_data in self.find_films(page).items()
        }
        print(f"Populated {self.username}'s profile with {len(self)} films")

    @staticmethod
    async def exists(username: str, session: ClientSession) -> bool:
        try:
            await session.get(
                f"https://letterboxd.com/{username}", raise_for_status=True
            )
            return True
        except ClientResponseError:
            return False

    @staticmethod
    def common(*profiles) -> set[str]:
        return set.intersection(*(set(prof.films.keys()) for prof in profiles))

    @staticmethod
    def diff(*profiles) -> set[str]:
        return set.difference(*(set(prof.films.keys()) for prof in profiles))

    @staticmethod
    async def initialise(username: str, session) -> Union["LetterboxdProfile", None]:
        """
        If user exists, create, populate, and return its profile object.

        Args:
            username: username
            session: aiohttp session

        Returns:
            LetterboxProfile(username) object
        """
        if await LetterboxdProfile.exists(username, session):
            prof = LetterboxdProfile(username, session)
            print(f"Found user {username}")
            await prof.populate()
            return prof
        else:
            print(f"Could not initialise {username}")
