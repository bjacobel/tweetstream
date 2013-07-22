import redis


class RedisContainer:
    def __init__(self, timeout=300):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.timeout = timeout

    # Inserts item into redis.
    # Item must have a unique 'id' property.
    def add(self, item):
        self.r.set("item:"+item['id'], item)
        self.r.expire("item:"+item['id'], self.timeout)
        self.r.hset("hash", item['id'], "item:"+item['id'])

    # Returns the number of currently active entries.
    def len(self):
        return len(all())

    # Return all currently active entries.
    def all(self):
        all_objs = []
        for key in self.r.keys("item:*"):
            all_objs.append(self.r.get("key"))

    # Return the values for a key that all entries in the db possess
    # Optionally specity a subkey for deeper introspection
    def inspect_value(self, key, subkey=None):
        pass

    # Purge elements added to redis through this class.
    def clear(self):
        for item in all():
            self.r.delete(item)
