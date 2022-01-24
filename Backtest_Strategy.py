import os
import pandas as pd
import numpy as np
import Update_Inputs as up
import config as cfg
import Select_Sector as sec_select
import datetime
import time
import itertools as it  # to learn
import matplotlib.pyplot as plt
import matplotlib as mlib

'''
developer notes
3, qly_rtn_df Q2 Q4 NAV the same, possible problem
8, 2018 Q4 rows gone
'''


class WgtRtnMatrix():
    def __init__(self):
        self.mktcap_cls = cfg.param_cls_dict.get('mkt_cap')
        self.signal_df = cfg.updated_csv_data.get('signal').copy()
        self.mktcap_df = cfg.updated_csv_data.get('mkt_cap').copy()
        self.stkpx_df = cfg.updated_csv_data.get('px').copy()
        self.chgTestPeriod()
        self.rtn_df = self.getRtnDF()
        self.wgt_df = self.getWgt()
        self.rtn_matrix = self.calWgtRtn()
        self.kpi_df = self.calKPI()
        self.final_matrix = self.getFinalMatrix()

    def chgTestPeriod(self):
        beg_year = cfg.checkBegYr()
        self.signal_df = self.signal_df.loc[self.signal_df.index >=
                                            pd.to_datetime(beg_year).to_period("Q")
                                            - cfg.qtr_to_semi_ratio]

        self.mktcap_df = self.mktcap_df.loc[self.mktcap_df.index >=
                                            pd.to_datetime(beg_year).to_period("Q")
                                            - cfg.qtr_to_semi_ratio]

        self.stkpx_df = self.stkpx_df.loc[self.stkpx_df.index >= beg_year]

    def getRtnDF(self):
        shft_signal_df = self.shiftDfDate(self.signal_df)
        rtn_df = self.stkpx_df.replace(0, np.nan).pct_change()
        rtn_df.columns = self.mktcap_cls.sec_list
        rtn_df.index = cfg.rfmtToSemiannual(self.stkpx_df.index.copy())
        rtn_df = rtn_df.mul(shft_signal_df)
        return rtn_df

    def getWgt(self):
        chk_px_exist_df = self.stkpx_df.copy()
        chk_px_exist_df = chk_px_exist_df.applymap(lambda x: 0 if x == 0 else 1)
        chk_px_exist_df.index = cfg.rfmtToSemiannual(chk_px_exist_df.index)

        shft_signal_df = self.shiftDfDate(self.signal_df)

        shft_mktcap_df = self.shiftDfDate(self.mktcap_df)
        shft_mktcap_df.columns = self.mktcap_cls.sec_list
        shft_mktcap_df = shft_mktcap_df[1::cfg.qtr_to_semi_ratio]

        invted_cap_df = shft_mktcap_df.mul(shft_signal_df)
        invted_cap_df.columns = self.mktcap_cls.stkcode_list
        cap_wth_px_df = chk_px_exist_df.mul(invted_cap_df)
        sum_invt_cap = cap_wth_px_df.sum(axis=1)
        wgt_df = cap_wth_px_df.div(sum_invt_cap, axis=0)
        return wgt_df

    def calWgtRtn(self):
        self.rtn_df.columns = self.mktcap_cls.stkcode_list
        rtn_matrix = self.wgt_df*self.rtn_df
        rtn_matrix.index = self.stkpx_df.index.copy()
        rtn_matrix = rtn_matrix.replace(0, np.nan)
        rtn_matrix = rtn_matrix*100
        return rtn_matrix

    def calKPI(self):
        kpi_dict = {}
        kpi_dict['Daily Return'] = self.rtn_matrix.sum(axis=1)
        kpi_dict['Cumulative Return'] = self.rtn_matrix.sum(axis=1).div(100).add(1).cumprod()
        kpi_dict['Stock Count'] = self.rtn_matrix.count(axis=1)
        kpi_dict['Portfolio NAV'] = self.rtn_matrix.sum(axis=1).div(100).add(1).cumprod()*cfg.initial_NAV
        kpi_df = pd.DataFrame(kpi_dict, index = self.rtn_matrix.index)
        return kpi_df

    def getFinalMatrix(self):
        final_matrix = pd.concat([self.rtn_matrix, self.kpi_df], axis=1)
        return final_matrix

    def writeCSV(self):
        self.final_matrix.to_csv(cfg.directory['ssr'] + '[' + datetime.datetime.now().strftime("%Y%m%d %H%M %S") + '] result matrix.csv')

    # use previous semi data to calculate, shift 1 period for mul calculation
    @staticmethod
    def shiftDfDate(df):
        df = df.copy()
        df.index = df.index.shift(cfg.qtr_to_semi_ratio)
        return df


