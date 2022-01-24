import config as cfg
import Update_Inputs as up
import pandas as pd
import os
import scipy.stats as stat
import time

'''
developer notes
2, Ranking [1 and 0] file sec name short form
3, check if update is needed, rather than always update
4, Q2 Q4: semiannual, but use Q2 Q4 quarter only earn growth

'''

def routing(csv_name, earn_g_df, mktcap_df):
    if csv_name == 'ranking':
        cfg.sec_eval_cls_dict[csv_name] = MarksDF(earn_g_df, mktcap_df)
    elif csv_name == 'signal':
        cfg.sec_eval_cls_dict[csv_name] = SignalDF(earn_g_df, mktcap_df)
    cfg.updated_csv_data[csv_name] = cfg.sec_eval_cls_dict[csv_name].updateCSV()


class MarksDF(object):
    def __init__(self, earn_g_df, mktcap_df):
        self.mktcap_df = mktcap_df.copy()
        self.earn_g_df = earn_g_df.copy()
        self.earn_g_df.columns = self.mktcap_df.columns  # FIXME for US only. US earn_g column idx no sector
        self.sec_dict_list = {}
        self.rank_date_list = self.getRankDateList()
        self.sum_list = self.getSumList()

    def getRankDateList(self):
        date_beg_idx = None
        rank_date_list = self.earn_g_df.index.copy() \
                        if len(self.mktcap_df.index) > len(self.earn_g_df.index) \
                        else self.mktcap_df.index.copy()

        for date in rank_date_list:
            if date >= cfg.beg_test_date and date.quarter%2 == 0:
                #one-off if
                if date_beg_idx is None:
                    date_beg_idx = rank_date_list.get_loc(date)
                    rank_date_list = rank_date_list[date_beg_idx::2]
        return rank_date_list

    def getSumList(self):
        sum_list = []
        j = 0
        for i, date in enumerate(self.rank_date_list):
            for sec_abbr, sec_fullname in cfg.sec_league_tbl.items():
                self.sec_dict_list[sec_abbr] = list(self.earn_g_df.loc[date].xs(sec_fullname, level=1))
            sum_list.append([])
            for sec_abbr in self.sec_dict_list.keys():
                sum_list[j].append(sum(self.sec_dict_list[sec_abbr]))
            sum_list[j] = len(sum_list[j]) - stat.rankdata(sum_list[j])
            j += 1
        return sum_list

    def updateCSV(self):
        marks_df = pd.DataFrame(self.sum_list, index=self.rank_date_list,
                                columns=cfg.sec_league_tbl.values())
        marks_df.to_csv(cfg.directory['ssr'] + 'Ranking based on Weighted Earnings Growth.csv')


class SignalDF(MarksDF):
    mark_criteria = cfg.num_of_sec_chosen - 1  # -1 to consider "0" idx
    def __init__(self, earn_g_df, mktcap_df):
        MarksDF.__init__(self, earn_g_df, mktcap_df)

    def updateCSV(self):
        marks_df = pd.DataFrame(self.sum_list, index=self.rank_date_list,
                                columns=cfg.sec_league_tbl.values())
        signal_df = marks_df.applymap(lambda x: 0 if x > self.mark_criteria else 1)
        signal_df.to_csv(cfg.directory['ssr'] + 'Signal [1 and 0].csv')
        return signal_df


if __name__ == '__main__':
    start_time = time.time()
    print("\n")
    print("Start Sector Selection Process...")

    cfg.setupFolder('ssr')
    up.routing('earn_g')
    up.routing('mkt_cap')
    earn_g_df = cfg.updated_csv_data.get('earn_g')
    mktcap_df = cfg.updated_csv_data.get('mkt_cap')

    routing('ranking', earn_g_df, mktcap_df)
    routing('signal', earn_g_df, mktcap_df)

    print("Choosing Sectors Completed...")
    print("\n")
    print("--- Time used: %s seconds ---" % (round(time.time() - start_time, 2)))
