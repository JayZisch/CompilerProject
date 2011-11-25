print (lambda x: x)(1)

def f(y):
    return x + y

# redine function
def f(y):
    return x + y + 1


x = 10
print f(11)

def g(x):
    return lambda y: x+y

print g(1)(2)


x = [1, 2, 3]

(lambda: x)()[0] = x[2]
print x

def h():
    input()
    return x

h()[0] = input()

print x[0]
