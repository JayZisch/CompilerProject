def f():
    x = 1
    g = (lambda: x)
    x = 2
    return g

print f()()

