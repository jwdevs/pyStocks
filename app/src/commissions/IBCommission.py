
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import math

class IBCommission(bt.CommInfoBase):
    params = (
        ('perstock', 0.005),
        ('minperorder', 1.0),
        ('maxpercent', 0.005),
    )

    def __init__(self):
        super().__init__()

    def getcommission(self, size, price):
        '''Calculates the commission of an operation at a given price
        '''

        maxComm = abs(size) * price * self.params.maxpercent
        comm = abs(size) * self.params.perstock
        # print("Size: {size} price: {price} Calculated: {com}, max: {max}, min: {min}".format(size=size, price=price, com=comm,max=maxComm, min=self.params.minperorder))

        return min(max(comm,self.params.minperorder),maxComm)