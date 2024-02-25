from aiohttp import ClientResponseError, ClientSession
from lxml import html


class LetterboxdProfile:
    def __init__(self, username: str, session) -> None:
        self.username: str = username
        self.link: str = f"https://letterboxd.com/{self.username}"
        self.session: ClientSession = session
        self.films: dict[str, dict] = dict()

    def __repr__(self) -> str:
        return f"LetterboxdProfile({self.username!r}, {self.session!r})"

    def __getitem__(self, key):
        if type(key) is str:
            return self.films[key]
        elif type(key) in (slice, int):
            return tuple(self.films.values())[key]

    def __iter__(self):
        return iter(self.films)

    def __contains__(self, item) -> bool:
        return item in self.films

    def __len__(self) -> int:
        return len(self.films)

    def __add__(self, *others) -> set:
        return self.common(self, *others)

    @staticmethod
    async def exists(username, session) -> bool:
        """
        Check if a Letterboxd profile exists

        Args:
            username
            session: the aiohttp ClientSession object

        Returns:
            Username, if the associated profile exists
            Otherwise, None
        """
        try:
            await session.get(
                f"https://letterboxd.com/{username}", raise_for_status=True
            )
            return True
        except ClientResponseError:
            return False

    @staticmethod
    def common(*profiles) -> set[dict]:
        """
        Compare multiple profiles and find common films.

        Args:
            profiles: an iterable with LetterboxdProfile entries

        Returns:
            A set of films present in every passed profile.
        """
        return set.intersection(*(set(prof.films.keys()) for prof in profiles))

    @staticmethod
    def diff(*profiles) -> set[dict]:
        return set.difference(*(set(prof.films.keys()) for prof in profiles))

    def find_films(self, page) -> dict[str, dict]:
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

    async def get_all_pages(self) -> list:
        page1 = await self.get_user_page(1)
        last_page = int(page1.xpath("//li[@class='paginate-page'][last()]/a/text()")[0])
        pages = [page1] + [
            (await self.get_user_page(page)) for page in range(2, last_page + 1)
        ]
        print(f"Downloaded {last_page} pages for {self.username}")
        return pages

    async def get_user_page(self, pagenum):
        url = "https://letterboxd.com/{}/films/page/{}"
        async with self.session.get(url.format(self.username, pagenum)) as resp:
            page = await resp.text()
        return html.document_fromstring(page)

    async def populate(self) -> None:
        self.films = {
            film: data
            for page in await self.get_all_pages()
            for film, data in self.find_films(page).items()
        }
        print(f"Populated {self.username}'s profile with {len(self)} films")

    @staticmethod
    async def initialise(username: str, session):
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
