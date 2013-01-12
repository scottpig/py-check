import importlib
import inspect


#===============================================================================
# type_proxy
#===============================================================================
def type_proxy(typename):
    """Proxy is used when an actual typename cannot be used becuase it is not yet
    defined in the namespace and cannot be -- typically because of circular
    references between types.
    
    Example:
        class A:
            @checked
            def foo(x) -> B : # Error: B not yet defined
                return x*x
                
        class B:
            @checked
            def bar(y) -> A : # if B is moved before A's definition then 
                return y**y   # the return type of B will not be defined.
            
    Solution:
        class A:
            @checked
            def foo(x) -> type_proxy("B") : # valid - invocation of B deferred until it is actually needed
                return x*x
            
        class B: # unchanged
            ...
    """
    class Proxy:
        stack = inspect.stack()
        
        # stack[0] is right here where inspect.stack() was called.
        # stack[1] is where the function type_proxy() calls the constructor of this class.
        # stack[2] is where in the code type_proxy() was actually called.
        f_globals = stack[2][0].f_globals

        def __new__(cls, *args, **kwds):
            modulename = cls.f_globals['__name__']
    
            module = importlib.import_module(modulename)
            
            the_type = getattr(module, typename)
            return the_type(*args, **kwds)
         
    return Proxy
    

if __name__ == '__main__':

    import unittest
    
    class A:
        pass    
    
    class TestCase(unittest.TestCase):
            
        def testMet1(self):

            PA = type_proxy('A') 
            pa = PA()
            a = A()
            
            print('Type(PA) = ',type(PA))
            print('Type(A) = ', type(A))
            print('type(pa) = ', type(pa))
            print('type(a) = ', type(a))
            self.assertTrue(isinstance(pa, A))
            self.assertTrue(type(a) == type(pa))

            self.assertTrue(issubclass(A, A))
            self.assertTrue(issubclass(PA, PA))

#            self.assertTrue(isinstance(a, PA))
#            self.assertTrue(issubclass(PA, A))
#            self.assertTrue(issubclass(A, PA))


    unittest.main()
    