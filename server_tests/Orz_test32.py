# lambda scoping

x = 1
class A:
    x = 3
    print (lambda: x)()


class B:
    x = 5
    class C:
        print (lambda: x)()

class D:
    def f(self):
        x = 7
        print (lambda: x)()
        
D().f()