class Stats():
    def __init__(self, perf_df, bm_df):
        self.perf_df = perf_df.copy()
        self.bm_idx_val_df = bm_df.copy()
        self.daily_rtn_series = self.perf_df['Daily Return'].copy()
        self.avg_rtn = self.daily_rtn_series.mean()
        self.std_rtn = self.daily_rtn_series.std()

    def drawBarGraphs(self, grph_name):
        def calQlyRtn():
            qly_rtn_list = [cfg.rfmtToSemiannual(self.perf_df.index.copy()),
                            list(self.perf_df['Portfolio NAV'])]
            qly_rtn_df = pd.DataFrame(qly_rtn_list, index=['Semi Date', 'Return']).T
            qly_rtn_df = qly_rtn_df.drop_duplicates(subset='Semi Date')
            qly_rtn_df = qly_rtn_df.set_index(['Semi Date'])
            qly_rtn_df = qly_rtn_df.pct_change()
            return qly_rtn_df

        qly_rtn_df = calQlyRtn()
        fig = plt.figure()
        ax = fig.add_subplot()
        qly_rtn_df['Return'].plot(ax=ax, color=(qly_rtn_df['Return']>0).map({True:'mediumblue', False:'red'}),
                                  kind='bar', title=grph_name, ylabel='Return', legend=False)
        ax.xaxis.set_major_locator(plt.MaxNLocator(8))
        ax.yaxis.set_major_locator(plt.MaxNLocator(8))
        ax.yaxis.set_major_formatter(mlib.ticker.PercentFormatter(xmax=1, symbol='%'))
        fig.set_facecolor('lightgrey')
        ax.set_facecolor('black')
        fig.autofmt_xdate()
        fig.savefig(cfg.directory['ssr']+cfg.mkt_idx_name+" "+grph_name+".png")
        plt.show()

    def drawLineGraphs(self, grph_name):
        beg_mktidx_val = self.bm_idx_val_df.iat[0, 0]
        idx_cum_rtn_df = self.bm_idx_val_df/beg_mktidx_val
        portfo_cum_rtn_df = self.perf_df['Portfolio NAV']/cfg.initial_NAV
        fig = plt.figure()
        ax = fig.add_subplot()
        idx_cum_rtn_df.plot(ax=ax, kind='line',
                            ylabel='Cumulative Return',
                            title=grph_name)
        portfo_cum_rtn_df.plot(ax=ax, kind='line')
        ax.legend(['Benchmark:'+cfg.mkt_idx_name, 'Strategy:'+cfg.strategy_name])
        ax.xaxis.set_major_locator(plt.MaxNLocator(8))
        ax.grid(visible=True, axis='y', color='grey', linestyle='--')
        fig.set_facecolor('lightgrey')
        ax.set_facecolor('black')
        fig.autofmt_xdate()
        fig.savefig(cfg.directory['ssr'] + cfg.mkt_idx_name + " " + grph_name + ".png")
        plt.show()

    def printStats(self, strategy):
        mdd_subj = None
        if strategy == 'Sector Rotate':
            print(len(self.perf_df), "days")
            mdd_subj = self.perf_df['Portfolio NAV']
        elif strategy == cfg.mkt_idx_name:
            print(cfg.mkt_idx_name, "Index: ")
            mdd_subj = self.bm_idx_val_df['Index Value']

        print("Annual Sharpe Ratio: ", round(self.avg_rtn/self.std_rtn*(cfg.trade_days**(1/2)), 4))
        print("Cumulative =", round((self.perf_df['Cumulative Return'][-1]-1)*100, 4), "%")
        print("Max Consecutive Loss =", self.calMaxConsecLoss(self.perf_df['Daily Return'] < 0), "days")
        print("Max Drawdown:", round(self.calMdd(mdd_subj.to_numpy(copy=True)), 4), "%")
        print("Win Rate:", round(self.calWinRate(self.daily_rtn_series), 4), "%")
        print("Average Daily Return =", round(self.avg_rtn, 4), "%")
        print("SD of Daily Return =", round(self.std_rtn, 4), "%")
        print("Annualized Return =", round(self.avg_rtn*cfg.trade_days, 4), "%")
        print("Annualized Volatility =", round(self.std_rtn*(cfg.trade_days**(1/2)), 4), "%")
        print("\n")

    @staticmethod
    def calMaxConsecLoss(neg_rtn):
        max_val = 0
        for val, grp in it.groupby(neg_rtn):
            max_val = max(max_val, sum(grp))
        return max_val

    @staticmethod
    def calWinRate(rtn_series):
        win_cnt = list(rtn_series > 0).count(True)
        lose_cnt = list(rtn_series < 0).count(True)
        win_rate = win_cnt/(win_cnt + lose_cnt)*100
        return win_rate

    @staticmethod
    def calMdd(nav_series):
        new_max_nav = nav_series[0]
        dd_period_idx = []
        dd_pct_list = []
        beg_nav_idx = 0
        end_nav_idx = 1

        for idx, nav in enumerate(nav_series):
            if nav > new_max_nav:
                new_max_nav = nav
                dd_period_idx.append(idx)

        dd_period_idx = np.array(dd_period_idx)
        period_cnt = int(len(dd_period_idx)/2)
        dd_period_idx = np.resize(dd_period_idx, (period_cnt,2))

        for arr in dd_period_idx:
            periodic_dd = nav_series[arr[beg_nav_idx]:arr[end_nav_idx]]
            dd_pct_list.append((min(periodic_dd)-max(periodic_dd))/max(periodic_dd)*100)
        mdd = min(dd_pct_list)
        return mdd


