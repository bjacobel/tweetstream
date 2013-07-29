from twitter import *
from myoauth import creds
from redis_container import RedisContainer
from time import time
import requests
import re
import sys


cache_length = 900  # 15 minutes


def parse_links(tweet):
    # regex to match shortened URLs, god help me if this actually works
    parsed_links = []
    if tweet['text']:
        text = tweet['text'].encode('utf-8')
        # every properly formed link on twitter is shortened to t.co on the backend already, so matching other domains is unnecesary
        links = re.findall(r'http:\/\/t\.co\/\w{10}', text)
        for link in links:
            try:
                r = requests.get(link, timeout=1.5)
            except requests.exceptions.Timeout:
                print("Exception: Redirect timed out.")
            except requests.HTTPError:
                print("Exception: a wild HTTPError appeared!")
            except:
                raise
            if r.status_code == 200 and r.url not in parsed_links:
                parsed_links.append(r.url)
    return parsed_links


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

    id_list = [str(line.strip()) for line in open("ids.txt").readlines()]
    id_string = ','.join(id_list)

    iterator = twitter_stream.statuses.filter(follow=id_string)

    try:
        for tweet in iterator:
            try:
                # tweet comes from someone in the list (not an RT of one of their tweets)
                if 'user' in tweet and tweet['user']['id_str'] in id_list:
                    links = parse_links(tweet)
                    if links:
                        print(links)
            except KeyboardInterrupt:
                raise
            except:
                pass
    except socket.error:
        print("Twitter hiccuped.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        cache.clear()
        sys.exit("Terminated with CTRL-C")
