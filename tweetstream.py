from twitter import *
from myoauth import creds
from CacheContainer import CacheContainer
import re
from math import log

cache_length = 500


def importance(tweet):
    points = 0

    # add some value for the tweet being itself a retweet
    if re.search(r'RT @\w+\:', tweet['text']):
        points += 3

    # add value based on the number of followers the person tweeting has over 1000
    points += log(tweet['user']['followers_count']) - 2

    # highly devalue @replies
    if re.match(r'@', tweet['text']):
        points -= 5

    # slightly devalue tweets by users already in the cache
    if tweet['user']['screen_name'] in cache.lookinside('user', 'screen_name'):
        points -= 1

    # devalue swearwords because god forbid we offend somebody
    #if swearwordzz:
    #    points -= 3

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

    for tweet in iterator:
        print("%.3f") % rate()
        # tweet comes from someone in the list and isn't an @reply by them
        if 'user' in tweet and tweet['user']['id_str'] in id_list:
            print(tweet['user']['name'].encode('utf-8') + ": " + tweet['text'].encode('utf-8'))
            if importance(tweet) > rate():
                print(" --> That one was a " + str(importance(tweet)) + ", so I retweeted it.")
                twitter.statuses.retweet(tweet['id'])
            cache.add(tweet)


if __name__ == "__main__":
    main()
