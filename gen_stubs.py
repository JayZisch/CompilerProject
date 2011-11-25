#!/usr/bin/env python

p0_nodes = []
p1_nodes = ['Compare', 'Or', 'And', 'Not', 'List', 'Dict', 'Subscript', 'IfExp']
p1_classes = ['GetTag', 'InjectFrom', 'ProjectTo', 'Let']
p2_nodes = ['Function','Lambda','Return']
p0_funcs = ['flatten','code','asm']
p1_funcs = ['explicate']
p2_funcs = ['boundvars']

args={}
args['flatten'] = ', tempGen'
args['explicate'] = ', tempGen'

def func_stubs(nodes=p2_nodes, funcs=p0_funcs+p1_funcs):
    stubs = ''
    for n in nodes:
        for f in funcs:
            stubs += "def %s_%s(self%s):\n    raise Exception('not implemented')\n\n"%(n.lower(), f, args.get(f,''))
        for f in funcs:
            stubs += '%s.%s = %s_%s\n'%(n,f,n.lower(),f)
        stubs += '\n\n'
    return stubs

def class_stubs(classes = p1_classes, funcs=p0_funcs+p1_funcs):
    stubs=''
    for c in classes:
        stubs += 'class %s(Node):\n'%c
        
        for f in funcs:
            stubs += "    def %s(self%s):\n        raise Exception('not implemented')\n    \n"%(f, args.get(f,''))
        stubs += '\n\n'
    return stubs

def stubs():
    return func_stubs()+class_stubs()


if __name__ == '__main__':
    pass
