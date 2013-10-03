from __future__ import print_function
from twitter import *
from myoauth import creds
from redis_container import RedisContainer
from Levenshtein import ratio
from math import log
from time import time
import re

cache_length = 300

f = open('logs/log-{}.csv'.format(int(time())), 'w')


def importance(tweet):

    f.write("\"")

    points = 0

    # Kill the tweet with no points if it's vulgar
    if re.search(r'fuck|\bass(hole)?\b|shit|bitch', tweet['text'].lower()):
        f.write("thrown out for being vulgar")
        return 0

    tags = []
    if 'hashtags' in tweet:
        for hashtag in tweet['hashtags']:
            tags.append(hashtag['tweet'])

    # add value for the tweet being itself a retweet
    if 'retweeted_status' in tweet:
        points += 1.5
        tweet = tweet['retweeted_status']
        f.write("a retweet (really from @{}) (+1.50), ".format(tweet['user']['screen_name']))

    # add value for favorites and retweets
    if 'retweet_count' in tweet and tweet['retweet_count']:
        points += log(tweet['retweet_count'], 10)
        f.write("retweeted by {} (+{:.2f}), ".format(tweet['retweet_count'], log(tweet['retweet_count'], 10)))
    if 'favorite_count' in tweet and tweet['favorite_count']:
        points += log(tweet['favorite_count'], 10)
        f.write("favorited by {} (+{:.2f}), ".format(tweet['favorite_count'], log(tweet['favorite_count'], 10)))

    # add value for sharing links and media
    urls = ""
    if 'entities' in tweet:
        if 'urls' in tweet['entities']:
            for url in tweet['entities']['urls']:
                urls += " ".join(url['display_url'])
            print(tweet['text'] + " :: " + urls)
        else:
            print (tweet['text'] + " :: (no URLs parsed)")

    if 'media' in tweet or re.search(r'(vine|pic\.twitter|twitpic|yfrog|instagr(\.)?am)', urls):
        points += 1.5
        f.write("contains media (+1.5), ")
    elif urls is not "":
        points += 1.5
        f.write("contains a link (non-media) (+1.5), ")

    # uprank for tweets with hashtags shared by 25% of the other tweets in the cache
    for tag in tags:
        cached_tags = []
        for taglist in cache.inspect_value('hashtags'):
            for tag in taglist:
                cached_tags.append(tag['text'])
        if len(re.findall(tag, ' '.join(cached_tags)))/float(len(cached_tags)) > 0.25:
            points += 1
            f.write("contains a popular hashtag (+1.0), ")

    # highly devalue tweets that are suspected duplicates
    # uses Levenshtein edit distance
    for cached_tweet in cache.inspect_value('text'):
        if ratio(tweet['text'], cached_tweet) > 0.75:  # 75% similarity
            points -= 5
            f.write("a suspected duplicate (-5.0), ")

    # highly devalue @replies
    if re.match(r'@', tweet['text']):
        points -= 6.5
        f.write("an @reply (-6.5), ")

    # devalue every @mention past 1 (they indicate the tweet is for those peoples' benefit, not ours)
    mentions = len(re.findall(r'@', tweet['text']))
    if mentions > 1:
        points -= ((mentions-1) * 0.75)
        f.write("too @mention-y (-{:.2f}), ".format((mentions-1) * 0.75))

    # downrank stupid hashtags
    for tag in tags:
        if re.match(r'yolo|omg|wtf|lol|some|sm|wow|ff)', tag.lower()):
            points -= 1.5
            f.write("has stupid hashtags (-1.5 per), ")

    # Public conversations that have nothing to do with you
    if re.match(r'\.@\w+\s+[A-Z]', tweet['text']):
        points -= 1.5
        f.write("a needlessly public conversation (-1.5), ")

    # retweet cascades
    if re.search(r'RT[^RT]+RT', tweet['text']):
        points -= 1.5
        f.write("-a retweet cascade (-1.5), ")

    # Plaintive requests for follows, or 'Follow Friday'
    if re.search(r'(?i)please.*(\bwatch\b|\bfollow\b)|(\bwatch\b|\bfollow\b).*(me|please|back) | ^#?(FF|ff)', tweet['text']):
        points -= 2
        f.write("a request for attention (-2.0), ")

    # the last rule of wire curator is you do not talk about wire curator
    if re.search(r'@wirecurator', tweet['text']):
        points -= 4
        f.write("@wirecurator (-4.0), ")

    if points == 0:
        f.write("had no special attributes")

    f.write("\", ")
    
    return points


# average tweets per 100 seconds
def rate():
    elapsed = time() - start
    if elapsed < cache_length:
        return cache.size() / float(elapsed) * 100
    else:
        return cache.size() / float(cache_length) * 100


def main():
    auth = OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET'])
    twitter = Twitter(auth=auth)
    twitter_stream = TwitterStream(auth=auth)

    global cache
    cache = RedisContainer(cache_length)

    global start
    start = time()

    id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.filter(follow=id_string)

    # Print column headers to CSV
    f.write("User,Tweet,Attributes Assigned,Tweet Value,Current Rate,Retweeted?\n")

    for tweet in iterator:
        try:
            # tweet comes from someone in the list (not an RT of one of their tweets)
            if 'user' in tweet and tweet['user']['id_str'] in id_list:
                
                # print user name to csv
                f.write("{},".format(tweet['user']['screen_name'].encode('utf-8')))

                # print tweet text to csv
                f.write("\"{}\",".format(tweet['text'].encode('utf-8')))

                tweet_imp = importance(tweet)
                stream_rate = rate()

                if tweet_imp > stream_rate:
                    f.write("{:.2f}, {:.2f}, yes\n".format(tweet_imp, stream_rate))
                    while not twitter.statuses.retweet(id=tweet['id']):
                        pass
                else:
                    f.write("{:.2f}, {:.2f}, no\n".format(tweet_imp, stream_rate))

                # cache the tweet whether it was worthy or not
                cache.add(dict(tweet))
        except:
            import traceback; print(traceback.print_exc())
            print("\n")
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cache.clear()

