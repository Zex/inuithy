import random, string
name = ''.join([random.choice(string.digits+string.ascii_letters) for i in range(6)])
print(name)
name = ''.join([random.choice(string.hexdigits) for i in range(4)])
print(name)
