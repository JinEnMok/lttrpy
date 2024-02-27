from .LetterboxdProfile import LetterboxdProfile


class Formatter:
    def __init__(self, profiles: set[dict]):
        self.profiles: set[dict] = profiles

    def make_html(self) -> str:
        pass

    def make_md(self) -> str:
        pass

    def write(self, filename: str, out_format: str = "html") -> None:
        """
        Writes output to specified file

        Args:
            filename: output filename
            out_format: HTML or Markdown
        """
        if out_format == "html":
            text: str = self.make_html()
        elif out_format == "md":
            text: str = self.make_md()
        with open(filename, mode="w", encoding="utf-8") as f:
            f.write(text)


def write_markdown(profiles, outfile: str) -> None:
    """
    Calculates film overlap between users and writes it as a Markdown table

    Example:

    |     Film title     |      user1's rating        |       user2's rating      |
    |--------------------|:--------------------------:|:-------------------------:|
    |Another Round       |             n/r            |            ★★★           |
    |Million Dollar Baby |       ★★★★ (liked)       |             n/r           |
    |Bana Masal Anlatma  |              ★             |             ★★           |

    Args:
        profiles: the user profile objects as an iterable
        outfile: output filename

    Returns:
        None
    """

    common_films: set = LetterboxdProfile.common(*profiles)

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(
            f"## {len(common_films)} common films for "
            f"{', '.join(p.username for p in profiles)}.\n\n"
        )

        f.write("| Film title |")
        for user in profiles:
            f.write(f"{user.username}'s rating |")
        f.write("\n")

        f.write("| --- |")
        for user in profiles:
            f.write(": --- :|")
        f.write("\n")

        for film_id in common_films:
            f.write(
                f"| {profiles[0].films[film_id]["title"]} |"
            )
            for user in profiles:
                rating: str = user.films[film_id]["rating"][0]
                if user.films[film_id]["liked"]:
                    f.write(f"{rating} (liked) |")
                else:
                    f.write(f"{rating} |")
            f.write("\n")
    print(f"Wrote output to {outfile}")
