import config as cfg
import csv
import numpy as np
import pandas as pd
import time

'''
developer notes
4, calWgtEarnG -> 就咁two df divide
7, post_df = pd.... can use index_col =['0']
'''


def routing(csv_key):
    with open(cfg.directory['pre'] + cfg.pre_csv[csv_key])as file:
        reader = csv.reader(file)
        raw_pre_rows = [rows for rows in reader]
    post_df = pd.read_csv((cfg.directory['post'] + cfg.post_csv[csv_key]), header=None)  # index_col = ['0']

    if csv_key == 'mkt_cap':
        cfg.param_cls_dict[csv_key] = MktCap(csv_key, raw_pre_rows, post_df) # FIXME
        cfg.updated_csv_data[csv_key] = cfg.param_cls_dict[csv_key].final_df
        cfg.param_cls_dict[csv_key].updateCSV()
    elif csv_key == 'earn_g':
        cfg.param_cls_dict[csv_key] = EarnG(csv_key, raw_pre_rows, post_df) # FIXME
        cfg.updated_csv_data[csv_key] = cfg.param_cls_dict[csv_key].final_df
        cfg.param_cls_dict[csv_key].updateCSV()
    elif csv_key == 'px':
        cfg.param_cls_dict[csv_key] = StkPx(csv_key, raw_pre_rows, post_df) # FIXME
        cfg.updated_csv_data[csv_key] = cfg.param_cls_dict[csv_key].final_df
        cfg.param_cls_dict[csv_key].updateCSV()
    elif csv_key == cfg.mkt_idx_name:
        cfg.mktidx_cls_dict[csv_key] = MktIdx(csv_key, raw_pre_rows, post_df)
        cfg.updated_csv_data[csv_key] = cfg.mktidx_cls_dict[csv_key].final_df
        cfg.mktidx_cls_dict[csv_key].updateCSV()


class MktIdx(object):
    pre_data_beg_idx = 6
    date_col_idx = 0

    def __init__(self, csv_key, raw_pre_rows, post_df):
        self.pre_df = pd.DataFrame(raw_pre_rows[self.pre_data_beg_idx:]).iloc[:, [0, 1]]
        self.pre_date_df = cfg.refmtDateList(self.pre_df[self.date_col_idx])
        self.post_df = post_df
        self.post_last_date = self.getPostLastDate()
        self.csv_name = csv_key
        self.final_df = self.getFinalDF()

    def getPostLastDate(self):  # FIXME to adjustDfPeriod
        post_last_date = self.post_df[self.date_col_idx][len(self.post_df[self.date_col_idx]) - 1]
        post_last_date = pd.to_datetime(post_last_date, format='%d/%m/%Y')
        return post_last_date

    def getFinalDF(self):
        rows_to_add_idx = self.pre_df.loc[self.pre_date_df > self.post_last_date].index
        rows_to_add = self.pre_df.loc[rows_to_add_idx]
        final_df = pd.concat([self.post_df, rows_to_add], ignore_index=True)
        final_df = final_df.replace(to_replace='', value=None).fillna(method='ffill')
        final_df = final_df.set_index([0])
        final_df.columns = ['Index Value']
        final_df['Index Value'] = pd.to_numeric(final_df['Index Value'])
        final_df.index = cfg.refmtDateList(final_df.index)
        return final_df

    def calKPI(self, test_type='in_sam', freq=0):
        test_roll_freq = freq
        if test_type == 'in_sam':
            test_beg_year, test_end_year, _ = cfg.getTestBegEndYr(test_roll_freq)  #FIXME
        elif test_type == 'out_sam':
            _ , test_beg_year, test_end_year = cfg.getTestBegEndYr(test_roll_freq)  #FIXME
        bm_idx_df = self.final_df.loc[self.final_df.index >= test_beg_year]
        bm_idx_df = bm_idx_df.loc[bm_idx_df.index < test_end_year]  # FIXME, may del
        bm_kpi_df = bm_idx_df.pct_change().mul(100).copy()
        bm_kpi_df.columns = ['Daily Return']
        bm_kpi_df['Cumulative Return'] = bm_kpi_df['Daily Return'].div(100).add(1).cumprod()
        return bm_idx_df, bm_kpi_df

    def updateCSV(self):
        to_print_df = self.final_df.copy()
        to_print_df.index = to_print_df.index.strftime("%d/%m/%Y")
        to_print_df.to_csv(cfg.directory['post'] + cfg.post_csv[self.csv_name], header=False) # index=False


