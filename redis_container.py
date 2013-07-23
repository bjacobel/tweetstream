import redis
import pickle


class RedisContainer:
    def __init__(self, timeout=300):
        self.r = redis.StrictRedis(host='localhost', port=6379, db=0)
        self.timeout = timeout

    # Inserts item into redis.
    # Item must have a unique 'id' property.
    def add(self, item):
        self.r.set("item:"+str(item['id']), pickle.dumps(item))
        self.r.expire("item:"+str(item['id']), self.timeout)

    # Returns the number of currently active entries.
    def size(self):
        return len(self.all())

    # Return all currently active entries.
    def all(self):
        all_objs = []
        for key in self.r.keys("item:*"):
            all_objs.append(pickle.loads(self.r.get(key)))
        return all_objs

    # Return the values for a key that all entries in the db possess
    # Optionally specity a subkey for deeper introspection
    def inspect_value(self, key, subkey=None):
        value_list = []
        if subkey:  # judgement call: check if subkey on every iteration, or write loop twice
            for obj in self.all():
                value_list.append(obj[key][subkey])
            return value_list
        for obj in self.all():
            value_list.append(obj[key])
        return value_list

    # Purge elements added to redis through this class.
    def clear(self):
        for item in self.all():
            self.r.delete(item)
