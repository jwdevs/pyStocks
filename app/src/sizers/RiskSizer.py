#!/usr/bin/env python
# -*- coding: utf-8; py-indent-offset:4 -*-
###############################################################################
#
# Copyright (C) 2015, 2016 Daniel Rodriguez
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import backtrader as bt
import math

class RiskSizer(bt.Sizer):
    '''This takes into account the total risk of the capital for a given transaction
    '''
    params = (
        ('total_percentage_risk', 0.01), #One percent risk of total capital per transaction
        ('stop_loss_percentage' ,0.25) #Stop loss percentage
    )

    def __init__(self):
        super().__init__()
        pass

    def _getsizing(self, comminfo, cash, data, isbuy):
        print("RiskSizer: Getting position size start")
        position = self.broker.getposition(data)
        if not position:
            size = self.calculatePosition(data)
        else:
            size = position.size

        return size

    def calculatePosition(self, data):
        totalValue = self.broker.getvalue()
        totalPermittedLoss = totalValue * self.p.total_percentage_risk
        perStockMaxLoss = data.close[0] * self.p.stop_loss_percentage
        positionSize = math.floor(totalPermittedLoss / perStockMaxLoss);
        print("RiskSizer: price={pr} totalValue={tv} totalPermittedLoss={tpl} perStockMaxLoss={psml} positionSize={ps}".format(pr=data.close[0],tv=totalValue,tpl=totalPermittedLoss,psml=perStockMaxLoss,ps=positionSize))
        return positionSize;