#!/usr/bin/env python
import sys
import compiler
import traceback

from compiler.ast import *

import random

class InParen(object):
    def __init__(self,node):
        self.node = node
    def code(self):
        return '(' + self.node.code() + ')'

def progVars():
    var_prefixes=['temp','tmp','Temp','Tmp','t']
    var_prefixes += list(set([s.upper() for s in var_prefixes]))
    i = 0
    while True:
        prefix = random.choice(var_prefixes)
        yield '%s%d'%(prefix,i)
        i += 1


def randAdd(varList,varGen):
    left,l_inputs = randExpr(varList,varGen)
    right,r_inputs  = randExpr(varList,varGen)
    return Add((left,right)),l_inputs+r_inputs

def randUnarySub(varList,varGen):
    node,inputs = randExpr(varList,varGen)
    return UnarySub(node),inputs

def randVar(varList,varGen):
    return Name(random.choice(varList)), 0

def randConst(varList,varGen):
    return Const(random.randint(-(2**16),2**16)), 0

def getInput(varList,varGen):
    return CallFunc(Name('input'),[]), 1

def inParen(varList,varGen):
    node,inputs = randExpr(varList,varGen)
    return InParen(node),inputs

def randDiscard(varList,varGen):
    expr,inputs = randExpr(varList,varGen)
    return Discard(expr),inputs
    
def randExpr(varList,varGen):
    funcs = [randAdd,randUnarySub,randConst,getInput,inParen]
    if varList:
        funcs.append(randVar)
    func = random.choice(funcs)
    return func(varList,varGen)

def randVarAssign(varList,varGen):
    expr,inputs = randExpr(varList,varGen)
    var = random.choice([v.__str__ for v in varList]+[varGen.next])()
    if var not in varList:
        varList.append(var)
    return Assign([AssName(var,'OP_ASSIGN')],expr),inputs

def randPrint(varList,varGen):
    expr,inputs = randExpr(varList,varGen)
    return Printnl([expr],None),inputs

def randStmt(varList,varGen):
    func = random.choice([randVarAssign, randDiscard, randPrint])
    return func(varList,varGen)

def randProg(size):
    inputs = 0
    varList=[]
    
    global varGen
    
    varGen = progVars()
    statements = []
    for i in xrange(size):
        stmt,stmt_inputs = randStmt(varList,varGen)
        statements.append(stmt)
        inputs += stmt_inputs
    
    #print inputs,varList
    randInputs = [randConst(None,None)[0].value for i in xrange(inputs)]
    randcode = Module(None,Stmt(statements)).code()
    code = '#randomly generated p0 AST\n\n'+randcode
    var_print = '\n'.join(['print ' + v for v in varList])
    code += '\n#print all vars to ensure they are used at least once\n\n' +var_print
    return code,'\n'.join(map(str,randInputs))
    

from subprocess import Popen,PIPE
import compile

def test_compiler(size=10, count=-1):
    test_num = 0
    i = 0
    while i != count:
        prog,input_txt = randProg(size)
        f = open('out.py','w')
        f.write(prog)
        f.close()
        try:
            compile.gen_asm_file(prog,'out.s')
        except:
            print 'failed to compile'
            print 
            print prog
            print
            raise
        
        p = Popen('gcc -m32 out.s *.o -lm -o out.bin',shell=True,stdout=PIPE,stderr=PIPE)
        stdout,stderr = p.communicate()
        
        if p.returncode != 0:
            print 'Error compiling asm for'
            print
            print prog
            print
            print 'output from gcc'
            print stdout
            print stderr
            return
        
        py_interp = Popen(['python','out.py'],stdin=PIPE,stdout=PIPE,stderr=PIPE)
        py_stdout,py_stderr = py_interp.communicate(input_txt)
        
        asm_exec = Popen(['out.bin'],stdin=PIPE,stdout=PIPE,stderr=PIPE)
        asm_stdout,asm_stderr = asm_exec.communicate(input_txt)
        
        if py_stderr or asm_stderr:
            print 'Error: non-empty stderr'
            print 'python stderr:'
            print
            print py_stderr
            print
            print 'asm stderr:'
            print
            print asm_stderr
            return
        
        if py_stdout != asm_stdout:
            print 'test failed for'
            print
            print prog
            print
            print 'python:', repr(py_stdout)
            print
            print 'asm:', repr(asm_stdout)
            print
            test_out_name,input_out_name = write_test_to_disk(prog,input_txt)
            print 'prog written to',test_out_name
            print 'input written to',input_out_name
            print
            raw_input()
            
        else:
            print 'test passed'
#            test_out_name,input_out_name = write_test_to_disk(prog,input_txt)
#            print 'prog written to',test_out_name
#            print 'input written to',input_out_name
        i += 1
        
def write_test_to_disk(prog,input_txt):
    test_num = 0
    try:
        while True:
            test_out_name = 'test/test%d.py'%test_num
            f=open(test_out_name)
            f.close()
            test_num += 1
    except IOError:
        pass #IOError indicates file does not exist
    
    f=open(test_out_name,'w')
    f.write(prog)
    f.close()
    input_out_name = test_out_name.rstrip('py')+'in'
    f=open(input_out_name,'w')
    f.write(input_txt)
    f.close()
    return test_out_name,input_out_name

if __name__ == '__main__':
    count = 1
    size = 10
    
    if len(sys.argv) > 1:
        count = int(sys.argv[1])
    if len(sys.argv) > 2:
        size = int(sys.argv[2])

    test_compiler(size,count)
    
