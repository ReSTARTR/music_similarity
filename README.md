## install requirements
    pip install redis
    pip install https://github.com/jc/python-lastfm/zipball/master

## set api key

* Get api key from [http://www.lastfm.jp/api/account]
* Edit run.py
    API_KEY = 'YOUR API KEY'

## run
    python ./run.py

## data in Redis

### list
- list:artists
  - value: [ {artist_name},, ...]
  - type: list

### rank
- rank:artists
  - value: [ ({artist_name},{score}), ...]
  - type: sorted set
- rank:tags
  - value: [ ({tag_name},{score}), ...]
  - type: sorted set

### artist
- artist:tags:{artist_name}
  - value: [ {tag_name}, ...]
  - type: list
- artist:similars{artist_name}
  - value: [ ({tag_name},{score}), ...]
  - type: sorted set
- artist:sims:{artist_name}
  - value: [ {tag_name}, ...]
  - type: list

### tag
- tag:artists:{tag_name}
  - value: [{artist_name}, ...]
  - type: list


