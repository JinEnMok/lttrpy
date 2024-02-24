from lxml import html


class LetterboxdFilm:
    # will work on this later
    def __init__(self, film_id, session=None, ratings=[], reviews=[], liked=set()):

        self.string_id = film_id
        self.film_page = f"https://letterboxd.com/film/{self.string_id}"
        self.tvdb_id = None
        self.session = session
        # get title here
        self.title = None
        # also get film year
        self.year = None
        self.watched_by = set()
        self.ratings = ratings
        self.reviews = reviews

    def __repr__(self):
        return f"Film({self.title!r})"

    def __str__(self):
        return f"{self.title} ({self.year})"

    def add_user(self, user):
        if user not in self.watched_by:
            self.watched_by.add(user)
            self.populate(self, user)
            print(f"{self.title} ({self.year}) watched by {user}")

    async def get_review(self, username):
        REVIEW_PAGE = "https://letterboxd.com/{}/film/{}/"
        page = (
            await self.session.get(REVIEW_PAGE.format(username, self.string_id))
        ).text
        tree = html.document_fromstring(page)
        spoiler = (
            True
            if (
                "This review may contain spoilers"
                in tree.xpath("//meta[@name='description'][1]")[0].get("content")
            )
            else None
        )
        review = "\n".join(
            tree.xpath(
                "/html/body/div[1]/div/div/section/section/div[1]/div/div/p/text()"
            )
        )
        return spoiler, review

    def populate(self, username):
        pass
