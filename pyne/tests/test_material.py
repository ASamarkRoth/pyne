"""Material tests"""

from unittest import TestCase
import nose 

from nose.tools import assert_equal, assert_not_equal, assert_raises, raises, \
    assert_almost_equal, assert_true, assert_false

import os
from pyne.material import Material
import numpy  as np
import tables as tb


nucvec = {10010:  1.0,   
          80160:  1.0,   
          691690: 1.0,
          922350: 1.0,
          922380: 1.0,
          942390: 1.0,
          942410: 1.0,
          952420: 1.0,
          962440: 1.0,
          }

leu = {922380: 0.96, 922350: 0.04}


def make_mat_txt():
    """Helper for mat.txt"""
    with open('mat.txt', 'w') as f:
        f.write('U235  0.05\nU238  0.95')


def make_mat_h5():
    """Helper for mat.h5"""
    f = tb.openFile("mat.h5", "w")
    f.createGroup("/", "mat", "Mass Material Test")
    f.createArray("/mat", "Mass",  np.array([1.0, 0.5,  0.0]), "Mass Test")
    f.createArray("/mat", "U235",  np.array([1.0, 0.75, 0.0]), "U235 Test")
    f.createArray("/mat", "PU239", np.array([0.0, 0.25, 0.0]), "PU239 Test")
    f.close()


class TestMaterialConstructor(TestCase):
    "Tests that the Material constructors works."

    def test_mat1(self):
        mat = Material("mat.txt")
        assert_equal(mat.comp, {922350: 0.05, 922380: 0.95})
        assert_equal(mat.mass, 1.0)
        assert_equal(mat.name, '')

    def test_mat2(self):
        mat = Material("mat.txt", 42)
        assert_equal(mat.comp, {922350: 0.05, 922380: 0.95})
        assert_equal(mat.mass, 42.0)
        assert_equal(mat.name, '')

    def test_mat3(self):
        mat = Material("mat.txt", -42, "My Material")
        assert_equal(mat.comp, {922350: 0.05, 922380: 0.95})
        assert_equal(mat.mass, 1.0)
        assert_equal(mat.name, 'My Material')

    def test_mat4(self):
        mat = Material({922350: 0.05, 922380: 0.95}, 15, "Dict Try")
        assert_equal(mat.comp, {922350: 0.05, 922380: 0.95})
        assert_equal(mat.mass, 15.0)
        assert_equal(mat.name, 'Dict Try')

    def test_load_from_hdf5(self):
        #perform tests
        mat = Material()
        mat.load_from_hdf5("mat.h5", "/mat")
        assert_equal(mat.mass, 0.0)
        assert_equal(mat.comp, {922350: 0.0, 942390: 0.0})

        mat.load_from_hdf5("mat.h5", "/mat", 0)
        assert_equal(mat.mass, 1.0)
        assert_equal(mat.comp, {922350: 1.0, 942390: 0.0})

        mat.load_from_hdf5("mat.h5", "/mat", 1)
        assert_equal(mat.mass, 0.5)
        assert_equal(mat.comp, {922350: 0.75, 942390: 0.25})

        mat.load_from_hdf5("mat.h5", "/mat", 2)
        assert_equal(mat.mass, 0.0)
        assert_equal(mat.comp, {922350: 0.0, 942390: 0.0})

        mat.load_from_hdf5("mat.h5", "/mat", -1)
        assert_equal(mat.mass, 0.0)
        assert_equal(mat.comp, {922350: 0.0, 942390: 0.0})

        mat.load_from_hdf5("mat.h5", "/mat", -2)
        assert_equal(mat.mass, 0.5)
        assert_equal(mat.comp, {922350: 0.75, 942390: 0.25})

        mat.load_from_hdf5("mat.h5", "/mat", -3)
        assert_equal(mat.mass, 1.0)
        assert_equal(mat.comp, {922350: 1.0, 942390: 0.0})


    def test_load_from_text(self):
        mat = Material()
        mat.load_from_text("mat.txt")
        assert_equal(mat.comp, {922350: 0.05, 922380: 0.95})



