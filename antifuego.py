from twitter import *
from myoauth import creds
from redis_container import RedisContainer
from time import time
import requests
import re


cache_length = 900  # 15 minutes


def parse_links(tweet):
    # regex to match shortened URLs, god help me if this actually works
    if tweet['text']:
        text = tweet['text'].encode('utf-8')
        # every properly formed link on twitter is shortened to t.co already, so matching a whole bunch of other domains is unnecesary
        links = re.search(r'http:\/\/t\.co\/\w{10}', text).group(0)
        return links
    else:
        return []


# average tweets per 100 seconds
def rate():
    elapsed = time() - start
    if elapsed < 300:
        return cache.size() / float(elapsed) * 100
    else:
        return cache.size() / float(cache_length) * 100


def main():
    # twitter = Twitter(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))
    twitter_stream = TwitterStream(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))

    global cache
    cache = RedisContainer(cache_length)

    global start
    start = time()

    #id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    #id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.sample()  # filter(follow=id_string)

    for tweet in iterator:
        try:
            # tweet comes from someone in the list (not an RT of one of their tweets)
            if 'user' in tweet:  # and tweet['user']['id_str'] in id_list:
                links = parse_links(tweet)
                if links:
                    print(links)
        except:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cache.clear()
