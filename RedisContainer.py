import redis
import collections


class RedisTweet:
    def __init__(self, timeout=300):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.timeout = timeout

    # Inserts item into redis.
    # Item must have a unique 'id' property.
    def add(self, item):
        r.set("item:"+item['id'], item)
        r.hset("hash", item['id'], )

    # Returns the number of currently active entries.
    def len(self):
        return len(all())

    # Return all currently active entries.
    def all(self):

    # Return the values for a key that all entries in the db possess
    # Optionally specity a subkey for deeper introspection
    def inspect_value(self, key, subkey=None):
        

    # Purge elements added to redis through this class.
    def clear(self):
        for item in all():
            #delete item
