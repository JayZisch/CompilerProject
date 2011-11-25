f = lambda x: not x

g = lambda x: not f(x)

print True
print f(True)

def f(x, y):
    return True if x==y else False

def g(x, y):
    return False if x!=y else True

print f(1, 2)
print f(2, 2)

print g(True, True)
print g(False, True)

print f([]+[], [])
