#! /usr/local/bin/python

import sys
import compiler
from compiler.ast import *
from ir_x86 import *
from explicit import TypeCheckVisitor, PrintASTVisitor
from explicate1 import ExplicateVisitor
from flatten2 import FlattenVisitor2
from instruction_selection3 import InstrSelVisitor3
from register_alloc2 import RegisterAlloc2
from print_visitor2 import PrintVisitor2
from generate_x86_2 import GenX86Visitor2
from remove_structured_control import RemoveStructuredControl
from os.path import splitext
#from parse_p1 import yacc

debug = True

try:
    input_file_name = sys.argv[1]
    input_file = open(input_file_name)
    ast = compiler.parseFile(input_file_name)
#    ast = yacc.parse(input_file.read())
    if debug:
        print 'finished parsing'
        print ast

    ast = ExplicateVisitor().preorder(ast)
    if debug:
        print 'finished explicating'
        #print PrintASTVisitor().preorder(ast)
        print repr(ast)

    TypeCheckVisitor().preorder(ast)

    instrs = FlattenVisitor2().preorder(ast)
    if debug:
        print 'finished flattening'
        print PrintASTVisitor().preorder(instrs)
        print 'starting instruction selection'

    instrs = InstrSelVisitor3().preorder(instrs)
    if debug:
        print 'finished instruction selection'
        print PrintVisitor2().preorder(instrs)
        print 'starting register allocation'

    # Need to update the register allocator to handle the new instructions -JS
    instrs = RegisterAlloc2().allocate_registers(instrs, input_file_name)
    if debug:
        print 'finished register allocation'

    instrs = RemoveStructuredControl().preorder(instrs)

    # Need to update the x86 printer to handle the new instructions -JS
    x86 = GenX86Visitor2().preorder(instrs)
    if debug:
        print 'finished generating x86'

    asm_file = open(splitext(input_file_name)[0] + '.s', 'w')
    print >>asm_file, x86

except EOFError:
    print "Could not open file %s." % sys.argv[1]
except Exception, e:
    print e.args[0]
    exit(-1)

