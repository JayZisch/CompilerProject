# scoping
x = 1

class A():
    x = 3
    class B:
        print x


class C:
    x = 5
    class B:
        def f(self):
            print x

C.B().f()

class D:
    x = 7
    class E:
        class F:
            print x


class G:
    def f(self):
        x = 9
        class H:
            print x

G().f()


class I:
    x = 11
    def f(self):
        print x

I().f()
