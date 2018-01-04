from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import backtrader as bt



# Create a Stratey
class TestStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('trailpercent', 0.05)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):

        # Keep a reference to the "close" line in the data[0] dataseries
        self.dataclose = self.datas[0].close

        # To keep track of pending orders and buy price/commission
        self.order = None
        self.buyprice = None
        self.buycomm = None
        self.stop_order = None

        # Add a MovingAverageSimple indicator
        self.sma = bt.indicators.SimpleMovingAverage(
            self.datas[0], period=self.params.maperiod)

        # Indicators for the plotting show
        # bt.indicators.ExponentialMovingAverage(self.datas[0], period=25)
        # bt.indicators.WeightedMovingAverage(self.datas[0], period=25,
        #                                     subplot=True)
        # bt.indicators.StochasticSlow(self.datas[0])
        # bt.indicators.MACDHisto(self.datas[0])
        # rsi = bt.indicators.RSI(self.datas[0])
        # bt.indicators.SmoothedMovingAverage(rsi, period=10)
        # bt.indicators.ATR(self.datas[0], plot=False)

    def place_stop_loss_order(self,order):
        '''This will immediatelly place a stop loss order'''
        self.stop_order = self.sell(exectype=bt.Order.StopTrail, trailpercent=self.params.trailpercent)

        # print("Placing StopTrail order for {order}".format(order=order))
        self.log("Placing StopTrail order Ref: {order}".format(order=self.stop_order.ref))

    def notify_order(self, order):
        if order.status in [order.Submitted]:
            # self.log("Order accepted Ref: {ref}".format(ref=order.ref))
            return
        if order.status in [order.Accepted]:
            self.log("Order accepted Ref: {ref}".format(ref=order.ref))
            return

        # Check if an order has been completed
        # Attention: broker could reject order if not enougth cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED Ref: %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.ref,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
                self.place_stop_loss_order(order)
            else:  # Sell
                self.log('SELL EXECUTED Ref: %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.ref,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                if self.stop_order and self.stop_order.ref != order.ref:
                    self.cancel(self.stop_order)

            self.bar_executed = len(self)

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            self.log('Order Canceled Ref: {ref} {type}'.format(ref=order.ref, type=order.info))

        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order Margin/Rejected {ref}'.format(ref=order.ref))


        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        # Simply log the closing price of the series from the reference
        self.log('Close, %.2f' % (self.dataclose[0]))

        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if self.order:
            return

        # Check if we are in the market
        if not self.position:

            # Not yet ... we MIGHT BUY if ...
            if self.dataclose[0] > self.sma[0]:
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                # Keep track of the created order to avoid a 2nd order
                self.order = self.buy()

        # else:
        #     if self.dataclose[0] < self.sma[0]:
        #         # SELL, SELL, SELL!!! (with all possible default parameters)
        #         self.log('SELL CREATE, %.2f' % self.dataclose[0])
        #         if self.stop_order:
        #             self.cancel(self.stop_order)
        #         else:
        #             print("WARNING - no stop loss order and selling?")
        #         # Keep track of the created order to avoid a 2nd order
        #         self.order = self.sell()