class TestMaterialMethods(TestCase):
    "Tests that the Material member functions work."

    def test_normalize(self):
        mat = Material({922350: 0.05, 922380: 0.95}, 15)
        mat.normalize()
        assert_equal(mat.mass, 1.0)


    def test_mult_by_mass(self):
        mat = Material({922350: 0.05, 922380: 0.95}, 15)
        nucvec = mat.mult_by_mass()
        assert_equal(nucvec, {922350: 0.75, 922380: 14.25})


    def test_atomic_weight(self):
        mat_empty = Material({})
        assert_equal(mat_empty.atomic_weight(), 0.0)

        mat_u238 = Material({922380: 1.0})
        assert_equal(mat_u238.atomic_weight(), 238.0)

        mat_mixed = Material({922350: 0.5, 922380: 0.5})
        assert_almost_equal(mat_mixed.atomic_weight()/236.5, 1.0, 4)



class TestMassSubMaterialMethods(TestCase):
    "Tests that the Material sub-Material ter member functions work."

    def test_sub_mat_int_1(self):
        mat = Material(nucvec, -1, "Old Material")
        mat1 = mat.sub_mat([92, 80160])
        assert_almost_equal(mat1.comp[80160],  0.3333333333333)
        assert_almost_equal(mat1.comp[922350], 0.3333333333333)
        assert_almost_equal(mat1.comp[922380], 0.3333333333333)
        assert_equal(mat1.mass, 3.0)
        assert_equal(mat1.name, '')

    def test_sub_mat_int_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_mat([92, 80160], "New Material")
        assert_almost_equal(mat1.comp[80160],  0.3333333333333)
        assert_almost_equal(mat1.comp[922350], 0.3333333333333)
        assert_almost_equal(mat1.comp[922380], 0.3333333333333)
        assert_equal(mat1.mass, 3.0)
        assert_equal(mat1.name, 'New Material')

    def test_sub_mat_attr_1(self):
        mat = Material(nucvec, -1, "Old Material")
        mat1 = mat.sub_mat(["U", "80160", "H1"])
        assert_almost_equal(mat1.comp[10010],  0.25)
        assert_almost_equal(mat1.comp[80160],  0.25)
        assert_almost_equal(mat1.comp[922350], 0.25)
        assert_almost_equal(mat1.comp[922380], 0.25)
        assert_equal(mat1.mass, 4.0)
        assert_equal(mat1.name, '')

    def test_sub_mat_attr_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_mat(["U", "80160", "H1"], "New Material")
        assert_almost_equal(mat1.comp[10010],  0.25)
        assert_almost_equal(mat1.comp[80160],  0.25)
        assert_almost_equal(mat1.comp[922350], 0.25)
        assert_almost_equal(mat1.comp[922380], 0.25)
        assert_equal(mat1.mass, 4.0)
        assert_equal(mat1.name, 'New Material')

    def test_sub_u_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_u()
        assert_equal(mat1.comp, {922350: 0.5, 922380: 0.5})
        assert_equal(mat1.mass, 2.0)
        assert_equal(mat1.name, '')

    def test_sub_u_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_u("U Material")
        assert_equal(mat1.comp, {922350: 0.5, 922380: 0.5})
        assert_equal(mat1.mass, 2.0)
        assert_equal(mat1.name, 'U Material')

    def test_pu_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_pu()
        assert_equal(mat1.comp, {942390: 0.5, 942410: 0.5})
        assert_equal(mat1.mass, 2.0)
        assert_equal(mat1.name, '')

    def test_pu_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_pu("PU Material")
        assert_equal(mat1.comp, {942390: 0.5, 942410: 0.5})
        assert_equal(mat1.mass, 2.0)
        assert_equal(mat1.name, 'PU Material')

    def test_lan_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_lan()
        assert_equal(mat1.comp, {691690: 1.0})
        assert_equal(mat1.mass, 1.0)
        assert_equal(mat1.name, '')

    def test_lan_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_lan("LAN Material")
        assert_equal(mat1.comp, {691690: 1.0})
        assert_equal(mat1.mass, 1.0)
        assert_equal(mat1.name, 'LAN Material')

    def test_act_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_act()
        assert_equal(mat1.comp[922350], 1.0/6.0)
        assert_equal(mat1.comp[922380], 1.0/6.0)
        assert_equal(mat1.comp[942390], 1.0/6.0)
        assert_equal(mat1.comp[942410], 1.0/6.0)
        assert_equal(mat1.comp[952420], 1.0/6.0)
        assert_equal(mat1.comp[962440], 1.0/6.0)
        assert_equal(mat1.mass, 6.0)
        assert_equal(mat1.name, '')

    def test_act_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_act("ACT Material")
        assert_equal(mat1.comp[922350], 1.0/6.0)
        assert_equal(mat1.comp[922380], 1.0/6.0)
        assert_equal(mat1.comp[942390], 1.0/6.0)
        assert_equal(mat1.comp[942410], 1.0/6.0)
        assert_equal(mat1.comp[952420], 1.0/6.0)
        assert_equal(mat1.comp[962440], 1.0/6.0)
        assert_equal(mat1.mass, 6.0)
        assert_equal(mat1.name, 'ACT Material')

    def test_tru_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_tru()
        assert_equal(mat1.comp[942390], 1.0/4.0)
        assert_equal(mat1.comp[942410], 1.0/4.0)
        assert_equal(mat1.comp[952420], 1.0/4.0)
        assert_equal(mat1.comp[962440], 1.0/4.0)
        assert_equal(mat1.mass, 4.0)
        assert_equal(mat1.name, '')

    def test_tru_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_tru("TRU Material")
        assert_equal(mat1.comp[942390], 1.0/4.0)
        assert_equal(mat1.comp[942410], 1.0/4.0)
        assert_equal(mat1.comp[952420], 1.0/4.0)
        assert_equal(mat1.comp[962440], 1.0/4.0)
        assert_equal(mat1.mass, 4.0)
        assert_equal(mat1.name, 'TRU Material')

    def test_ma_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_ma()
        assert_equal(mat1.comp[952420], 1.0/2.0)
        assert_equal(mat1.comp[962440], 1.0/2.0)
        assert_equal(mat1.mass, 2.0)
        assert_equal(mat1.name, '')

    def test_ma_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_ma("MA Material")
        assert_equal(mat1.comp[952420], 1.0/2.0)
        assert_equal(mat1.comp[962440], 1.0/2.0)
        assert_equal(mat1.mass, 2.0)
        assert_equal(mat1.name, 'MA Material')

    def test_fp_1(self):
        mat = Material(nucvec)
        mat1 = mat.sub_fp()
        assert_equal(mat1.comp[10010],  1.0/3.0)
        assert_equal(mat1.comp[80160],  1.0/3.0)
        assert_equal(mat1.comp[691690], 1.0/3.0)
        assert_equal(mat1.mass, 3.0)
        assert_equal(mat1.name, '')

    def test_fp_2(self):
        mat = Material(nucvec)
        mat1 = mat.sub_fp("FP Material")
        assert_equal(mat1.comp[10010],  1.0/3.0)
        assert_equal(mat1.comp[80160],  1.0/3.0)
        assert_equal(mat1.comp[691690], 1.0/3.0)
        assert_equal(mat1.mass, 3.0)
        assert_equal(mat1.name, 'FP Material')


    def test_sub_range(self):
        mat = Material(nucvec)
        mat1 = mat.sub_range(920000, 930000)
        assert_equal(mat1.mass, 2.0)
        for nuc in mat1:
            assert_true(920000 <= nuc < 930000)

        mat1 = mat.sub_range(upper="U238")
        assert_equal(mat1.mass, 4.0)
        for nuc in mat1:
            assert_true(nuc < 922380)

        
