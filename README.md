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

|         Film title         |      user1's rating    |     user2's rating     |   user3's rating   |
|----------------------------|:----------------------:|:----------------------:|:------------------:|
|Waking Life                 |   ★★★★★ (liked)     |     ★★★★★ (liked)      |        n/r         |
|The Revenant                |        ★★★★½        |          n/r           |        ★★★         |
|The Grand Budapest Hotel    |     ★★★★½ (liked)      |     ★★★★★ (liked)      |        n/r         |
|Léon: The Professional      |          ★★★★          |          n/r           |        n/r         |
|Hercules                    |          n/r           |          n/r           |       ★★★★        |
|Baby Driver                 |     ★★★★½ (liked)      |          ★★★           |        n/r         |
|Now You See Me              |          ★★★½          |          n/r           |        (liked)        |
|X2                          |          n/r           |          n/r           |        n/r         |


There's an effort to make the source tables have constant column width, but the Unicode stars usually mess that up.


### Requirements

* Python >= 3.9
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
        - Film year
    * New output formats:
        - Directly to HTML
    * Display reviews
    * Interactive mode
- Improvements:
    * More verbosity during stages (fancy progress bars?)
    * rewrite the profile class to create instances of the film class \
      so that the film class can then pull film year, reviews, etc
- Long-term goals:
    * Create a locally-served interactive app