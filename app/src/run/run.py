from __future__ import (absolute_import, division, print_function,
                        unicode_literals)


import datetime  # For datetime objects
import backtrader as bt
from strategies import MACrossOver, DMAStrategy,TestStrategy,MultiStocksStrategy,MACDStrategy,PrettyGoodOscillatorStrategy,StochasticStrategy, StochasticEnhancedStrategy

from sizers import PercentWithRoundingSizer, RiskSizer
from commissions import IBCommission

def run():
    stopLossPercent = 0.13
    stocks = ['GOOGL', 'AAPL', 'AMZN', 'FB', 'INTC', 'IBM', 'T', 'HPQ']
    # stocks = ['INTC']
    # Create a cerebro entity
    cerebro = bt.Cerebro()
    cerebro.broker = bt.brokers.BackBroker(slip_perc=0.01)  # 0.5%

    # Add a strategy
    # cerebro.addstrategy(TestStrategy, maperiod=30, trailpercent=0.01),
    # cerebro.addstrategy(MultiStocksStrategy, maperiod=15, trailpercent=0.07)
    # cerebro.addstrategy(MACDStrategy)
    # cerebro.addstrategy(PrettyGoodOscillatorStrategy)
    #cerebro.addstrategy(StochasticStrategy,trailpercent=0.05)
    #cerebro.addstrategy(StochasticEnhancedStrategy,trailpercent=0.05)
    # cerebro.addstrategy(DMAStrategy,trailpercent=0.07, sell_signal=False)
    # cerebro.addstrategy(MACrossOver,trailpercent=0.08, sell_signal=False, fast=5, slow=20, movav=bt.indicators.ExponentialMovingAverage)
    cerebro.addstrategy(MACrossOver,trailpercent=stopLossPercent, sell_signal=False, fast=5, slow=20)

    for stock in stocks:
        # Create a Data Feed
        data = bt.feeds.YahooFinanceData(
            dataname=stock,
            # Do not pass values before this date
            fromdate=datetime.datetime(2017, 1, 1),
            # Do not pass values before this date
            todate=datetime.datetime(2017, 12, 31),
            # Do not pass values after this date
            reverse=False)
        cerebro.adddata(data)

    # Set our desired cash start
    cerebro.broker.setcash(30000.0)


    cerebro.addsizer(RiskSizer, total_percentage_risk=0.01,stop_loss_percentage=stopLossPercent)

    # Set the commission
    # cerebro.broker.setcommission(commission=0.002)
    cerebro.broker.addcommissioninfo(IBCommission())

    # Print out the starting conditions
    print('Starting Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Run over everything
    cerebro.run()

    # Print out the final result
    print('Final Portfolio Value: %.2f' % cerebro.broker.getvalue())

    # Plot the result
    cerebro.plot(savefig=True)


