class C:
    def __init__(o, n):
        print n

o = C(42)
o.x = 7

p = C(42)
p.x = 10

print o.x
print p.x

o.f = lambda n: n + n
print o.f(3)
