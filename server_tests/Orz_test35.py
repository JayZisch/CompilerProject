class A:
    x = 1

B = A

class A:
    A.x = 3

print B.x


class B:
    class C:
        x = 5
    C.x = 7

print B.C.x
