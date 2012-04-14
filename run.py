# -*- coding: utf-8 -*-

import time
import redis
import lastfm
from lastfm.error import InvalidParametersError

READ_NUM = 100
MATCH_TAGS = 100
ARTIST_FILE = './resources/frf2012.txt'
API_KEY =''

api = lastfm.Api(API_KEY)

r = redis.Redis()

class Artist(object):
    def __init__(self, name):
        self._name = name

    @property
    def name(self):
        return self._name

    @property
    def tags(self):
        if not hasattr(self, '_tags'):
            self._tags = r.lrange('artist:tags:%s' % self._name, 0, MATCH_TAGS)
        return self._tags

    @property
    def similars(self):
        if not hasattr(self, '_similars'):
            similars = [ (name,score) for (name,score) in r.zrevrange('artist:similars:%s' % self._name, 0, MATCH_TAGS, withscores=True)]
            similars = sorted(similars, key=lambda x:x[1], reverse=True)
            self._similars = [ Artist(k) for (k,v) in sorted(similars, key=lambda x:x[1], reverse=True)]
        return self._similars

    def tags_intersect(self, artist, match_tags=None):
        score = MATCH_TAGS
        ts = []
        match_tags = match_tags or MATCH_TAGS #int(MATCH_TAGS*0.25)
        for t in self.tags[:match_tags]:
            if t in artist.tags:
                ts.append( (t, score) )
            score -= 1
        return ts

    def similarity(self, artist):
        intersect = self.tags_intersect(artist)
        return gen_tag_score(intersect) if len(intersect) else 0.0

def gen_tag_score(tags):
    x = sum([ e[1] for e in tags])
    y = float(sum(range(MATCH_TAGS)))
    return ( x / y ) * 100

def make_similar_artist(name, targets):
    l = []
    for n in targets:
        same_tags = get_same_tags(name , n)
        score = 1
        if len(same_tags)>0:
            score = gen_tag_score(same_tags)
            l.append( (n, same_tags) )
        r.zincrby('rank:artists', name, amount=int(score))
    return l

def load_artist_info(name):
    try:
        artist = api.get_artist(artist=name.decode('utf-8'))
        if not artist:
            return
        r.rpush('list:artists', artist.name)
        tags = [ tag.name.lower() for tag in artist.top_tags ]
        similars =  [ s.name.encode('utf-8') for s in artist.similar ]

        with r.pipeline() as pipe:
            for n in similars:
                pipe.rpush('artist:sims:%s' % artist.name, n)
            pipe.execute() 

            for tag in tags:
                pipe.zincrby('rank:tags', tag, 1)
                pipe.sadd('tag:artists:%s' % tag, artist.name)
                pipe.rpush('artist:tags:%s' % artist.name, tag)
                pipe.execute()
    except lastfm.error.InvalidParametersError, e:
        print e
    finally:
        time.sleep(0.2)

def get_artists():
    artists = []
    with open(ARTIST_FILE, 'r') as f:
        for line in f.readlines()[:READ_NUM]:
            if len(line) > 1:
                artists.append(line[:-1])
    return artists

def make_similars():
    r.delete('rank:artists')
    r.delete('artist:similars:*')

    artists = get_artist_list()
    for artist_name in artists:
        anothers = [name for name in artists if name != artist_name]
        similars = make_similar_artist(artist_name, anothers)
        with r.pipeline() as pipe:
            for (name_,same_tags) in similars:
                pipe.zadd('artist:similars:%s' % artist_name, name_, gen_tag_score(same_tags))
            pipe.execute()

def tag_score(tag):
    return r.zscore('tag:rank', tag) or 0

def get_sims(artist):
    return r.lrange('artist:sims:%s' % artist, 0, -1)

def get_same_tags(a, b):
    a_tag = r.lrange('artist:tags:%s' % a, 1, MATCH_TAGS)
    b_tag = r.lrange('artist:tags:%s' % b, 1, MATCH_TAGS)
    score = MATCH_TAGS
    same_tags = []
    for t in a_tag:
        if t in b_tag:
            same_tags.append( (t, score) )
        score -= 1
    return same_tags

def get_artist_tags(artist):
    return r.lrange('artist:tags:%s' % artist, 0, -1)

def get_similar_artists(name):
    return r.zrevrange('artist:similars:%s' % name, 0, -1, withscores=True)

def get_top_tags():
    return r.zrevrange('rank:tags', 0, 30, withscores=True)

def get_top_artists():
    return r.zrevrange('rank:artists', 0, 30, withscores=True)

def get_similar_artists_in(name, artist_names):
    return [ s for s in get_sims(name) if s.upper() in artist_names ]

def get_artist_list():
    return r.lrange('list:artists', 0, -1)

def update_db():
    r.flushdb()
    artists = get_artists()
    print 'now loading...'
    cnt = 0
    for artist_name in artists:
        if not artist_name:
            continue
        print cnt,'/',len(artists)
        load_artist_info(artist_name)
        cnt += 1
    make_similars()

def read():
    artists = get_top_artists()
    artist_names = [ n for (n,s) in artists ]
    for (name,score) in artists:
        artist = Artist(name)
        print '\n###', artist.name, 'score:', score, '\n'

        for a in artist.similars[:5]:
            score = artist.similarity(a)
            if score>0:
                print ' ', '%3d' % int(score*10), a.name, artist.tags_intersect(a)[:4]

if __name__ == '__main__':
    update_db()
    read()

