from LetterboxdProfile import LetterboxdProfile


def write_markdown(profiles, outfile):
    """
    Calculates film overlap between users and writes it as a Markdown table
    It tries to adjust column width so the unrendered Markdown looks alright,
    but the Unicode stars don't always allow that

    Example:

    |     Film title     |      user1's rating        |       user2's rating      |
    |--------------------|:--------------------------:|:-------------------------:|
    |Another Round       |             n/r            |             n/r           |
    |Million Dollar Baby |       ★★★★ (liked)       |             n/r           |
    |Bana Masal Anlatma  |             n/r            |             n/r           |

    Args:
        profiles: the user profile objects as an iterable
        outfile: output filename

    Returns:
        None
    """

    common_films: set = LetterboxdProfile.common(*profiles)

    # flexible column width
    # some magic numbers here, tune according to taste
    FILM_PADDING: int = 4
    film_width: int = FILM_PADDING + max(
        len(profiles[0][film_id]["title"]) for film_id in common_films
    )

    USER_PADDING: int = 4
    user_width: int = {
        user.username: USER_PADDING
        + (max(len(f"{user.username}'s rating"), len("★★★★★ (liked)")))
        for user in profiles
    }

    with open(outfile, "w", encoding="utf-8") as f:
        # write header
        f.write(
            f"## {len(common_films)} common films for "
            f"{', '.join(_.username for _ in profiles)}.\n\n"
        )

        f.write("|" + "Film title".center(film_width - 2) + "|")
        for user in profiles:
            f.write(f"{user.username}'s rating".center(user_width[user.username]) + "|")
        f.write("\n")

        f.write("|" + "-" * (film_width - 2) + "|")
        for user in profiles:
            f.write(":" + "-" * (user_width[user.username] - 2) + ":|")
        f.write("\n")

        # TODO: alphabetic (or other) ordering for the films
        for film_id in common_films:
            f.write(
                "|" + profiles[0].films[film_id]["title"].ljust(film_width - 2) + "|"
            )
            for user in profiles:
                if user.films[film_id]["rating"]:
                    rating = user.films[film_id]["rating"][0]
                else:
                    rating = "n/r"

                if user.films[film_id]["liked"]:
                    f.write(f"{rating} (liked)".center(user_width[user.username]) + "|")
                else:
                    f.write(rating.center(user_width[user.username]) + "|")
            f.write("\n")
    print(f"Wrote output to {outfile}")
