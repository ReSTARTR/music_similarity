# -*- coding: utf-8 -*-
import config


def usage():
    print 'usage: python ./run.py <key>'
    print 'the key is following'
    for k in config.settings.keys():
        print ' -', k, '\t:', config.settings[k]['desc']

if __name__ == '__main__':
    import sys
    if len(sys.argv)<2 or sys.argv[1] in ['-h','--help']:
        usage()
        sys.exit()

    from music_similarity import init, update_db, read

    init(sys.argv[1])
    update_db()
    read()
