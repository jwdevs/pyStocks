from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import datetime  # For datetime objects
import os.path  # To manage paths
import sys  # To find out the script name (in argv[0])

import backtrader as bt



# Create a Strategy
class MultiStocksStrategy(bt.Strategy):
    params = (
        ('maperiod', 15),
        ('trailpercent', 0.05),
        ('sell_signal', True)
    )

    def log(self, txt, dt=None):
        ''' Logging function fot this strategy'''
        dt = dt or self.datas[0].datetime.date(0)
        print('%s, %s' % (dt.isoformat(), txt))

    def create_context(self,name):
        return {
                'name' : name,
                'order' : None,
                'stop_order': None,
                'buyprice' : None,
                'buycomm' : None,
                'data' : self.getdatabyname(name),
                'indicators' : self.create_indicators(name)
        }
    def create_indicators(self,name):
        return {
            'sma': bt.indicators.MovingAverageSimple(self.getdatabyname(name), period=self.params.maperiod),
        }

    def __init__(self):

        self.stocks = dict()
        names = self.getdatanames()

        for name in names:
            print('Adding data: {name}'.format(name=name))
            self.stocks[name]= self.create_context(name)


    def place_stop_loss_order(self,order,stock, context):
        '''This will immediatelly place a stop loss order'''
        stopLoss= self.sell(data=context['data'], exectype=bt.Order.StopTrail, trailpercent=self.params.trailpercent, parent=order, size=order.size)
        # print("Placing StopTrail order for {order}".format(order=order))
        self.log("Placing StopTrail Order Ref: {order} for stock: {name} ".format(order=stopLoss.ref, name=stock))
        return stopLoss

    def notify_order(self, order):
        # FIXME: not sure if this is supposed to be taken like that? We can always introduce a dictionary for this later.
        name = order.params.data.params.dataname
        context = self.stocks[name]

        self.log("Notify order: {ref} with status: {status} for stock: {name}".format(ref=order.ref,status=order.status,name=name))
        if order.status in [order.Submitted,order.Accepted]:
            # self.log("Order accepted Ref: {ref}".format(ref=order.ref))
            return


        # Check if an order has been completed
        # Attention: broker could reject order if not enough cash
        if order.status in [order.Completed]:
            if order.isbuy():
                self.log(
                    'BUY EXECUTED Ref: %s, Stock: %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                    (order.ref,
                     name,
                     order.executed.price,
                     order.executed.value,
                     order.executed.comm))

                # self.buyprice = order.executed.price
                # self.buycomm = order.executed.comm
                # self.place_stop_loss_order(order,stock,context)
            else:  # Sell
                self.log('SELL EXECUTED Ref: %s, Stock: %s, Price: %.2f, Cost: %.2f, Comm %.2f' %
                         (order.ref,
                          name,
                          order.executed.price,
                          order.executed.value,
                          order.executed.comm))
                if context['stop_order'] and context['stop_order'].ref != order.ref:
                    self.log('SIGNAL SELL ORDER EXECUTED Ref: {ref}, Stock: {stock}'.format(ref=order.ref, stock=name))
                    self.cancel(context['stop_order'])
                    context['stop_order'] = None
                elif context['stop_order'] and context['stop_order'].ref == order.ref:
                    self.log('STOP ORDER EXECUTED Ref: {ref}, Stock: {stock}'.format(ref=order.ref, stock=name))
                    context['stop_order'] = None

            # self.bar_executed = len(self)

        elif order.status in [order.Canceled]:
            self.log('Order Canceled Ref: {ref} {type}'.format(ref=order.ref, type=order.info))

        elif order.status in [order.Margin, order.Rejected]:
            self.log('Order Margin/Rejected {ref}'.format(ref=order.ref))

        context['order'] = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))


    def next_stock(self, name, context):
        self.log('####### Calculating {stock}: close price: {close} '.format(stock=name, close=context['data'][0]))

        position = self.getpositionsbyname()[name]
        # self.log('Stock: {name} position: {pos}'.format(name=name,pos=position))
        # Check if an order is pending ... if yes, we cannot send a 2nd one
        if context['order']:
            self.log('We have pending order for {name}'.format(name = name))
            return

        # Check if we are in the market
        if not position:
            self.log('No position for stock: {name}'.format(name=name))
            # # Not yet ... we MIGHT BUY if ...
            if self.should_buy(name, context):
                # BUY, BUY, BUY!!! (with all possible default parameters)
                self.log('BUY CREATE, Stock: {stock}, price: {price}'.format(stock=name, price=context['data'].close[0]))
                # Keep track of the created order to avoid a 2nd order
                context['order'] = self.buy(data=context['data'],transmit=False)
                #context['order'] = self.order_target_percent(data=context['data'], target=0.9/len(self.stocks), transmit=False)
                if context['order'] is not None:
                    self.log('Order ref: {ref} for stock: {name} created'.format(ref=context['order'].ref, name=name))
                    context['stop_order'] = self.place_stop_loss_order(context['order'],name,context)

        else:
           self.log("Has already a position for stock: {stock} position: {position}".format(stock=name,position=self.getpositionsbyname()[name]))
           if self.params.sell_signal and self.should_sell(name,context):
                # SELL, SELL, SELL!!! (with all possible default parameters)
                self.log('SELL CREATE, Stock: {stock}, price: {price}'.format(stock=name, price=context['data'].close[0]))
                # Keep track of the created order to avoid a 2nd order
                context['order'] = self.sell(data=context['data'], oco=context['stop_order'])

    def next(self):
        self.log('******** NEXT ********')
        for s,v in self.stocks.items():
            self.next_stock(s, v)


    def should_buy(self, name, context):
        return context['data'].close[0] > context['indicators']['sma'][0]

    def should_sell(self, name, context):
        return context['data'].close[0] < context['indicators']['sma'][0] and context['stop_order']


