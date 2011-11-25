#!/usr/bin/env python
import sys
import random

def get_code(prefix, count=6):
    
    variables = ['%s%d'%(prefix ,i) for i in range(6)]
    variables.reverse()
    
    lines=['%s = %d'%(variables[i],random.randint(0,(2**16))) for i in range(len(variables))]
    
    
#    lines.append('print '+' + '.join(variables))
    
    add_exprs = [str(-(i+1)) for i in range(len(variables)+1)]
    
#    add_exprs = add_exprs + variables
    
    inputs=[]
    for c in range(1,len(variables)):
        add_exprs.insert(random.randint(0,len(add_exprs)), random.choice(['input()','- input()']))
        inputs.append(repr(random.randint(0,2**10)))
    
    lines.append('print '+' + '.join(add_exprs))
    lines += ['print '+var for var in variables]
    
    return '\n'.join(lines),'\n'.join(inputs)
        
    
def write_code():
    
    var_prefix_roots=['t','temp','tmp','T','Temp','Tmp']#+[,'temporary','Temporary','t','var','Var','v','x','e','a','b']
#    var_prefix_roots += list(set([s.upper() for s in var_prefix_roots]))
    var_prefixes = list(var_prefix_roots)
    var_prefixes += ['_'+s for s in var_prefix_roots]
    var_prefixes += ['__'+s for s in var_prefix_roots]
    var_prefixes += [s+'_' for s in var_prefix_roots]
    var_prefixes += ['_'+s+'_' for s in var_prefix_roots]
    var_prefixes += ['__'+s+'_' for s in var_prefix_roots]
    var_prefixes += [s+'__' for s in var_prefix_roots]
    var_prefixes += ['_'+s+'__' for s in var_prefix_roots]
    var_prefixes += ['__'+s+'__' for s in var_prefix_roots]
    
    
    i = 0
    for prefix in var_prefixes:
        filename = 'test/test_tempvars%d.py'%i
        code,input_txt = get_code(prefix)
        f=open(filename,'w')
        f.write(code)
        f.close()
        
        f = open(filename.rstrip('py')+'in','w')
        f.write(input_txt)
        f.close()
        i+=1

def long_vars():
    lines = ['']
    lines += ['tmp0 = input()','tmp1=input()']
    for i in range(2,1000):
        lines += ['tmp%d = tmp%d +- tmp%d'%(i,i-1,i-2), 'print tmp%d'%i]
    lines += ['','']
    f=open('test/test_tempvar4.py','w')
    f.write('\n'.join(lines))
    f.close()
    f=open('test/test_tempvar4.in','w')
    f.write('1000\n707\n')
    f.close()
    
    
    
    lines = ['']
    lines += ['tmp0 = input()']
    for i in range(1,1000):
        lines += ['tmp%d = tmp%d'%(i,i-1)]
    lines += ['print tmp%d'%i]
    lines += ['','']
    f=open('test/test_tempvar5.py','w')
    f.write('\n'.join(lines))
    f.close()
    f=open('test/test_tempvar5.in','w')
    f.write('707\n')
    f.close()

if __name__ == '__main__':
    write_code()

