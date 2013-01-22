'''
Created on Jan 8, 2013

@author: Scott Pigman
'''
#===============================================================================
# type_proxy
#===============================================================================
#def classProxy(classname, module='.'):
#    class ClassProxy(BusinessObject):
#        def __new__(self, *args, **kwds):
#            modname = __package__ + module if module.startswith('.') else module
#            mod = __import__(modname, fromlist=[classname], level=0) #@UnusedVariable -- Used in eval'd string.
#
#            return eval('%s%s(*%s, **%s)' % ('mod.' if module else '', classname, args, kwds))  
#    return ClassProxy  
import inspect
import importlib

def type_proxy(typename):
    """type_proxy(typename) is used when an actual typename cannot be used because 
    it is not yet defined in the namespace and cannot be. 
    
    The two typical causes are, 
    
    1. Using a class in an annotation of a method of that same class.
        Example:
            class A:
                @checked
                @classmethod
                def factory(cls, ...) -> A: # Error, when the annotation is processed, A has not yet been defined
                    ...
        Solution:
            class A:
                @checked
                @classmethod
                def factory(cls, ...) -> type_proxy('A') # valid
                    ...
                    
    2. Trying to create an annotation which refers to a class not yet defined, which itself uses an annotation
       that refers back to _this_ class (i.e. circular references). Because the two classes refer to each other
       the solution is not so simple as to just move the second class definition before the first.

        Example:
            class A:
                @checked
                def to_b(self) -> B : # Error: B not yet defined
                    return B(self)
                    
            class B:
                @checked
                def to_a(self) -> A : # A refers to B and B refers to A, so it doesn't matter
                    return A(self)    # which class is defined first, there's going to be an error.
                
        Solution:
            class A:
                @checked
                def to_b(self) -> type_proxy("B") : # Fixed
                    return B(self)
                    
            class B:
                ...unchanged...
    """
    
    class MetaProxy(type):
        
        stack = inspect.stack()
        def __init__(self, *args, **kwds):
            super().__init__(*args, **kwds)
            
            
            # stack[0] is right here where inspect.stack() was called.
            # stack[1] is where the function type_proxy() calls the constructor of this class.
            # stack[2] is where in the code type_proxy() was actually called.
            f_globals = self.stack[2][0].f_globals
            self.__modulename = f_globals['__name__']
                
        def __subclasscheck__(self, subclass):
            """
            Return true if subclass should be considered a (direct or indirect) subclass of class. 
            If defined, called to implement issubclass(subclass, class).
            """
            
    
            module = importlib.import_module(self.__modulename)
            
            the_type = getattr(module, typename)
            return issubclass(the_type, subclass)

        def __instancecheck__(self, instance):
            """
            Return true if instance should be considered a (direct or indirect) instance of class. 
            If defined, called to implement isinstance(instance, class).
            """
            module = importlib.import_module(self.__modulename)
            
            the_type = getattr(module, typename)
            return isinstance(instance, the_type)  
    
    class Proxy(metaclass=MetaProxy):
        stack = inspect.stack()

        def __new__(cls, *args, **kwds):
            
            
            # stack[0] is right here where inspect.stack() was called.
            # stack[1] is where 
            # stack[2] is where 
            f_globals = cls.stack[2][0].f_globals
            
            modulename = f_globals['__name__']
    
            module = importlib.import_module(modulename)
            
            the_type = getattr(module, typename)
            return the_type(*args, **kwds)
        
    return Proxy
    

    