"""Output formatter for Letterboxd watched film comparisons.
    Currently able to output HTML and Markdown."""

import sys

from typing import TYPE_CHECKING
from pathlib import Path
from jinja2 import Environment, FileSystemLoader


from typing import Iterable
from .LetterboxdProfile import LetterboxdProfile
from os import PathLike


class Formatter:
    module_dir = Path(sys.path[0])
    environment: Environment = Environment(
        loader=FileSystemLoader([module_dir / "Templates"]),
        lstrip_blocks=True,
        trim_blocks=True,
    )

    def __init__(self, profiles: Iterable[LetterboxdProfile]) -> None:
        self.profiles: Iterable[LetterboxdProfile] = profiles
        self.overlap: set[str] = LetterboxdProfile.common(*profiles)
        self.context: dict[str, Iterable[LetterboxdProfile] | set[str]] = {
            "profiles": self.profiles,
            "common_films": self.overlap,
        }

    def make_html(self) -> str:
        template = self.environment.get_template("HTMLTemplate.jinja")
        return template.render(self.context)

    def make_md(self) -> str:
        template = self.environment.get_template("MarkdownTemplate.jinja")
        return template.render(self.context)

    def write(self, filename: str | PathLike, out_format: str = "html") -> None:
        """
        Writes output to specified file

        Args:
            filename: output filename
            out_format: 'html' or 'md'
        """
        if out_format.lower() == "html":
            text: str = self.make_html()
        elif out_format.lower() == "md":
            text: str = self.make_md()
        else:
            raise ValueError("Provided output format not recognised or not supported.")
        with open(filename, mode="w", encoding="utf-8") as f:
            print(text, file=f)
