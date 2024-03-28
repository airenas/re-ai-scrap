import hashlib
import json


def get_store(store, key):
    key = hashlib.md5(key.encode()).hexdigest()
    value = store.mget([key])
    if value[0]:
        return json.loads(value[0])
    return None


def set_store(store, key, value):
    key = hashlib.md5(key.encode()).hexdigest()
    store.mset([(key, json.dumps(value).encode())])