if __name__ == '__main__':
    start_time = time.time()
    print("\n")
    print(cfg.mkt_idx_name, "BACK TEST", "start from", cfg.beg_yr)

    cfg.setupFolder('ssr')

    for csv_key in cfg.pre_csv.keys():
        up.routing(csv_key)

    sec_select.routing('signal',
                       cfg.updated_csv_data.get('earn_g'),
                       cfg.updated_csv_data.get('mkt_cap'))

    matrix_cls = WgtRtnMatrix()
    matrix_cls.writeCSV()

    mktidx_cls = cfg.mktidx_cls_dict.get(cfg.mkt_idx_name)
    bm_idx_df, bm_kpi_df = mktidx_cls.calKPI()

    # match testing period time
    bm_idx_df = bm_idx_df.loc[bm_idx_df.index <= matrix_cls.kpi_df.index.max()]
    bm_kpi_df = bm_kpi_df.loc[bm_kpi_df.index <= matrix_cls.kpi_df.index.max()]
    
    bt_stats_cls = Stats(matrix_cls.kpi_df, bm_idx_df)
    bt_stats_cls.drawLineGraphs(cfg.line_grph_title)
    bt_stats_cls.drawBarGraphs(cfg.bar_grph_title)
    bt_stats_cls.printStats(cfg.strategy_name)

    bm_stats_cls = Stats(bm_kpi_df, bm_idx_df)
    bm_stats_cls.printStats(cfg.mkt_idx_name)

    print("Backtesting Completed...")
    print("\n")
    print("--- Time used: %s seconds ---" % (round(time.time()-start_time, 2)))
