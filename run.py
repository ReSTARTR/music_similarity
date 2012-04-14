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

def set_artist(artist):
    for n in artist['similars']:
        r.sadd('artist:sims:%s' % artist['name'], n)

    cnt = 1
    with r.pipeline() as pipe:
        for t in artist['tags']:
            pipe.zincrby('rank:tags', t, 1)
            pipe.sadd('tag:artists:%s' % t, artist['name'])
            pipe.zadd('artist:tags:%s' % artist['name'], t, cnt)
            pipe.execute()
            cnt += 1

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
        if artist:
            tags = [ tag.name.lower() for tag in artist.top_tags ]
            similars =  [ s.name.encode('utf-8') for s in artist.similar ]
            set_artist(
                    {'name': name,
                     'tags': tags,
                     'similars': similars})
    except lastfm.error.InvalidParametersError, e:
        print e
    finally:
        time.sleep(1)

def get_artists():
    artists = []
    with open(ARTIST_FILE, 'r') as f:
        for line in f.readlines()[:READ_NUM]:
            if len(line) > 1:
                artists.append(line[:-1])
    return artists

def make_similars(artists):
    r.delete('rank:artists')
    r.delete('artist:similars:*')

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
    return r.smembers('artist:sims:%s' % artist)

def get_same_tags(a, b):
    a_tag = r.zrange('artist:tags:%s' % a, 1, MATCH_TAGS)
    b_tag = r.zrange('artist:tags:%s' % b, 1, MATCH_TAGS)

    score = MATCH_TAGS
    same_tags = []
    for t in a_tag:
        if t in b_tag:
            same_tags.append( (t, score) )
        score -= 1
    return same_tags

def get_artist_tags(artist):
    return r.zrange('artist:tags:%s' % artist, 0, -1)

def get_similar_artists(name):
    return r.zrevrange('artist:similars:%s' % name, 0, -1, withscores=True)

def get_top_tags():
    return r.zrevrange('rank:tags', 0, 30, withscores=True)

def get_top_artists():
    return r.zrevrange('rank:artists', 0, 30, withscores=True)

def get_similar_artists_in(name, artist_names):
    return [ s for s in get_sims(name) if s.upper() in artist_names ]


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
    make_similars(artists)

def read():
    artists = get_top_artists()
    artist_names = [ n for (n,s) in artists ]
    for (name,score) in artists:
        similars = get_similar_artists(name)
        print '----'
        print name

        print 'similar from last.fm:', get_similar_artists_in(name, artist_names)

        for (name_,similarity) in similars[:5]:
            tags = get_same_tags(name, name_)
            tags = sorted(tags, key=lambda x: x[1], reverse=True)
            print '\t', similarity, '\tname:',name_,  '\ttags:','/'.join(dict(tags).keys())

    print get_top_tags()[:10]

if __name__ == '__main__':
    #update_db()
    read()

