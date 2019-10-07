import itertools
import numpy as np


class Detail:
    def __init__(self, a, b):
        if a > b:
            self.a = a
            self.b = b
        else:
            self.a = b
            self.b = a

    def __str__(self):
        return f'({self.a} x {self.b})'

    def __repr__(self):
        return str(self)

    def __mul__(self, other):
        if type(other) is int:
            return [self] * other


class Kit:
    def __init__(self, d):
        types = []
        for dtype in d:
            if dtype not in types:
                types.append(dtype)
        self.n = len(d)
        self.t = np.array(types)
        self.q = np.array([d.count(dtype) for dtype in types])

        # Building pick-map
        self.map = np.identity(len(self.t), dtype=int)
        for i in range(1, int(self.n / 2)):
            last_block = 0
            cur_block = len(self.t)
            for j in range(last_block, cur_block):
                for k in range(last_block, cur_block):
                    self.map = np.vstack([self.map, self.map[j] + self.map[k]])
        for i in range(len(self.map)):
            if (self.map[i] > self.q).any():
                self.map[i] = np.zeros((1, len(self.t)))
        self.map = np.unique(self.map, axis=0)

    def split(self, index):
        key = self.map[index]
        subset1 = np.dot(self.t, key)
        subset2 = np.dot(self.t, self.q - key)
        print(subset1)
        print(subset2)

    def iterate(self):
        for row in self.map:
            yield row, self.q - row

    def flat(self):
        return np.dot(self.t, self.q)

    def __str__(self):
        return self.flat()


class Vector:
    def __init__(self, *args):
        if args:
            assert len(args) == 2, "Wrong args"
            self.x = args[0]
            self.y = args[1]
        else:
            self.x = 0
            self.y = 0

    def __add__(self, other):
        return Vector(self.x + other.x, self.y + other.y)

    def __str__(self):
        return f'({self.x}, {self.y})'


class Instruction:
    def __init__(self, slice, first, second):
        """
        Slice is a number which represents an offset of the slice.
        It is positive in horizontal case and negative in vertical.
        If slice == 0, no slice needed.
        """
        self.slice = slice
        self.first = first
        self.second = second

    def slice2str(self, slice):
        direction = 'Horizontal' if slice > 0 else 'Vertical'
        return f'{direction} slice at {abs(slice)}'

    def report(self, level=0):
        tab = ' ' * 6
        if self.slice:
            dir1, dir2 = ('Bottom', 'Up') if self.slice > 0 else ('Left', 'Right')
            print(tab * level + self.slice2str(self.slice))

            print(tab * (level + 1) + dir1 + ' part:')
            self.first.report(level=level+2)

            print(tab * (level + 1) + dir2 + ' part:')
            self.second.report(level=level+2)
        else:
            print(tab * level + 'It is a detail!')
            print(tab * level + self.slice2str(self.first))
            print(tab * level + self.slice2str(self.second))


def diff(lst, sub):
    """
    :param lst: List
    :param sub: It's sublist
    :return: Their exact difference
    """
    result = []
    for i in lst:
        if i not in result:
            for j in range(lst.count(i) - sub.count(i)):
                result.append(i)
    return result


def R(D):
    """
    :param D: Collection of Details.
    :return: Generator of all possible splits into 2 sub-collections.
    """
    for left_size in range(1, int(len(D) / 2) + 1):
        for i in itertools.combinations(D, left_size):
            yield i, diff(D, i)


def f_vertical(x, D, C):
    """
    This is the same as function f(x, D), but it assumes that the first
    guillotine cut is vertical.
    """
    minimum = None
    slices = None
    for D1, D2 in R(D):
        for z in range(int(x/2)+1):
            left, l_slices = f(z, D1, C)
            point = C + Vector(z, 0)
            right, r_slices = f(x - z, D2, point)
            m = max(left, right)
            if not minimum or m < minimum:
                minimum = m
                slices = Instruction(-z, l_slices, r_slices)
    return minimum, slices


def f_horizontal(x, D, C):
    """
    This is the same as function f(x, D), but it assumes that the first
    guillotine cut is horizontal.
    """
    minimum = None
    slices = None
    for D1, D2 in R(D):
        bottom, b_slices = f(x, D1, C)
        point = C + Vector(0, bottom)
        top, t_slices = f(x, D2, point)
        m = bottom + top
        if not minimum or m < minimum:
            minimum = m
            slices = Instruction(bottom, b_slices, t_slices)
    return minimum, slices


def f(x, D, C):
    """
    :param x: Width of the strip.
    :param D: Collection of Details.
    :param C: Vector object - left-bottom point of the strip.
    :return: Minimum height (y) of the strip of width x, which is enough
    for guillotine allocation for collection D.
    """
    max_b = 0
    for detail in D:
        if detail.b > max_b:
            max_b = detail.b
    if max_b > x:
        return 100000, Instruction(None, None, None)
    elif len(D) == 1:
        if D[0].a <= x:
            first = -D[0].a
            second = D[0].b
            slices = Instruction(None, first, second)
            return D[0].b, slices
        else:
            first = D[0].b
            second = -D[0].a
            slices = Instruction(None, first, second)
            return D[0].a, slices
    else:
        vertical, v_slices = f_vertical(x, D, C)
        horizontal, h_slices = f_horizontal(x, D, C)
        # Finding minimum
        if vertical < horizontal:
            return vertical, v_slices
        else:
            return horizontal, h_slices
