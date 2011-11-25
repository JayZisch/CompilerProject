class C:
    def move(o, dx):
        o.x = o.x + dx

o = C()
o.x = 40
o.move(2)
print o.x