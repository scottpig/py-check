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
    from pycheck.checked_helpers import (check_args, check_kwds, check_return)

    def checked(f): 
        '''
        A function decorator that uses function annotations as type declarations
        and verifies that the function has been passed, and is returning, the 
        correct types of values. 
        
        This is intended to be used as a tool during 
        development and testing to help identify errors more quickly. For
        this reason ``@checked`` is only functional in debug mode
        (i.e. when ``__debug__ == True``). If not in debug mode it is defined
        simply as,
        
            def checked(f):
                return f
        
        Sample usage:
        
            @checked
            def function(parameter:<type declaration>) -> <type declaration>
                ....
                
        parameters with default values, as well as *arg and **kwd arguments can also have
        their types declared:
            
            @checked
            def function(x:<type declaration>, y:<type declaration>=1, *args:<type declaration>, **kwds:<type declaration):
                
        <type declaration> can be any of the following:
        
            * a class or type object (int, str, MyClass, etc.)
              Example: ``def f( x:int ): # function that only accepts int``

            * A tuple (or any iterable) of type objects, indicating that the value may be an instance of 
              any of those types.
              Example: ``def f( x: (int, str) ): # function that accepts int or str``

            * The literal None, to indicate that only None is an acceptable value
              (usually used for declaring that a function does not return a value)
              Example: ``def f( x ) -> None: # function returning only None``

            * A tuple (or any other iterable) containing type objects and the value None, indicating that
              the value may be any of the indicated types or the special value None.
              Example: ``def f( x ) -> (str, None) # function returning a str or None``

            * Dict (or other mapping type) object which maps a key type to value type, {keytype:valuetype}. 
              In this usage the
              key type is interpreted as a collection type (e.g. set, list, tuple, etc.) and the value   
              type is interpreted as the type of the contents. 
              Example: ``def f(x) -> {set:int}: # function returning a set of integers``

            * A callable object which accepts one parameter and returns true or false. The callable 
              object is treated as a pre-condition when annotating function parameters and a 
              post-condition when annotating the return value. The value passed or returned will be 
              passed to the callable and an error will be raised if the result is not true. 
              Example ``def f( x: lambda x: x > 0 ): # function only accepting values greater than zero``
        
        '''
                                
        @functools.wraps(f)
        def checked_f(*args:list, **kwds:dict):  
            argspec = inspect.getfullargspec(f)
            
            try:          
                check_args(f, args, argspec)
                check_kwds(f, kwds, argspec)
            except TypeDeclarationViolation as e:
                # It would be confusing to the user to see a big stack of our function calls
                # here in the stack trace when an error is detected, so if we're in 3.3 or higher
                # we supress the rest of our own stack trace by the "raise Exception from None"
                # technique.
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
