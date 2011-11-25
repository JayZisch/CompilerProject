a = {(lambda: input())(): 1, 2: (lambda x, y, z: x if y else z)(1, 2, 3)}

print a[2]

print (lambda x: x) == (lambda y: y)

def div(a, b, c):
    return c if a==0 else div(a+(-b), b, c+1)

print div(6, 3, 0)
print div(81, 3, 0)
print div(121, 11, 0)
