class A:
    x = 1
    class B:
        x = 2
        class C:
            x = 3

print A.x
print A.B.x
print A.B.C.x
