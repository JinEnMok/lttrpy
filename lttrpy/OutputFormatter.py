from LetterboxdProfile import LetterboxdProfile
from string import Template
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable

# https://docs.python.org/3/library/string.html#string.Template


class Formatter:
    def __init__(self, profiles: Iterable[LetterboxdProfile]) -> None:
        self.profiles: Iterable[LetterboxdProfile] = profiles
        self.overlap: set[str] = LetterboxdProfile.common(*profiles)

    def make_html(self) -> str:

        title_entry = '<th>{}</th>'
        rt_entry = '<td style="text-align:center">{}</td>'
        
        page_header: str = (
            "<h2>" + f"{len(self.overlap)} common films for "
            f"{', '.join(p.username for p in self.profiles)}" + "</h2>"
        )

        table_header: str = (
            "<thead>"
            + (
                "Film title | "
                + " | ".join(f"{p.username}'s rating" for p in self.profiles)
            )
            + "</thead>"
        )
        table_footer: str = (
            "<tfoot>"
            + (
                "Film title | "
                + " | ".join(f"{p.username}'s rating" for p in self.profiles)
            )
            + "</tfoot>"
        )
        # table_entries: tuple[str] = (
        #     "<tbody>",
        #     *["<tr>",
        #       f"<td>{self.profiles[0].films[film].title}<td>",

        #         + " | ".join(
        #             (
        #                 f"{p.films[film].rating} (liked)"
        #                 if p.films[film].liked
        #                 else f"{p.films[film].rating}"
        #             )
        #             for p in self.profiles
        #         )
        #         for film in self.overlap
        #     "</tr>"], "</tbody>"
        # )

        return (page_header, "<table>", table_header, *table_entries, table_footer, "</table>")

    def make_md(self) -> str:
        page_header: str = (
            f"## {len(self.overlap)} common films for "
            f"{', '.join(p.username for p in self.profiles)}.\n"
        )

        table_header: str = "Film title | " + " | ".join(
            f"{p.username}'s rating" for p in self.profiles
        )
        top_row_sep: str = "--- | " + " | ".join(":---:" for _ in self.profiles)
        table_entries: str = (
            f"{self.profiles[0].films[film].title} | "
            + " | ".join(
                (
                    f"{p.films[film].rating} (liked)"
                    if p.films[film].liked
                    else f"{p.films[film].rating}"
                )
                for p in self.profiles
            )
            for film in self.overlap
        )
        return (page_header, table_header, top_row_sep, *table_entries)

    def write(self, filename: str, out_format: str = "html") -> None:
        """
        Writes output to specified file

        Args:
            filename: output filename
            out_format: 'html' or 'markdown' | 'md'
        """
        if out_format.lower() == "html":
            text: Iterable = self.make_html()
        elif out_format.lower() in ("md", "markdown"):
            text: Iterable = self.make_md()
        with open(filename, mode="w", encoding="utf-8") as f:
            print(*text, sep="\n", end="\n", file=f)


def write_markdown(profiles: Iterable, outfile: str) -> None:
    """
    Calculates film overlap between users and writes it as a Markdown table

    Example:

    |     Film title     |  user1's rating  |  user2's rating  |
    |--------------------|:----------------:|:----------------:|
    |Another Round       |       n/r        |      ★★★       |
    |Million Dollar Baby |  ★★★★ (liked) |       n/r        |
    |Bana Masal Anlatma  |        ★        |       ★★        |

    Args:
        profiles: the user profile objects as an iterable
        outfile: output filename

    Returns:
        None
    """
    common_films: set[str] = LetterboxdProfile.common(*profiles)

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(
            f"## {len(common_films)} common films for "
            f"{', '.join(p.username for p in profiles)}.\n\n"
        )

        f.write("| Film title |")
        for user in profiles:
            f.write(f" {user.username}'s rating |")
        f.write("\n")

        f.write("| --- |")
        for user in profiles:
            f.write(" :---: |")
        f.write("\n")

        for film_id in common_films:
            f.write(f"| {profiles[0].films[film_id].title} |")
            for user in profiles:
                rating: str = user.films[film_id].rating
                if user.films[film_id].liked:
                    f.write(f" {rating} (liked) |")
                else:
                    f.write(f" {rating} |")
            f.write("\n")
    print(f"Wrote output to {outfile}")
