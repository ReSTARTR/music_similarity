import music_similarity
music_similarity.init('testfes')

from music_similarity import *

class TestMusicSimilarity(object):

    def setup(self):
        r.flushdb()

    def test_gen_tag_score(self):
        tags = [('foo', 30), ('bar', 40), ('baz', 50)]
        assert gen_tag_score(tags) == ( 120 / 4950.0 ) * 100

    #def test_get_same_tags(self):
    #    r.rpush(KEY_ARTIST_TAGS % 'The Foo', ['foo', 'bar', 'baz'])
    #    r.rpush(KEY_ARTIST_TAGS % 'The Who', ['foo', 'bar', 'who'])
    #    print r.keys(KEY_ARTIST_TAGS % '*')
    #    tags = get_same_tags('The Foo', 'The Who')
    #    print tags

    def _test_update_db(self):
        load_artist_info('Radiohead')
        assert 0 < len(get_sims('Radiohead')) <= 100
        assert 0 < len(get_artist_tags('Radiohead')) <= 100

        load_artist_info('MUSE')
        load_artist_info('Beatles')
        assert get_artist_list() == ['Radiohead', 'Muse', 'Beatles']  # Normarized

        sims = make_similar_artist('Radiohead', ['MUSE', 'Beatles'])
        print sims

        make_similars()
        sims = get_similar_artists('Radiohead')
        assert [sim[0] for sim in sims] == ['Muse', 'Beatles']

