def f(x,c):
    p = 8
    return lambda j: j + x + c + p

p = 19

print f(3,4)(7)
