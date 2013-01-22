'''
    Created on Dec 22, 2012
    
    @author: Scott Pigman
    
    pycheck is a collection of tools for validating that your code does what you think it does. These
    tools are intended to be used during development and debugging. 
'''

from .proxy import type_proxy

__all__ = ['checked', 'type_proxy', 'TypeDeclarationViolation']

#TODO: how to specify that return type is a tuple of heterogeneous types?
# (probably with a special helper class)s

from pycheck.checked_helpers import TypeDeclarationViolation
if __debug__:
    import functools
    import inspect
    import sys
    from pycheck.checked_helpers import (check_args, check_kwds, check_return)
    from types import GeneratorType

    def checked(f): 
        '''
        checked is a function decorator that uses function annotations as type declarations
        and verifies that the function has been passed, and is returning, the 
        correct types of values. 
        
        Yes, yes, I know, this is python and we're not supposed to have to have
        type checking. Before you pound your keyboard angrily telling me what an
        idiot I am, please at least read the "Motivation" section below. Thank you.
                
        SAMPLE USAGE:
        ------------
        
            @checked
            def function(parameter:<type declaration>) -> <type declaration>
                ....
                
        "function" may be a function, a method, or a generator*. 
        
            * For generators the actual return type is type <generator> however 
              @checked will check that the values yielded by the generator are 
              of the specified type.
                
        <type declaration> may be any of the following:
        
            * a class or type object (int, str, MyClass, etc.)
              
              Example: 
                  ``def f( x:int ): # f() only accepts int``

            * A tuple (or any iterable) of type objects, indicating that the value may be an instance of 
              any of those types.
              
              Example: 
                  ``def f( x: (int, str) ): # f() must return a str OR None``

            * The literal None, to indicate that only None is an acceptable value
              (usually used for declaring that a function does not return a value)
              
              Example: 
                  ``def f( x ) -> None: # f() has no return value``

            * A tuple (or any other iterable) containing type objects and the value None, indicating that
              the value may be any of the indicated types or the special value None.
              
              Example: 
                  ``def f( x ) -> (str, None) # f() must return a str or None``

            * Dict (or other mapping type) object which maps a collection type to an element type, 
              {<collection type> : <element type>}.
              
              This usage means that the function ruturns a collection of type <collection type> 
              (e.g. set, list, tuple, etc.), which contains only elements of type <element type>.
              
              Example: 
                  ``def f(x) -> {set:int}: # f() must return a set of integers``

            * A callable object which accepts one parameter and returns true or false. The callable 
              object is treated as a pre-condition when annotating function parameters and a 
              post-condition when annotating the return value. The value passed or returned will be 
              passed to the callable and an error will be raised if the result is not true. 
              
              Example 
                  ``def f( x: lambda x: x > 0 ): # f() only accepting values greater than zero``
                  
                  ``def g(x) -> lambda y: y >= 0: # g() must return a value >= 0``
        
        
        DEFAULTS, *ARG, AND **KWD
        --------------------------------------
        Parameters with default values, as well as *arg and **kwd arguments can also have
        their types declared:
            
            @checked
            def function(x:<type declaration>, y:<type declaration>=1, *args:<type declaration>, **kwds:<type declaration):
        
        
        DEBUG MODE:
        -----------------------------
        @checked is intended to be used as a tool during 
        development and testing to help identify errors more quickly. For
        this reason ``@checked`` is only functional in debug mode
        (i.e. when ``__debug__ == True``). If not in debug mode it is defined
        simply as,
        
            def checked(f):
                return f
                
        
        MOTIVATION:
        -----------
        The original motivation for this function was my attempt to apply the excercises outlined in Ben Nadel's whitepaper, 
        "Object Calisthenics" (http://www.bennadel.com/resources/uploads/2012/ObjectCalisthenics.pdf). 
        
        One of Nadel's excercises is to, "wrap all primitives and Strings." What he means is that instead of passing simple
        ints, floats, and strings to a function, you'd create simple subclasses of int, float and str to represent the
        type of data the parameter actually represents and to protect you from accidently passing an integer that
        represents Hours to a function that is intended to work with dollar ammounts, for example. 
        
        Of course, Nadel wrote his paper with Java in mind, so the java compiler would actually catch an error like that. 
        In attempting to apply that recommendation to python something was needed in order implement type checking. 
        Not finding a suitable package after an exhaustive five minute search of the internet I decided to try to 
        implement my one on my own (okay, I really wanted to see if I could do it or not).
        
        
        LIMITATIONS
        -----------
        *  there's currently no way to verify if the default value specified for a parameter violates the 
           type declaration for that parameter.
                Example:
                    def f( x:int="bad default value" ):
                        ....
              
              Hopefully the fact that the type declaration is RIGHT THERE IN FRONT OF YOU will be enough to 
              get you to use the right type. 
              
              This actually has at least one legitamate use, actually, in the case where the default value
              is a magic value (typically None) which indicates that the user didn't supply a value:
                  
                  def f( x:int=None )
                      # user is never intended to specify a value of None. User is expected 
                      # to either supply an int or no value at all.
                      
                      if x is None:
                          ...do something special...
            
        * If the annotations are callable objects, they can only operate on a single parameter, or the return,
          value. The validation cannot evaluate all of the parameters -- for example you can't write a
          pre-condition that checks that the parameters are ordered from least to greatest.
        
        
        KNOWN ISSUES:
        -------------
        Although an error is raised as it should be, the text of the error message for a container containing and 
        element of the wrong type is not clear
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
            
                if isinstance(rvalue, GeneratorType):
                    def checked_gen():
                        for value in rvalue:
                            yield check_return(f, value, argspec)
                    return checked_gen()
                else:
                    return check_return(f, rvalue, argspec) 
            except TypeDeclarationViolation as e:
                raise TypeDeclarationViolation(str(e)) from (None if sys.version >= '3.3' else e)
            
        return checked_f

else:
    def checked(f):
        return f