class TestMaterialOperatorOverloading(TestCase):
    "Tests that the Material operator overloads work."
    u235 = Material({922350: 1.0})
    u238 = Material({922380: 1.0})

    def test_add_num(self):
        mat = self.u235 + 30.0
        assert_equal(mat.mass, 31.0)

    def test_radd_num(self):
        mat = 90 + self.u235
        assert_equal(mat.mass, 91.0)

    def test_add_mat(self):
        mat = self.u235 + self.u238
        assert_equal(mat.comp, {922350: 0.5, 922380: 0.5})
        assert_equal(mat.mass, 2.0)
        assert_equal(mat.name, '')

    def test_mul_num(self):
        mat = self.u235 * 2.0
        assert_equal(mat.mass, 2.0)

    def test_rmul_num(self):
        mat = 150 * self.u235
        assert_equal(mat.mass, 150.0)

    def test_div_num(self):
        mat = self.u235 / 10
        assert_equal(mat.mass, 0.1)


#
# Test mapping functions
#

def test_len():
    mat = Material(nucvec)
    assert_equal(len(mat), 9)


def test_contains():
    mat = Material(nucvec)
    assert_true(10010 in mat)
    assert_true(922350 in mat)
    assert_false(92000 in mat)
    assert_raises(TypeError, lambda: 'word' in mat)


