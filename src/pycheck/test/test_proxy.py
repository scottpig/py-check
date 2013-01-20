'''
Created on Jan 12, 2013

@author: dev
'''
import unittest
from pycheck import type_proxy


class A:
    pass    

class TestCase(unittest.TestCase):
        
    def test_main(self):

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

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()