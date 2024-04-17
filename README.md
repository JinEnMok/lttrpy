# lttrpy

## A CLI Python script to compare Letterboxd users' watched films, with ratings and likes.

### Usage

```
python lttrpy.py user1 [user2 ...]
```

### Output

Writes the comparison tables in a Github-flavoured Markdown file or an HTML file.

Sample output:

## 110 common films for user1, user2, user3.

Film title | user1's rating | user2's rating | user3's rating
--- | :---: | :---: | :---:
American Psycho |  |  | ★★★★ (liked)
Another Round |  |  | ★★★★ (liked)
Glass Onion |  |  |
WALL·E | ★★★★½ (liked) |  |
Ratatouille | ★★★★½ |  |


### Requirements

* Python >= 3.10
* `aiohttp`
* `lxml`
* `jinja2`
- (optional) `uvloop` - speeds up (?) async, Linux and MacOS only
  

### Known bugs and troubleshooting

* Sometimes the scraping simply hangs. Usually it takes no more than 15-20 seconds in total (for up to 5 users), so feel free to CTRL-C and start over if it's taking longer.


### TODO:
- Bugs: 
    * LetterboxdFilm.get_page() breaks if there's no diary entry. Probably should rewrite it so that it uses the "activity" page directly

- Features:
    * Sort by:
        - Alphabetic order
        - Has rating/like/review
        - Sort by numerical rating (unicode ★½ to str)
        - Common ratings
    * Display reviews
    * Interactive mode
- Improvements:
    * More verbosity during stages (fancy progress bars?)
- Long-term goals:
    * Create a locally-served interactive app

### Credits

This script was inspired by a similar script from Sena Bayram.