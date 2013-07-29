from twitter import *
from myoauth import creds
from redis_container import RedisContainer
from Levenshtein import ratio
from math import log, sqrt
from time import time
import re

cache_length = 300

f = open('log.txt', 'w')


def importance(tweet):

    points = 0

    tags = []
    if 'hashtags' in tweet:
        for hashtag in tweet['hashtags']:
            tags.append(hashtag['tweet'])

    # add value for the tweet being itself a retweet
    if 'retweeted_status' in tweet:
        points += 1.5
        tweet = tweet['retweeted_status']
        f.write("+1.50 -- a retweet (really from @{})\n".format(tweet['user']['screen_name']))

    # add value based on the number of followers the person tweeting has over 1000
    points += log(tweet['user']['followers_count'], 10) - 3
    f.write("+{:.2f} -- followed by {:,}\n".format(log(tweet['user']['followers_count'], 10) - 3, tweet['user']['followers_count']))

    # add some value for being on peoples lists (people use lists, right?)
    points += sqrt(tweet['user']['listed_count']/float(5000))
    f.write("+{:.2f} -- listed by {:,}\n".format(sqrt(tweet['user']['listed_count']/float(5000)), tweet['user']['listed_count']))

    # add value for favorites and retweets
    if tweet['retweet_count']:
        points += log(tweet['retweet_count'], 10)
        f.write("+{:.2f} -- retweeted by {}\n".format(log(tweet['retweet_count'], 10), tweet['retweet_count']))
    if tweet['favorite_count']:
        points += log(tweet['favorite_count'], 10)
        f.write("+{:.2f} -- favorited by {}\n".format(log(tweet['favorite_count'], 10), tweet['favorite_count']))

    # add value for sharing media
    urls = ""
    if 'urls' in tweet:
        for url in tweet['urls']:
            urls += " ".join(url['display_url'])
    if 'media' in tweet or re.search(r'(vine|pic.twitter|twitpic|yfrog|instagr(am)?)', urls):
        points += 1.5
        f.write("+1.50 -- contains media\n")

    # uprank for tweets with hashtags shared by 25% of the other tweets in the cache
    for tag in tags:
        cached_tags = []
        for taglist in cache.inspect_value('hashtags'):
            for tag in taglist:
                cached_tags.append(tag['text'])
        if len(re.findall(tag, ' '.join(cached_tags)))/float(len(cached_tags)) > 0.25:
            points += 1
            f.write("+1.00 -- contains a popular hashtag\n")

    # highly devalue tweets that are suspected duplicates
    # uses Levenshtein edit distance
    for cached_tweet in cache.inspect_value('text'):
        if ratio(tweet['text'], cached_tweet) > 0.75:  # 75% similarity
            points -= 5
            f.write("-5.00 -- a suspected duplicate\n")

    # highly devalue @replies
    if re.match(r'@', tweet['text']):
        points -= 5
        f.write("-5.00 -- an @reply\n")

    # devalue tweets by users already in the cache (no livetweeting)
    if tweet['user']['screen_name'] in cache.inspect_value('user', 'screen_name'):
        points -= 1.5
        f.write("-1.50 -- from an author already in the cache\n")

    # devalue every @mention past 1 (they indicate the tweet is for those peoples' benefit, not ours)
    mentions = len(re.findall(r'@', tweet['text']))
    if mentions > 1:
        points -= ((mentions-1) * 0.75)
        f.write("-{:.2f} -- too @mention-y\n".format((mentions-1) * 0.75))

    # devalue swearwords because god forbid we offend somebody
    # proof of concept - this could either get way more complex or removed entirely
    # because in theory we trust the people we're following to not be jerks
    if re.search(r'(fuck|\bass(hole)?\b|shit|bitch)', tweet['text'].lower()):
        points -= 2
        f.write("-2.00 -- vulgar\n")

    # downrank stupid hashtags
    for tag in tags:
        if re.match(r'yolo|omg|wtf|lol|some|sm|wow|ff)', tag.lower()):
            points -= 1.5
            f.write("-1.50 -- stupid\n")

    # downrank tweets the farther they are from the "sweet spot", 100chars long
    points -= abs(len(tweet['text'])-100)/float(100)
    f.write("-{:.2f} -- too short/long.\n".format(abs(len(tweet['text'])-100)/float(100)))

    # borrowing heavily from https://github.com/tophtucker/tweetregs/

    # Public conversations that have nothing to do with you
    if re.match(r'\.@\w+\s+[A-Z]', tweet['text']):
        points -= 1.5
        f.write("-1.50 -- a needlessly public conversation\n")

    # retweet cascades
    if re.search(r'RT[^RT]+RT', tweet['text']):
        points -= 1.5
        f.write("-1.50 -- a retweet cascade\n")

    # Plaintive requests for follows, or 'Follow Friday'
    if re.search(r'(?i)please.*(\bwatch\b|\bfollow\b)|(\bwatch\b|\bfollow\b).*(me|please|back) | ^#?FF', tweet['text']):
        points -= 2
        f.write("-2.00 -- a request for attention\n")

    # the last rule of wire curator is you do not talk about wire curator
    if re.search(r'@wirecurator', tweet['text']):
        points -= 4
        f.write("-4.00 -- @wirecurator\n")

    return points


# average tweets per 100 seconds
def rate():
    elapsed = time() - start
    if elapsed < 300:
        return cache.size() / float(elapsed) * 100
    else:
        return cache.size() / float(cache_length) * 100


def main():
    twitter = Twitter(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))
    twitter_stream = TwitterStream(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))

    global cache
    cache = RedisContainer(cache_length)

    global start
    start = time()

    id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.filter(follow=id_string)

    drop = 0
    retweet = 0

    for tweet in iterator:
        try:
            # tweet comes from someone in the list (not an RT of one of their tweets)
            if 'user' in tweet and tweet['user']['id_str'] in id_list:
                f.write("\ntweet from {0}\n".format(tweet['user']['screen_name'].encode('utf-8')))
                f.write("{}\n".format(tweet['text'].encode('utf-8')))

                tweet_imp = importance(tweet)
                stream_rate = rate()

                f.write("------------------\n")
                if tweet_imp > stream_rate:
                    f.write("{:.2f} > current rate ({:.2f} tweets/100sec) : retweeting\n".format(tweet_imp, stream_rate))
                    f.write("That was retweet # {:,}\n".format(retweet))
                    retweet += 1
                    while not twitter.statuses.retweet(id=tweet['id']):
                        pass
                else:
                    f.write("{:.2f} < current rate ({:.2f} tweets/100sec) : dropping\n".format(tweet_imp, stream_rate))
                    f.write("That was drop # {:,}\n".format(drop))
                    drop += 1

                # cache the tweet whether it was worthy or not
                cache.add(dict(tweet))
        except:
            pass

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cache.clear()
