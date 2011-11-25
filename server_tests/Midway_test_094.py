x=1
z=2
def f():
    y=x
    def g():
        return lambda w: w + z + y
    return g()
print f()()(1)
