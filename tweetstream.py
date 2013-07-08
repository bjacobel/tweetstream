from twitter import *
from pprint import pprint
from datetime import datetime
from myoauth import creds
import re


def importance(tweet):
    points = 0
    if re.search(r'RT @\w+\:', tweet['text']):
        points += 2
    return points


def main():
    twitter_stream = TwitterStream(auth=OAuth(myoauth.creds['OAUTH_TOKEN'], myoauth.creds['OAUTH_SECRET'], myoauth.creds['CONSUMER_KEY'], myoauth.creds['CONSUMER_SECRET']))

    cache = CacheContainer()

    id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.filter(follow=id_string)

    for tweet in iterator:
        # tweet comes from someone in the list and isn't an @reply by them
        if 'user' in tweet and tweet['user']['id_str'] in id_list and not re.match(r'@', tweet['text']):
            cache.add((tweet, datetime.now()))
            print cache
            print tweet['user']['name'] + ": " + tweet['text']
            #print " --> Importance of that tweet was " + str(importance(tweet))

if __name__ == "__main__":
    main()