class StkParamBase(object):  # FIXME
    pre_data_beg_idx = 6
    post_data_beg_idx = 2
    data_col_per_stk = 2
    date_cidx_per_stk = 0

    def __init__(self, csv_key, raw_pre_rows, post_df):
        self.csv_name = csv_key
        self.raw_post_df = post_df
        #self.raw_pre_rows  = raw_pre_rows
        self.pre_list = raw_pre_rows[self.pre_data_beg_idx:]
        self.post_df, self.stkcode_list, self.sec_list = self.getPostDFComp()
        if not self.pre_list:
            self.final_df = self.naToZero(self.post_df.copy())
        else:
            self.decom_pre_list = self.getDecomPreList()
            self.date_list = self.getDateList()
            self.pre_stk_code = list(filter(None, raw_pre_rows[3]))[1:]
            self.rows_to_add = self.calRowsToAdd()
            self.final_df = self.getFinalDF()

    def getPostDFComp(self):
        stkcode_list = self.raw_post_df.iloc[0].to_numpy(copy=True)[1:]
        sec_list = self.raw_post_df.iloc[1].to_numpy(copy=True)[1:]
        post_df = self.raw_post_df[self.post_data_beg_idx:]
        post_df = post_df.set_index(post_df[0]).drop([0], axis=1)
        post_df.columns = stkcode_list
        post_df.index = pd.to_datetime(post_df.index, dayfirst=True)
        return post_df, stkcode_list, sec_list

    def getDecomPreList(self):
        decom_pre_list = []
        for x in range(int(len(self.pre_list[0])/self.data_col_per_stk)):
            decom_pre_list.append([])
            for y in range(self.data_col_per_stk):
                decom_pre_list[x].append([])
                for z in range(len(self.pre_list)):
                    decom_pre_list[x][y].append(self.pre_list[z][x * self.data_col_per_stk + y])
        return decom_pre_list

    def getDateList(self):
        date_list = []
        for i in range(len(self.decom_pre_list)):
            date_list += self.decom_pre_list[i][self.date_cidx_per_stk]
        date_list = cfg.refmtDateList(date_list).to_period("Q")
        return date_list

    def getParamList(self):
        param_list = []
        for i in range(len(self.decom_pre_list)):
            param_list.append([""]*len(self.date_list))
            for j in range(len(self.decom_pre_list[i][1])):  # FIXME
                param_list[i][len(self.decom_pre_list[i][1])*i + j] = self.decom_pre_list[i][1][j]  # FIXME
        return param_list

    def calRowsToAdd(self):
        param_list = self.getParamList()
        recom_pre_df = pd.DataFrame(param_list,
                                    index=self.pre_stk_code,
                                    columns=self.date_list).T
        recom_pre_df = recom_pre_df.loc[recom_pre_df.index.notnull()]
        self.post_df.index = self.post_df.index.to_period("Q")
        recom_pre_df = recom_pre_df.groupby(recom_pre_df.index).sum().replace("", 0.0)
        rows_to_add = recom_pre_df.loc[recom_pre_df.index > self.post_df.index.max()]
        return rows_to_add

    def getFinalDF(self):
        final_df = pd.concat([self.post_df, self.rows_to_add])
        final_df.columns = pd.MultiIndex.from_arrays((self.stkcode_list,
                                                      self.sec_list))
        final_df = self.naToZero(final_df)
        return final_df

    def updateCSV(self):
        to_print_df = self.final_df.copy()
        to_print_df.to_csv(cfg.directory['post'] + cfg.post_csv[self.csv_name])

    @staticmethod
    def naToZero(df_to_convert):
        df_to_convert = df_to_convert.replace(r'^\s', np.nan, regex=True)
        df_to_convert = df_to_convert.fillna(0)
        obj_col = df_to_convert.select_dtypes(include='object').columns
        df_to_convert[obj_col] = df_to_convert[obj_col].astype("float")
        return df_to_convert


