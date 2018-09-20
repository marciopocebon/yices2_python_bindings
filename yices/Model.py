import ctypes

from fractions import Fraction

import yices_api as yapi

from .UnderConstruction import UnderConstruction
from .Yvals import Yval
from .YicesException import YicesException


class Model(object):

    GEN_DEFAULT    = yapi.YICES_GEN_DEFAULT
    GEN_BY_SUBST   = yapi.YICES_GEN_BY_SUBST
    GEN_BY_PROJ    = yapi.YICES_GEN_BY_PROJ


    def __init__(self, model=None):
        self.model =  model


    @staticmethod
    def from_context(context, keep_subst):
        model = yapi.yices_get_model(context.context, keep_subst)
        if model == 0:
            raise YicesException('yices_get_model')
        return Model(model)


    @staticmethod
    def from_map(mapping):
        dom = mapping.keys()
        rng = [ mapping[d] for d in dom]
        model = yapi.yices_model_from_map(len(dom), yapi.make_term_array(dom), yapi.make_term_array(rng))
        if model == 0:
            raise YicesException('yices_model_from_map')
        return Model(model)


    def collect_defined_terms(self):
        defined_terms = yapi.term_vector_t()
        yapi.yices_init_term_vector(defined_terms)
        yapi.yices_model_collect_defined_terms(self.model, defined_terms)
        retval = []
        for i in range(0, defined_terms.size):
            retval.append(defined_terms.data[i])
        yapi.yices_delete_term_vector(defined_terms)
        return retval

    def dispose(self):
        assert self.model is not None
        yapi.yices_free_model(self.model)
        self.model = None


    def get_bool_value(self, term):
        ytval = ctypes.c_int32()
        errcode = yapi.yices_get_bool_value(self.model, term, ytval)
        if errcode == -1:
            raise YicesException('yices_get_bool_value')
        return True if ytval.value else False


    def get_integer_value(self, term):
        ytval = ctypes.c_int64()
        errcode = yapi.yices_get_int64_value(self.model, term, ytval)
        if errcode == -1:
            raise YicesException('yices_get_int64_value')
        return ytval.value

    def get_fraction_value(self, term):
        ytnum = ctypes.c_int64()
        ytden = ctypes.c_int64()
        errcode = yapi.yices_get_rational64_value(self.model, term, ytnum, ytden)
        if errcode == -1:
            raise YicesException('yices_get_rational64_value')
        return Fraction(ytnum.value, ytden.value)


    def get_float_value(self, term):
        ytval = ctypes.c_double()
        errcode = yapi.yices_get_double_value(self.model, term, ytval)
        if errcode == -1:
            raise YicesException('yices_get_double_value')
        return ytval.value

    def get_scalar_value(self, term):
        """ Returns the index of the value. This is the low level version, and does not use yapi.yices_constant. """
        ytval = ctypes.c_int32()
        errcode = yapi.yices_get_scalar_value(self.model, term, ytval)
        if errcode == -1:
            raise YicesException('yices_get_scalar_value')
        return ytval.value


    def formula_true_in_model(self, term):
        return True if yapi.yices_formula_true_in_model(self.model, term) == 1 else False

    def formulas_true_in_model(self, term_array):
        tarray = yapi.make_term_array(term_array)
        return True if yapi.yices_formulas_true_in_model(self.model, len(term_array), tarray) == 1 else False


    def get_value_from_rational_yval(self, yval):
        if yapi.yices_val_is_int64(self.model, yval):
            val = ctypes.c_int64()
            errcode = yapi.yices_val_get_int64(self.model,  yval, val)
            if errcode == -1:
                raise YicesException('yices_val_get_int64')
            return val.value
        elif yapi.yices_val_is_rational64(self.model, yval):
            ytnum = ctypes.c_int64()
            ytden = ctypes.c_int64()
            errcode = yapi.yices_val_get_rational64(self.model,  yval, ytnum, ytden)
            if errcode == -1:
                raise YicesException('yices_val_get_rational64')
            return Fraction(ytnum.value, ytden.value)
        else:
            val = ctypes.c_double()
            errcode = yapi.yices_val_get_double(self.model,  yval, val)
            if errcode == -1:
                raise YicesException('yices_val_get_double')
            return val.value

    def get_value_from_scalar_yval(self, yval):
        value = ctypes.c_int32()
        typev = ctypes.c_int32()
        errcode =  yapi.yices_val_get_scalar(self.model, yval, value, typev)
        if errcode == -1:
            raise YicesException('yices_val_get_scalar')
        return yapi.yices_constant(typev.value, value.value)

    def get_value_from_bv_yval(self, yval):
        bvsize = yapi.yices_val_bitsize(self.model, yval)
        if bvsize <= 0:
            return None
        bvarray = yapi.make_empty_int32_array(bvsize)
        errcode = yapi.yices_val_get_bv(self.model, yval, bvarray)
        if errcode == -1:
            raise YicesException('yices_val_get_bv')
        return [ bvarray[i] for i in range(0, bvsize) ]

    #FIXME: this problem is part of the gmp libpoly conundrum
    def get_value_from_algebraic_yval(self, yval):
        raise UnderConstruction("Haven't implemented this yet. Nag Ian.")

    def get_value_from_tuple_yval(self, yval):
        tuple_size = yapi.yices_val_tuple_arity(self.model, yval)
        if tuple_size <= 0:
            return None
        yval_array = yapi.make_empty_yval_array(tuple_size)
        errcode = yapi.yices_val_expand_tuple(self.model, yval, yval_array)
        if errcode == -1:
            raise YicesException('yices_val_expand_tuple')
        retval = [ Model.get_value_from_yval(self.model, yval_array[i]) for i in range(0, tuple_size) ]
        return tuple(retval)

    def get_value_from_mapping_yval(self, yval):
        mapping_size = yapi.yices_val_mapping_arity(self.model, yval)
        if mapping_size <= 0:
            return None
        ytgt = yapi.yval_t()
        ysrc = yapi.make_empty_yval_array(mapping_size)
        errcode = yapi.yices_val_expand_mapping(self.model, yval, ysrc, ytgt)
        if errcode == -1:
            raise YicesException('yices_val_expand_mapping')
        src = [Model.get_value_from_yval(self.model, ysrc[i]) for i in range(0, mapping_size) ]
        tgt = Model.get_value_from_yval(self.model, ytgt)
        return (tuple(src), tgt)

    def get_value_from_function_yval(self, yval):
        function_size = yapi.yices_val_function_arity(self.model, yval)
        if function_size <= 0:
            return None
        ydefault = yapi.yval_t()
        ymapping = yapi.yval_vector_t()
        yapi.yices_init_yval_vector(ymapping)
        errcode = yapi.yices_val_expand_function(self.model, yval, ydefault, ymapping)
        if errcode == -1:
            yapi.yices_delete_yval_vector(ymapping)
            raise YicesException('yices_val_expand_function')
        default = Model.get_value_from_yval(self.model, ydefault)
        mapping = [ Model.get_value_from_yval(self.model, ymapping.data[i]) for i in range(0, ymapping.size) ]
        dict_map = {}
        for (src, tgt) in mapping:
            dict_map[src] = tgt
        yapi.yices_delete_yval_vector(ymapping)
        def retfun(src):
            if src in dict_map:
                return dict_map[src]
            return default
        return retfun


    def get_value_from_yval(self, yval):
        tag = yval.node_tag

        if tag == Yval.RATIONAL:
            return self.get_value_from_rational_yval(yval)

        if tag == Yval.SCALAR:
            return self.get_value_from_scalar_yval(yval)

        if tag == Yval.BV:
            return self.get_value_from_bv_yval(yval)

        if tag == Yval.ALGEBRAIC:
            return self.get_value_from_algebraic_yval(yval)

        if tag == Yval.TUPLE:
            return self.get_value_from_tuple_yval(yval)

        if tag == Yval.MAPPING:
            return self.get_value_from_mapping_yval(yval)

        if tag == Yval.FUNCTION:
            return self.get_value_from_function_yval(yval)

        raise YicesException(msg='Model.get_value_from_yval: unexpected yval tag {0}\n'.format(tag))



    def get_value(self, term):

        yval = yapi.yval_t()
        errcode = yapi.yices_get_value(self.model, term, yval)
        if errcode == -1:
            raise YicesException('yices_get_value')
        return self.get_value_from_yval(yval)


    #yices tuples should be returned as python tuples

    #yices functions should be returned as closures (i.e functions)

    def get_value_as_term(self, term):
        return yapi.yices_get_value_as_term(self.model, term)

    def implicant_for_formula(self, term):
        retval = []
        termv = yapi.term_vector_t()
        yapi.yices_init_term_vector(termv)
        yapi.yices_implicant_for_formula(self.model, term, termv)
        retval = []
        for i in range(0, termv.size):
            retval.append(termv.data[i])
        yapi.yices_delete_term_vector(termv)
        return retval

    def implicant_for_formulas(self, term_array):
        tarray = yapi.make_term_array(term_array)
        termv = yapi.term_vector_t()
        yapi.yices_init_term_vector(termv)
        yapi.yices_implicant_for_formulas(self.model, len(term_array), tarray, termv)
        retval = []
        for i in range(0, termv.size):
            retval.append(termv.data[i])
        yapi.yices_delete_term_vector(termv)
        return retval

    def generalize_model(self, term, elim_array, mode):
        var_array = yapi.make_term_array(elim_array)
        termv = yapi.term_vector_t()
        yapi.yices_init_term_vector(termv)
        errcode = yapi.yices_generalize_model(self.model, term, len(elim_array), var_array, mode, termv)
        if errcode == -1:
            yapi.yices_delete_term_vector(termv)
            raise YicesException('yices_generalize_model')
        retval = []
        for i in range(0, termv.size):
            retval.append(termv.data[i])
        yapi.yices_delete_term_vector(termv)
        return retval

    def generalize_model_array(self, term_array, elim_array, mode):
        tarray = yapi.make_term_array(term_array)
        var_array = yapi.make_term_array(elim_array)
        termv = yapi.term_vector_t()
        yapi.yices_init_term_vector(termv)
        errcode = yapi.yices_generalize_model_array(self.model, len(term_array), tarray, len(elim_array), var_array, mode, termv)
        if errcode == -1:
            yapi.yices_delete_term_vector(termv)
            raise YicesException('yices_generalize_model_array')
        retval = []
        for i in range(0, termv.size):
            retval.append(termv.data[i])
        yapi.yices_delete_term_vector(termv)
        return retval
