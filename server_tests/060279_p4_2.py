class A:
    x = 4

class B:
    x = 0
    y = 2

class C(A, B):
    z = 3

print C.x  + C.y