class MktCap(StkParamBase):
    def __init__(self, csv_key, raw_pre_rows, post_df):
        StkParamBase.__init__(self, csv_key, raw_pre_rows, post_df)
        if not self.pre_list:
            self.final_df.index = self.final_df.index.to_period("Q")

class StkPx(StkParamBase):
    post_data_beg_idx = 1

    def __init__(self, csv_key, raw_pre_rows, post_df):
        self.sec_list = None
        StkParamBase.__init__(self, csv_key, raw_pre_rows, post_df)

    def getDateList(self):
        date_list = self.decom_pre_list[0][0]  #all HK stk, trading date the same; assume the same
        date_list = cfg.refmtDateList(date_list)
        return date_list

    def getParamList(self):
        param_list = []
        for i in range(len(self.decom_pre_list)):
            param_list.append(self.decom_pre_list[i][1])
        return param_list    

    def calRowsToAdd(self):
        param_list = self.getParamList()
        recom_pre_df = pd.DataFrame(param_list,
                                    index=self.pre_stk_code,
                                    columns=self.date_list).T
        rows_to_add = recom_pre_df.loc[self.date_list > self.post_df.index.max()]
        return rows_to_add

    def getFinalDF(self):
        final_df = pd.concat([self.post_df, self.rows_to_add])
        final_df = final_df.replace(to_replace='', value=None).fillna(method='ffill') #FIXME move to naToZero
        final_df = final_df.replace(to_replace='#N/A N/A', value=None).fillna(0) #FIXME move to naToZero
        final_df = final_df.astype(np.float64)
        return final_df

    def updateCSV(self):
        to_print_df = self.final_df.copy()
        to_print_df.index = to_print_df.index.strftime("%d/%m/%Y")
        to_print_df.to_csv(cfg.directory['post'] + cfg.post_csv[self.csv_name])


class EarnG(StkParamBase):
    def __init__(self, csv_key, raw_pre_rows, post_df):
        StkParamBase.__init__(self, csv_key, raw_pre_rows, post_df)
        if not self.pre_list:
            self.final_df.index = self.final_df.index.to_period("Q")
        else:
            self.sec_list_dict = self.getSectorDictList()  # chg to class var?
            self.rows_to_add = self.naToZero(self.rows_to_add)
            self.wgt_df = self.getWgtGrowth(self.sec_list_dict)
            self.rows_to_add = self.calWgtEarnG()

    def getSectorDictList(self):
        sec_list_dict = {}
        for sec_key in cfg.sec_league_tbl.keys():
            sec_list_dict[sec_key] = []
        return sec_list_dict

    def getWgtGrowth(self, sec_list_dict):
        weight = []
        for i in range(len(self.rows_to_add)): # why enumerate not work
            for key in sec_list_dict.keys():
                sec_list_dict[key] = []
            weight.append([])
            for j, sec_val in enumerate(self.sec_list):
                for key, val in cfg.sec_league_tbl.items():
                    if val == sec_val:
                        sec_list_dict[key].append(self.rows_to_add.iat[i, j])
            for key in sec_list_dict.keys():
                weight[i].append(sum(sec_list_dict[key]))
        wgt_df = pd.DataFrame(weight, index=self.rows_to_add.index,
                              columns=cfg.sec_league_tbl.keys())
        return wgt_df

    def calWgtEarnG(self):
        self.rows_to_add.columns = self.sec_list # del?
        for wgt_sec_key in self.wgt_df.columns:
            wgt_key = wgt_sec_key
            self.rows_to_add[cfg.sec_league_tbl[wgt_sec_key]] = self.rows_to_add[cfg.sec_league_tbl[wgt_sec_key]].apply \
                                                            (lambda cell_value: cell_value / list(self.wgt_df[wgt_sec_key]),
                                                             axis = 0)
        self.rows_to_add.columns = self.stkcode_list
        return self.rows_to_add


if __name__ == '__main__':
    print("\n")
    print("Start Update...")

    start_time = time.time()
    cfg.setupFolder('post')

    for csv_key in cfg.pre_csv.keys():
        routing(csv_key)
    
    print("...Finish Update: ready for Sector_selection")
    print("\n")
    print("--- Time used: %s seconds ---" % (round(time.time() - start_time, 2)))
