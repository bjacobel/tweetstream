from twitter import *
from myoauth import creds
from CacheContainer import CacheContainer
from ipdb import launch_ipdb_on_exception
import re
from math import log

cache_length = 300


def importance(tweet):
    points = 0

    # add some value for the tweet being itself a retweet
    if re.search(r'RT @\w+\:', tweet['text']):
        points += 3

    # add value based on the number of followers the person tweeting has over 1000
    points += log(tweet['user']['followers_count'], 10) - 3

    # highly devalue @replies
    if re.match(r'@', tweet['text']):
        points -= 5

    # slightly devalue tweets by users already in the cache (no livetweeting, guys)
    if tweet['user']['screen_name'] in cache.lookinside('user', 'screen_name'):
        points -= 1

    # devalue every @mention past 1 (it indicates the tweet is for their benefit, not ours)
    mentions = len(re.findall(r'@', tweet['text']))
    if mentions > 1:
        points -= mentions * -0.5

    # devalue swearwords because god forbid we offend somebody
    # proof of concept - this could either get way more complex or removed entirely
    # because in theory we trust the people we're following to not be jerks
    if re.search(r'fuck|\bass\b|shit|bitch', tweet['text']):
        points -= 2

    return points


def rate():
    return cache.len() / float(cache_length) * 1000


def main():
    twitter = Twitter(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))
    twitter_stream = TwitterStream(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))

    global cache
    cache = CacheContainer(cache_length)

    id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.filter(follow=id_string)

    with launch_ipdb_on_exception():
        for tweet in iterator:
            # tweet comes from someone in the list (not an RT of one of their tweets)
            if 'user' in tweet and tweet['user']['id_str'] in id_list:
                print("%.2f - %s: %s") % (importance(tweet), tweet['user']['name'].encode('utf-8'), tweet['text'].encode('utf-8'))
                if importance(tweet) > rate():
                    twitter.statuses.retweet(id=tweet['id'])
                cache.add(tweet)


if __name__ == "__main__":
    main()
