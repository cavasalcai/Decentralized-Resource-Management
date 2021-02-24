from operator import itemgetter as _itemgetter
from collections import namedtuple as _namedtuple
from math import sqrt as _sqrt
from itertools import product as _product
from numbers import Number as _Number
from IPython import embed
from itertools import groupby

_tuple = tuple


def check_fit(available_resources, task_resources):
    """ check if a task fits with available_resources. if it does, return the result upon available_resources"""
    resources_left = available_resources.copy()
    for resource in available_resources.keys():
        if task_resources.get(resource, False):
            if resources_left[resource] - task_resources[resource] >= 0:
                resources_left[resource] -= task_resources[resource]
            else:
                return False
    return resources_left


def make_vector(dimensionnames, typename='TaskResources'):
    '''
    Return TaskResources, an extended namedtuple that represents a container
    of N integer independent dimensions
    '''

    tmp = _namedtuple(typename, dimensionnames)
    _fields = tmp._fields

    class TaskResources(tmp):
        __doc__ = tmp.__doc__ + '\n\n' + make_vector.__doc__

        __slots__ = ()

        def __new__(_cls, *args0, **kwargs):
            a = []
            lenargs0 = len(args0)
            if lenargs0 > len(tmp._fields):
                raise ValueError('Got unexpected extra %d fields' %
                                 (lenargs0 - len(tmp._fields),))
            for i, name in enumerate(tmp._fields):
                if i < lenargs0:
                    a.append(args0[i])
                    if name in kwargs:
                        raise ValueError('Argument given twice: %r' % name)
                elif name in kwargs:
                    a.append(kwargs.pop(name))
                else:
                    raise ValueError('Missing field name: %r' % name)
            if kwargs:
                raise ValueError(
                    'Got unexpected field names: %r' % kwargs.keys())
            args = a
            if any(arg < 0 for arg in args):
                args = tuple(0 for arg in args)
            return _tuple.__new__(_cls, args)

        @classmethod
        def _make(cls, iterable, new=tuple.__new__, len=len):
            'Make a new TaskResources object from a sequence or iterable'
            args = tuple(iterable)
            if any(arg < 0 for arg in args):
                args = tuple(0 for arg in args)
            result = new(cls, args)
            if len(result) != len(cls._fields):
                raise TypeError('Expected %d arguments, got %d' % (len(cls._fields),
                                                                   len(result)))
            return result

        def range(_self, start, stop=None):
            '''
            range([start,] stop) -> itertools.product object
            Returns an iterator that generates the sizes in the range on demand as tuples.

            '''
            if stop is None:
                stop = start
                start = tuple(0 for i in _self)
            if len(_self) != len(start):
                raise TypeError('Expected %d elements in start, got %d' % (
                    len(_self), len(start)))
            if len(_self) != len(stop):
                raise TypeError('Expected %d elements in stop, got %d' % (
                    len(_self), len(stop)))
            return _product(*(range(mn, mx) for mn, mx in zip(start, stop)))

        __hash__ = _tuple.__hash__

        def __mul__(_self, y):
            'Return a new TaskResources object where corresponding elements are multiplied by y'
            if isinstance(y, _Number):
                return _self._make(x * y for x in _self)
            elif len(_self) == len(y):
                return _self._make(ex * ey for ex, ey in zip(_self, y))
            else:
                raise NotImplementedError('Expected a Number or a %d element tuple/list, got %r' % (
                    len(_self), y))

        def __truediv__(_self, y):
            'Return a new TaskResources object where corresponding elements are divided by y'
            if isinstance(y, _Number):
                return _self._make(x / y for x in _self)
            elif len(_self) == len(y):
                return _self._make(ex / ey for ex, ey in zip(_self, y))
            else:
                raise NotImplementedError('Expected a Number or a %d element tuple/list, got %r' % (
                    len(_self), y))

        def __repr__(self):
            return 'TaskResources(' + ', '.join('%r' % i for i in self) + ')'

        def __str__(self):
            return 'TaskResources(' + ', '.join('%s=%r' % i for i in zip(self._fields, self)) + ')'

        def __abs__(_self):
            'Return the sqrt of the sum of the squares of all elements'
            return _sqrt(sum(e * e for e in _self))

        def __add__(_self, y):
            'Return a new TaskResources object where corresponding elements are added'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return _self._make(x + y for x, y in zip(_self, y))

        def __radd__(_self, y):
            'Return a new TaskResources object where corresponding elements are added'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return _self._make(y + x for x, y in zip(_self, y))

        def __sub__(_self, y):
            'Return a new TaskResources object where corresponding elements are subtracted'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return _self._make(x - y for x, y in zip(_self, y))

        def __rsub__(_self, y):
            'Return a new TaskResources object where corresponding elements are subtracted'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return _self._make(y - x for x, y in zip(_self, y))

        def __eq__(_self, y):
            'Return true iff all fields of self == y'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return all(x == y for x, y in zip(_self, y))

        def __ne__(_self, y):
            'Return true iff any fields of self != y'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return any(x != y for x, y in zip(_self, y))

        def __gt__(_self, y):
            'Return true iff all fields of self >= y and at least one field is > its field in y'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            more = False
            for x, y in zip(_self, y):
                if x > y:
                    more = True
                if x < y:
                    break
            else:
                return more
            return False

        def __ge__(_self, y):
            'Return true iff all fields of self >= y'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return all(x >= y for x, y in zip(_self, y))

        def __lt__(_self, y):
            'Return true iff all fields of self <= y and at least one field is < its field in y'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            more = False
            for x, y in zip(_self, y):
                if x < y:
                    more = True
                if x > y:
                    break
            else:
                return more
            return False

        def __le__(_self, y):
            'Return true iff all fields of self <= y'
            if len(_self) != len(y):
                raise TypeError('Expected %d arguments, got %d' %
                                (len(_self), len(y)))
            return all(x <= y for x, y in zip(_self, y))
    return TaskResources

