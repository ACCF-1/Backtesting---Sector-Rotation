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
9, day need to minus 1?
10, add signal evaluation: buy but negative return; not buy but positive return
11, optim_max_param
'''


class WgtRtnMatrix():
    def __init__(self, signal_df, test_type='whole_sample', test_roll_freq=1):
        self.test_type = test_type
        self.test_roll_freq = test_roll_freq
        self.mktcap_cls = cfg.param_cls_dict.get('mkt_cap')
        self.signal_df = signal_df.copy()
        self.mktcap_df = cfg.updated_csv_data.get('mkt_cap').copy()
        self.stkpx_df = cfg.updated_csv_data.get('px').copy()
        self.chgTestPeriod()
        self.rtn_df = self.getRtnDF()
        self.wgt_df = self.getWgt()
        self.rtn_matrix = self.calWgtRtn()
        self.kpi_df = self.calKPI()
        self.final_matrix = self.getFinalMatrix()

    def chgTestPeriod(self):
        if self.test_type == 'in_sample':
            test_beg_year, test_end_year, _ = cfg.getTestBegEndYr(self.test_roll_freq)  #FIXME
        elif self.test_type == 'out_sample':
            _ , test_beg_year, test_end_year = cfg.getTestBegEndYr(self.test_roll_freq)
        elif self.test_type == 'whole_sample':
            test_beg_year, _ , test_end_year = cfg.getTestBegEndYr(self.test_roll_freq)

        self.signal_df = self.signal_df.loc[self.signal_df.index >=
                                            pd.to_datetime(test_beg_year).to_period("Q") - cfg.qtr_to_semi_ratio]
        self.signal_df = self.signal_df.loc[self.signal_df.index <= pd.to_datetime(test_end_year).to_period("Q")]

        self.mktcap_df = self.mktcap_df.loc[self.mktcap_df.index >=
                                            pd.to_datetime(test_beg_year).to_period("Q") - cfg.qtr_to_semi_ratio]
        self.mktcap_df = self.mktcap_df.loc[self.mktcap_df.index <= pd.to_datetime(test_end_year).to_period("Q")]

        self.stkpx_df = self.stkpx_df.loc[self.stkpx_df.index >= test_beg_year]
        self.stkpx_df = self.stkpx_df.loc[self.stkpx_df.index < test_end_year]

    def getRtnDF(self):
        shft_signal_df = self.shiftDfDate(self.signal_df)
        rtn_df = self.stkpx_df.replace(0, np.nan).pct_change()
        rtn_df.columns = self.mktcap_cls.sec_list
        rtn_df.index = cfg.rfmtToSemiannual(self.stkpx_df.index.copy())
        rtn_df = rtn_df.mul(shft_signal_df)
        rtn_df = rtn_df.drop(rtn_df.tail(1).index)
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
        wgt_df = wgt_df.drop(wgt_df.tail(1).index)
        return wgt_df

    def calWgtRtn(self):
        self.rtn_df.columns = self.mktcap_cls.stkcode_list
        rtn_matrix = self.wgt_df*self.rtn_df
        stkpx_df = self.stkpx_df.drop(self.stkpx_df.tail(len(self.stkpx_df.index)-len(rtn_matrix)).index)
        rtn_matrix.index = stkpx_df.index.copy()
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
        self.sharpe = self.calSharpe()
        self.cum_rtn = 100*(self.perf_df['Cumulative Return'][-1]-1)
        self.consec_loss = self.calMaxConsecLoss(self.perf_df['Daily Return'] < 0)
        self.win_rate = self.calWinRate(self.daily_rtn_series)
        self.strategy_mdd = self.calMdd(self.perf_df['Portfolio NAV'].to_numpy(copy=True))\
                                        if 'Portfolio NAV' in self.perf_df.columns else None
        self.annual_rtn = self.avg_rtn*cfg.trade_days
        self.annual_vol = self.std_rtn*(cfg.trade_days**(1/2))

    def drawBarGraphs(self, grph_name):
        def calQlyRtn():
            qly_rtn_list = [cfg.rfmtToSemiannual(self.perf_df.index.copy()),
                            list(self.perf_df['Portfolio NAV'])]
            qly_rtn_df = pd.DataFrame(qly_rtn_list, index=['Semi Date', 'Return']).T
            qly_rtn_df = qly_rtn_df.drop_duplicates(subset='Semi Date')
            qly_rtn_df = qly_rtn_df.set_index(['Semi Date'])
            qly_rtn_df = qly_rtn_df.pct_change()
            qly_rtn_df.index = qly_rtn_df.index.shift(cfg.qtr_to_semi_ratio*-1)
            return qly_rtn_df

        qly_rtn_df = calQlyRtn()
        fig = plt.figure()
        ax = fig.add_subplot()
        qly_rtn_df['Return'].plot(ax=ax, color=(qly_rtn_df['Return']>0).map({True:'mediumblue', False:'red'}),
                                  kind='bar', title=grph_name, ylabel='Return', legend=False)
        if len(qly_rtn_df) >= 8:
            ax.xaxis.set_major_locator(plt.MaxNLocator(8))
        ax.yaxis.set_major_locator(plt.MaxNLocator(8))
        ax.yaxis.set_major_formatter(mlib.ticker.PercentFormatter(xmax=1, symbol='%'))
        fig.set_facecolor('lightgrey')
        ax.set_facecolor('black')
        fig.autofmt_xdate()
        fig.savefig(cfg.directory['ssr'] + cfg.market+ ", " +grph_name + ".png")
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
        fig.savefig(cfg.directory['ssr'] + cfg.market + ", " + grph_name + ".png")
        plt.show()

    def printStats(self, strategy):
        mdd_subj = None
        if strategy == 'Sector Rotate':
            print(len(self.perf_df), "days")
            mdd_subj = self.perf_df['Portfolio NAV']
        elif strategy == cfg.mkt_idx_name:
            print(cfg.mkt_idx_name, "Index: ")
            mdd_subj = self.bm_idx_val_df['Index Value']

        print("Annual Sharpe Ratio: ", round(self.sharpe, 4))
        print("Cumulative =", round(self.cum_rtn, 4), "%")
        print("Max Consecutive Loss =", self.consec_loss, "days")
        print("Max Drawdown:", round(self.calMdd(mdd_subj.to_numpy(copy=True)), 4), "%")
        print("Win Rate:", round(self.win_rate, 4), "%")
        print("Average Daily Return =", round(self.avg_rtn, 4), "%")
        print("SD of Daily Return =", round(self.std_rtn, 4), "%")
        print("Annualized Return =", round(self.annual_rtn, 4), "%")
        print("Annualized Volatility =", round(self.annual_vol, 4), "%")
        print("\n")

    def calSharpe(self):
        sharpe = self.avg_rtn/self.std_rtn*(cfg.trade_days**(1/2))
        return sharpe

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
        dd_period_idx = [0]
        dd_pct_list = []

        for idx, nav in enumerate(nav_series):
            if nav > new_max_nav:
                new_max_nav = nav
                dd_period_idx.append(idx)

        if nav_series[-1] < nav_series[dd_period_idx[-1]]:
            dd_period_idx.append(len(nav_series)-1)

        period_cnt = len(dd_period_idx) - 1

        for idx in range(period_cnt):
            periodic_dd = nav_series[dd_period_idx[idx]:dd_period_idx[idx+1]]
            dd_pct_list.append((min(periodic_dd)-max(periodic_dd))/max(periodic_dd)*100)

        mdd = min(dd_pct_list)
        return mdd


def drawQuadScatGraphs(sec_cnt_list, sharpe_list, ann_rtn_list, mdd_list, ann_vol_list, freq):
    fig = plt.figure(figsize=(8,7), constrained_layout=True)
    fig.suptitle(cfg.scat_grph_title, fontsize=18)
    ax1 = fig.add_subplot(2,2,1)
    ax1.yaxis.tick_right()
    ax1.tick_params(labelright=False)
    ax1.axes.scatter(ann_rtn_list, sharpe_list, c='darkblue')
    ax1.axes.invert_xaxis()
    ax1.set_xlabel('Annualized Return, %')
    ax1.yaxis.set_label_position('right')

    ax2 = fig.add_subplot(2,2,2)
    ax2.tick_params(axis='x', pad=10)
    ax2.axes.scatter(mdd_list, sharpe_list, c='darkblue')
    ax2.set_xlabel('Max Drawdown, %')
    ax2.set_ylabel('Annual Sharpe Ratio')
    ax2.axes.invert_xaxis()

    ax3 = fig.add_subplot(2,2,3)
    ax3.xaxis.tick_top()
    ax3.yaxis.tick_right()
    ax3.tick_params(labelright=False)
    ax3.tick_params(labeltop=False)
    ax3.axes.scatter(ann_rtn_list, ann_vol_list, c='darkblue')
    ax3.axes.invert_yaxis()
    ax3.axes.invert_xaxis()

    ax4 = fig.add_subplot(2,2,4)
    ax4.xaxis.tick_top()
    ax4.tick_params(labeltop=False)
    ax4.axes.scatter(mdd_list, ann_vol_list, c='darkblue')
    ax4.axes.invert_yaxis()
    ax4.axes.invert_xaxis()
    ax4.set_ylabel('Annualized Volatility, %')

    four_scat = [ax1, ax2, ax3, ax4]
    fig.set_facecolor('darkgrey')

    for ax in four_scat:
        ax.set_facecolor('lightgrey')
    
    for i, txt in enumerate(sec_cnt_list):
        ax1.annotate(txt, (ann_rtn_list[i], sharpe_list[i]))
        ax2.annotate(txt, (mdd_list[i], sharpe_list[i]))
        ax3.annotate(txt, (ann_rtn_list[i], ann_vol_list[i]))
        ax4.annotate(txt, (mdd_list[i], ann_vol_list[i]))
    
    fig.savefig(cfg.directory['ssr'] + cfg.scat_grph_title + ", window " + str(freq+1) + ".png")
    plt.show()


def rollWindowTest():
    #optim_param = cfg.optim_max_param if cfg.optim_min_param == None else cfg.optim_min_param
    mktidx_cls = cfg.mktidx_cls_dict.get(cfg.mkt_idx_name)

    for freq in range(cfg.roll_freq):
        sharpe_list = []
        mdd_list = []
        ann_rtn_list = []
        ann_vol_list = []
        sec_cnt_list = []
        best_mark = None
        test_mark = []
        
        bm_idx_df, bm_kpi_df = mktidx_cls.calKPI('in_sample', freq)
        for mark in range(cfg.sim_sec_cnt_min, cfg.sim_sec_cnt_max + 1):
            test_mark.append(mark)
            cfg.sec_eval_cls_dict['signal'+str(mark)] = sec_select.SignalDF(cfg.updated_csv_data.get('earn_g'),
                                                                            cfg.updated_csv_data.get('mkt_cap'),
                                                                            mark)
            matrix_cls = WgtRtnMatrix(cfg.sec_eval_cls_dict['signal'+str(mark)].final_df, 'in_sample', freq)

            bm_idx_df = bm_idx_df.loc[bm_idx_df.index <= matrix_cls.kpi_df.index.max()]
            bt_stats_cls = Stats(matrix_cls.kpi_df, bm_idx_df)

            sec_cnt_list.append(mark)
            sharpe_list.append(bt_stats_cls.sharpe)
            ann_rtn_list.append(bt_stats_cls.annual_rtn)
            mdd_list.append(bt_stats_cls.strategy_mdd)
            ann_vol_list.append(bt_stats_cls.annual_vol)

            best_mark = test_mark[sharpe_list.index(max(sharpe_list))]

        print('Picking ' + str(best_mark) + ' sectors is the best in terms of annualized sharpe, with ' + str(round(max(sharpe_list),4)))

        drawQuadScatGraphs(sec_cnt_list, sharpe_list, ann_rtn_list, mdd_list, ann_vol_list, freq)
        if cfg.optim_param == 'sharpe':
    
                mktidx_cls = cfg.mktidx_cls_dict.get(cfg.mkt_idx_name)
                bm_idx_df, bm_kpi_df = mktidx_cls.calKPI('out_sample', freq)

                print('Out of sample test, rolling window: ' +
                      str(freq+1) + ', ' + str(best_mark) + ' of sectors picked')
                
                matrix_cls = WgtRtnMatrix(cfg.sec_eval_cls_dict['signal' + str(best_mark)].final_df, 'out_sample', freq)
                bm_idx_df = bm_idx_df.loc[bm_idx_df.index <= matrix_cls.kpi_df.index.max()]
            
                bt_stats_cls = Stats(matrix_cls.kpi_df, bm_idx_df)
                bt_stats_cls.drawLineGraphs(cfg.line_grph_title + ", " + str(best_mark) + " Sector(s) Chosen, " + "window " + str(freq+1))
                bt_stats_cls.printStats(cfg.strategy_name)
                
                bm_stats_cls = Stats(bm_kpi_df, bm_idx_df)
                bm_stats_cls.printStats(cfg.mkt_idx_name)
    if cfg.roll_freq == 1:
        bt_stats_cls.drawBarGraphs(cfg.bar_grph_title)
    matrix_cls.writeCSV()

def oneTimeTest():
    sec_select.routing('signal',
                       cfg.updated_csv_data.get('earn_g'),
                       cfg.updated_csv_data.get('mkt_cap'))

    matrix_cls = WgtRtnMatrix(cfg.updated_csv_data.get('signal'))
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


'''--------------------------------------------------------------------------'''

if __name__ == '__main__':
    start_time = time.time()
    print("\n")
    print(cfg.mkt_idx_name, "BACK TEST", "start from", cfg.test_beg_yr)

    cfg.setupFolder('ssr')

    for csv_key in cfg.pre_csv.keys():
        up.routing(csv_key)

    if cfg.test_method == 'rolling':
        rollWindowTest()
    elif cfg.test_method == 'single period':
        oneTimeTest()

    print("Backtesting Completed...")
    print("\n")
    print("--- Time used: %s seconds ---" % (round(time.time()-start_time, 2)))
