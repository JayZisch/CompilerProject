print (lambda x, y: x==y)(1, 2)

def f(a, b, c):
    print b
    print a
    print c
    return 1

b = 22
c = 1
a = 333

print f(c, b, a)

print (lambda: f)()(3,2,[])

a = [0]

print (lambda: a)() is []

print a