def test_getitem_int():
    mat = Material(nucvec)
    assert_equal(mat[922350], 1.0) 
    assert_raises(KeyError, lambda: mat[42]) 

    mat = Material(leu)
    assert_equal(mat[922350], 0.04) 
    assert_equal(mat[922380], 0.96) 
    assert_raises(KeyError, lambda: mat[922340]) 


def test_getitem_str():
    mat = Material(nucvec)
    assert_equal(mat['U235'], 1.0) 
    assert_raises(TypeError, lambda: mat['word']) 

    mat = Material(leu)
    assert_equal(mat['U235'], 0.04) 
    assert_equal(mat['U238'], 0.96) 
    assert_raises(KeyError, lambda: mat['U234']) 


def test_getitem_slice_int():
    mat = Material(nucvec)
    mat1 = mat[920000:930000] 
    assert_equal(mat1.mass, 2.0)
    for nuc in mat1:
        assert_true(920000 <= nuc < 930000)

    mat1 = mat[:922380]
    assert_equal(mat1.mass, 4.0)
    for nuc in mat1:
        assert_true(nuc < 922380)

    mat1 = mat[922350:]
    assert_equal(mat1.mass, 6.0)
    for nuc in mat1:
        assert_true(922350 <= nuc)


def test_getitem_slice_str():
    mat = Material(nucvec)
    mat1 = mat['U':'NP'] 
    assert_equal(mat1.mass, 2.0)
    for nuc in mat1:
        assert_true(920000 <= nuc < 930000)

    mat1 = mat[:'U238']
    assert_equal(mat1.mass, 4.0)
    for nuc in mat1:
        assert_true(nuc < 922380)

    mat1 = mat['U235':]
    assert_equal(mat1.mass, 6.0)
    for nuc in mat1:
        assert_true(922350 <= nuc)



def test_setitem_int():
    mat = Material(nucvec)
    assert_equal(mat.mass, 9.0)
    assert_equal(mat[922350], 1.0) 
    mat[922350] = 2.0
    assert_equal(mat.mass, 10.0)
    assert_equal(mat[922350], 2.0) 

    mat = Material(leu)
    assert_equal(mat.mass, 1.0)
    assert_equal(mat[922350], 0.04) 
    assert_equal(mat[922380], 0.96) 
    assert_raises(KeyError, lambda: mat[922340]) 
    mat[922340] = 17.0
    assert_equal(mat.mass, 18.0)
    assert_equal(mat[922340], 17.0) 
    assert_equal(mat[922350], 0.04) 
    assert_equal(mat[922380], 0.96) 



def test_setitem_str():
    mat = Material(nucvec)
    assert_equal(mat.mass, 9.0)
    assert_equal(mat[922350], 1.0) 
    mat['U235'] = 2.0
    assert_equal(mat.mass, 10.0)
    assert_equal(mat[922350], 2.0) 

    mat = Material(leu)
    assert_equal(mat.mass, 1.0)
    assert_equal(mat[922350], 0.04) 
    assert_equal(mat[922380], 0.96) 
    assert_raises(KeyError, lambda: mat[922340]) 
    mat['U234'] = 17.0
    assert_equal(mat.mass, 18.0)
    assert_equal(mat[922340], 17.0) 
    assert_equal(mat[922350], 0.04) 
    assert_equal(mat[922380], 0.96) 



def test_setitem_slice_int():
    mat = Material(nucvec)
    mat[920000:930000] = 42
    assert_equal(mat.mass, 91.0)
    assert_equal(mat[10010], 1.0)
    assert_equal(mat[922350], 42.0)
    assert_equal(mat[922380], 42.0)

    mat = Material(nucvec)
    mat[:922380] = 0.0
    assert_equal(mat.mass, 5.0)
    for nuc in mat:
        if (nuc < 922380):
            assert_equal(mat[nuc], 0.0)
        else:
            assert_equal(mat[nuc], 1.0)

    mat = Material(nucvec)
    mat[922350:] = 2
    assert_equal(mat.mass, 15.0)
    for nuc in mat:
        if (922350 <= nuc):
            assert_equal(mat[nuc], 2.0)
        else:
            assert_equal(mat[nuc], 1.0)



