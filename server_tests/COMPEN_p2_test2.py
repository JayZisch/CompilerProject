x = [lambda x,y: x+y, lambda : mult, lambda x,y: x+-y]

def mult(x,y):
    return x + mult(x,y+-1) if y != 0 else 0

print x[0](2,3)
print x[1]()(2,3)
print x[2](2,3)

print x[0](9,1) ==  10
