from twitter import Twitter, OAuth
from myoauth import creds

twitter = Twitter(auth=OAuth(creds['OAUTH_TOKEN'], creds['OAUTH_SECRET'], creds['CONSUMER_KEY'], creds['CONSUMER_SECRET']))

users = [line.strip() for line in open("users.txt").readlines()]
ids = open('ids.txt', 'w')

for user in users:
    id = str(twitter.users.lookup(screen_name=user)[0]['id'])
    print user + " has an ID of " + id
    ids.write(id + "\n")
