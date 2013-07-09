from twitter import *
from myoauth import creds
from CacheContainer import CacheContainer
import matplotlib.pyplot as mpl
from math import log
from time import time
import re, sys, os

cache_length = 300


def importance(tweet):
    points = 0

    # construct a list of all hashtags - this will be used in several places
    tags = []
    if 'hashtags' in tweet:
        for hashtag in tweet['hashtags']:
            tags.append(hashtag['tweet'])

    # add value for the tweet being itself a retweet
    if 'retweeted_status' in tweet:
        points += 2
        tweet = tweet['retweeted_status']

    # add value based on the number of followers the person tweeting has over 1000
    points += log(tweet['user']['followers_count'], 10) - 3

    # add some value for being on peoples lists (people use lists, right?)
    points += log(tweet['user']['listed_count'], 10)

    # add value for favorites and retweets
    if tweet['retweet_count']:
        points += log(tweet['retweet_count'], 10)
    if tweet['favorite_count']:
        points += log(tweet['favorite_count'], 10)

    # add value for sharing media
    if 'media' in tweet:
        points += 1.5

    # uprank for tweets with hashtags shared by 25% of the other tweets in the cache
    for tag in tags:
        cached_tags = []
        for taglist in cache.inspect_values('hashtags'):
            for tag in taglist:
                cached_tags.append(tag['text'])
        if len(re.findall(tag, ' '.join(cached_tags)))/float(len(cached_tags)) > 0.25:
            points += 1

    # highly devalue @replies
    if re.match(r'@', tweet['text']):
        points -= 5

    # devalue tweets by users already in the cache (no livetweeting)
    if tweet['user']['screen_name'] in cache.inspect_value('user', 'screen_name'):
        points -= 1.5

    # devalue every @mention past 1 (they indicate the tweet is for those peoples' benefit, not ours)
    mentions = len(re.findall(r'@', tweet['text']))
    if mentions > 1:
        points -= (mentions * 0.75)

    # devalue swearwords because god forbid we offend somebody
    # proof of concept - this could either get way more complex or removed entirely
    # because in theory we trust the people we're following to not be jerks
    if re.search(r'(fuck|\bass(hole)?|shit|bitch)', tweet['text'].lower()):
        points -= 2

    # downrank stupid hashtags
    for tag in tags:
        if re.match(r'yolo|omg|wtf|lol|some|sm|wow)', tag.lower()):
            points -= 1.5

    # downrank tweets the farther they are from the "sweet spot", 100chars long
    points -= abs(len(tweet['text'])-100)/float(100)

    return points


# average tweets per 100 seconds
def rate():
    elapsed = time() - start
    if elapsed < 300:
        return cache.len() / float(elapsed) * 100
    else:
        return cache.len() / float(cache_length) * 100


def main():
    twitter = Twitter(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))
    twitter_stream = TwitterStream(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))

    global cache
    cache = CacheContainer(cache_length)

    # for plot
    tweet_history = []
    rate_history = []
    events_history = []
    mpl.interactive(True)
    global start
    start = time()

    id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.filter(follow=id_string)

    for tweet in iterator:
        try:
            # tweet comes from someone in the list (not an RT of one of their tweets)
            if 'user' in tweet and tweet['user']['id_str'] in id_list:

                tweet_imp = importance(tweet)
                stream_rate = rate()

                if tweet_imp > stream_rate:
                    #debug printouts
                    print("Retweeting tweet with importance %.2f (current rate %.2f)") % (tweet_imp, stream_rate)
                    print(" -->  %s") % tweet['text'].encode('utf-8')

                    twitter.statuses.retweet(id=tweet['id'])
                else:
                    print("Not retweeting a tweet that scored %.2f (rate is %.2f)") % (tweet_imp, stream_rate)

                # cache the tweet whether it was worthy or not
                cache.add(tweet)

                # make pretty graphs
                tweet_history.append(tweet_imp)
                rate_history.append(stream_rate)
                events_history.append(time() - start)
                mpl.plot(events_history, tweet_history, "bo", events_history, rate_history, "r-")
                mpl.draw()
        except:
            print("ERROR: %s" % sys.exc_info()[0])  # DAMN THE TORPEDOES, FULL SPEED AHEAD

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cache.clear()
        mpl.close()
        print('Killed by user')
        #os.system('killall python')
