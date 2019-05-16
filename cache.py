class Cache:
    def __init__(self, size):

        # Class parameters
        self.__size = size
        self.__counter = {}
        self.__cache = {}

    def update(self, name, content, last_modified):
        if name in self.__counter:
            self.__counter[name] += 1
        else:
            self.__counter[name] = 1

        temp_cache = {}
        counter_sorted_keys = sorted(self.__counter, key=self.__counter.get, reverse=True)
        for i in range(self.__size):
            if len(self.__counter) <= i:
                break

            cache_name = counter_sorted_keys[i]
            if cache_name in self.__cache:
                temp_cache[cache_name] = self.__cache[cache_name]
            elif name == cache_name:
                temp_cache[cache_name] = {
                    "content": content,
                    "last_modified": last_modified
                }

        self.__cache = dict(temp_cache)

    def get(self, name):
        if name in self.__cache:
            return self.__cache[name]["content"], self.__cache[name]["last_modified"]
        return None, None
