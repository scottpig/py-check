'''
    Created on Dec 22, 2012
    
    @author: Scott Pigman
'''

from .proxy import type_proxy


#TODO: how to specify that return type is a tuple of heterogeneous types?
#TODO: How to specify generators that yield specific types of objects?

from pycheck.checked_helpers import TypeDeclarationViolation
if __debug__:
    import functools
    import inspect
    import sys
    from pycheck.checked_helpers import (check_args, check_kwds, 
                                         check_return)

    def checked(f): 
                                
        @functools.wraps(f)
        def checked_f(*args:list, **kwds:dict):  
            argspec = inspect.getfullargspec(f)
            
            try:          
                check_args(f, args, argspec)
                check_kwds(f, kwds, argspec)
            except TypeDeclarationViolation as e:
                raise TypeDeclarationViolation(str(e)) from (None if sys.version >= '3.3' else e)                
    
            # Since errors thrown here have to do with the actual implementation of the
            # checked function, f, we don't want to re-wrap any exceptions thrown
            # since they are actually caused by the user's code.
            rvalue = f(*args, **kwds)

            try:                
                return check_return(f, rvalue, argspec) 
            except TypeDeclarationViolation as e:
                raise TypeDeclarationViolation(str(e)) from (None if sys.version >= '3.3' else e)
            
        return checked_f

else:
    def checked(f):
        return f