def test_setitem_slice_str():
    mat = Material(nucvec)
    mat['U':'Np'] = 42
    assert_equal(mat.mass, 91.0)
    assert_equal(mat[10010], 1.0)
    assert_equal(mat[922350], 42.0)
    assert_equal(mat[922380], 42.0)

    mat = Material(nucvec)
    mat[:'U238'] = 0.0
    assert_equal(mat.mass, 5.0)
    for nuc in mat:
        if (nuc < 922380):
            assert_equal(mat[nuc], 0.0)
        else:
            assert_equal(mat[nuc], 1.0)

    mat = Material(nucvec)
    mat['U235':] = 2
    assert_equal(mat.mass, 15.0)
    for nuc in mat:
        if (922350 <= nuc):
            assert_equal(mat[nuc], 2.0)
        else:
            assert_equal(mat[nuc], 1.0)


def test_delitem_int():
    mat = Material(nucvec)
    assert_equal(mat[922350], 1.0)
    del mat[922350]
    assert_raises(KeyError, lambda: mat[922350]) 

    mat = Material(leu)
    assert_equal(mat[922350], 0.04)
    del mat[922350]
    assert_equal(mat.mass, 0.96) 
    assert_equal(mat.comp[922380], 1.0) 
    assert_raises(KeyError, lambda: mat[922350]) 


def test_delitem_str():
    mat = Material(nucvec)
    assert_equal(mat[922350], 1.0)
    del mat['U235']
    assert_raises(KeyError, lambda: mat[922350]) 

    mat = Material(leu)
    assert_equal(mat[922350], 0.04)
    del mat['U235']
    assert_equal(mat.mass, 0.96) 
    assert_equal(mat.comp[922380], 1.0) 
    assert_raises(KeyError, lambda: mat[922350]) 


def test_delitem_slice_int():
    mat = Material(nucvec)
    del mat[920000:930000]
    assert_equal(mat.mass, 7.0)
    assert_equal(mat[10010], 1.0)
    assert_raises(KeyError, lambda: mat[922350]) 
    assert_raises(KeyError, lambda: mat[922380]) 

    mat = Material(nucvec)
    del mat[:922380]
    assert_equal(mat.mass, 5.0)
    for nuc in mat:
        if (nuc < 922380):
            assert_raises(KeyError, lambda: mat[nuc]) 
        else:
            assert_equal(mat[nuc], 1.0)

    mat = Material(nucvec)
    del mat[922350:]
    assert_equal(mat.mass, 3.0)
    for nuc in mat:
        if (922350 <= nuc):
            assert_raises(KeyError, lambda: mat[nuc]) 
        else:
            assert_equal(mat[nuc], 1.0)


def test_delitem_slice_str():
    mat = Material(nucvec)
    del mat['U':'Np']
    assert_equal(mat.mass, 7.0)
    assert_equal(mat[10010], 1.0)
    assert_raises(KeyError, lambda: mat[922350]) 
    assert_raises(KeyError, lambda: mat[922380]) 

    mat = Material(nucvec)
    del mat[:'U238']
    assert_equal(mat.mass, 5.0)
    for nuc in mat:
        if (nuc < 922380):
            assert_raises(KeyError, lambda: mat[nuc]) 
        else:
            assert_equal(mat[nuc], 1.0)

    mat = Material(nucvec)
    del mat['U235':]
    assert_equal(mat.mass, 3.0)
    for nuc in mat:
        if (922350 <= nuc):
            assert_raises(KeyError, lambda: mat[nuc]) 
        else:
            assert_equal(mat[nuc], 1.0)


def test_iter():
    mat = Material(nucvec)
    for nuc in mat:
        assert_equal(mat[nuc], 1.0)

    mat = Material(leu)
    keys = set([922350, 922380])
    values = set([0.04, 0.96])
    items = set([(922350, 0.04), (922380, 0.96)])

    assert_equal(set(mat.keys()), keys)
    assert_equal(set(mat.values()), values)
    assert_equal(set(mat.items()), items)


#
# Run as script
#
if __name__ == "__main__":
    nose.main()