class MACDStrategy(MultiStocksStrategy):
    def create_indicators(self,name):
        macd = bt.indicators.MACD(self.getdatabyname(name))
        crossup = bt.indicators.CrossUp(macd.macd,macd.signal)
        crossdown = bt.indicators.CrossDown(macd.macd, macd.signal)
        return {
            'macd': macd,
            'buy' : crossup,
            'sell': crossdown
        }


    def should_buy(self, name, context):
        return context['indicators']['buy'][0]

    def should_sell(self, name, context):
        # return False
        return context['indicators']['sell'][0]

class PrettyGoodOscillatorStrategy(MultiStocksStrategy):
    def create_indicators(self,name):
        pgo = bt.indicators.PrettyGoodOscillator(self.getdatabyname(name))

        return {
            'pgo': pgo,
            'buy' : pgo >= 3,
            'sell': pgo <= 0.3
        }


    def should_buy(self, name, context):
        return context['indicators']['buy'][0]

    def should_sell(self, name, context):
        # return False
        return context['indicators']['sell'][0]

class DMAStrategy(MultiStocksStrategy):
    def create_indicators(self,name):
        dma = bt.indicators.DicksonMovingAverage(self.getdatabyname(name))
        buy = self.getdatabyname(name).close > dma
        sell = self.getdatabyname(name).close < dma
        return {
            'dma': dma,
            'buy' : buy,
            'sell': sell
        }


    def should_buy(self, name, context):
        return context['indicators']['buy'][0]

    def should_sell(self, name, context):
        # return False
        return context['indicators']['sell'][0]

class StochasticStrategy(MultiStocksStrategy):
    def create_indicators(self,name):
        stochastic = bt.indicators.Stochastic(self.getdatabyname(name))

        return {
            'st': stochastic,
            'buy' : bt.indicators.CrossUp(stochastic.percK,stochastic.percD),
            'sell': bt.indicators.CrossDown(stochastic.percK,stochastic.percD)
        }


    def should_buy(self, name, context):
        return context['indicators']['buy'][0]

    def should_sell(self, name, context):
        # return False
        return context['indicators']['sell'][0]

class StochasticEnhancedStrategy(MultiStocksStrategy):
    def create_indicators(self, name):
        stochastic = bt.indicators.Stochastic(self.getdatabyname(name))
        up = bt.indicators.UpMove(self.getdatabyname(name))
        upMove = up.upmove > 0
        buy = bt.And(bt.indicators.CrossUp(stochastic.percK, stochastic.percD), upMove)
        return {
            'st': stochastic,
            'up':up,
            'buy': buy,
            'sell': bt.indicators.CrossDown(stochastic.percK, stochastic.percD)
        }

    def should_buy(self, name, context):
        return context['indicators']['buy'][0]

    def should_sell(self, name, context):
        # return False
        return context['indicators']['sell'][0]





class MACrossOver(MultiStocksStrategy):
    params = (
        # period for the fast Moving Average
        ('fast', 10),
        # period for the slow moving average
        ('slow', 30),
        # moving average to use
        ('movav', bt.indicators.MovAv.SMA)
    )

    def create_indicators(self, name):
        sma_fast = self.p.movav(self.getdatabyname(name), period=self.p.fast)
        sma_slow = self.p.movav(self.getdatabyname(name), period=self.p.slow)

        buy = bt.indicators.CrossOver(sma_fast, sma_slow)
        return {
            'buy': buy,
            'fast': sma_fast,
            'slow': sma_slow
        }

    def should_buy(self, name, context):
        sma = context['indicators']['fast']
        return context['indicators']['buy'][0] > 0 and sma[0] > sma[-1]

    def should_sell(self, name, context):
        # return context['indicators']['buy'][0] < 0
        return context['data'].close[0] < context['indicators']['slow'][0]