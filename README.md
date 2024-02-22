# lttrpy
A CLI Python script to compare users' Letterboxd "watched" lists, with ratings and "likes".

### Usage

```
python lttrpy user1 [user2 ...]
```

### Requirements

* Python >= 3.9
* `aiohttp`
* `lxml`
  - `uvloop` - optional on Linux or MacOS, for faster async loops
  