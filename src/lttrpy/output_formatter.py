"""Output formatter for Letterboxd watched film comparisons.
Currently able to output HTML and Markdown."""

import sys
from os import PathLike
from pathlib import Path
from typing import Iterable

from jinja2 import Environment, FileSystemLoader, Template

from .letterboxd_profile import LetterboxdProfile


class Formatter:
    """
    Formatter class that uses Jinja2 templates to create output from the parsed Letterboxd data.

    Example usage:
        output = Formatter(profiles)
        output.write("output.md", out_format="md")
    """

    module_dir: Path = Path(sys.path[0])
    environment: Environment = Environment(
        autoescape=True,
        loader=FileSystemLoader([module_dir / "templates"]),
        lstrip_blocks=True,
        trim_blocks=True,
    )

    def __init__(self, profiles: Iterable[LetterboxdProfile]) -> None:
        self.profiles: tuple[LetterboxdProfile, ...] = tuple(profiles)
        self.overlap: set[str] = self.profiles[0].common(*profiles)
        self.context: dict[str, Iterable[LetterboxdProfile] | set[str]] = {
            "profiles": self.profiles,
            "common_films": self.overlap,
        }

    def make_html(self) -> str:
        template: Template = self.environment.get_template("html_template.py.jinja")
        return template.render(self.context)

    def make_md(self) -> str:
        template: Template = self.environment.get_template("markdown_template.py.jinja")
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
            _err_wrong_ext: str = (
                f"Provided output format {out_format} not recognised or not supported."
            )
            raise ValueError(_err_wrong_ext)
        with open(
            Path(filename).resolve().with_suffix(f".{out_format.lower()}"),
            mode="w",
            encoding="utf-8",
        ) as f:
            print(text, file=f)
