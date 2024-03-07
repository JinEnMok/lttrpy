# lttrpy

## A CLI Python script to compare Letterboxd users' watched films, with ratings and likes.

### Usage

```
python lttrpy.py user1 [user2 ...]
```

### Output

Writes the comparison tables in a Github-flavoured Markdown file.

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
- (optional) `uvloop` - speeds up async, Linux and MacOS only
  
### TODO:

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
