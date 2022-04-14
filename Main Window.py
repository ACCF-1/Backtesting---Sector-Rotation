import config as cfg
import Backtest_Strategy as bts
import Update_Inputs as up
import time
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


class Ui_stats_window(object):
    def setupUi(self, stats_window):
        stats_window.setObjectName("stats_window")
        stats_window.setFixedSize(1100, 789)
        stats_window.setStyleSheet("background-color: rgb(246, 255, 225);")
        self.label_1 = QtWidgets.QLabel(stats_window)
        self.label_1.setGeometry(QtCore.QRect(30, 20, 321, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_1.setFont(font)
        self.label_1.setObjectName("label_1")
        self.buttonBox = QtWidgets.QDialogButtonBox(stats_window)
        self.buttonBox.setGeometry(QtCore.QRect(989, 20, 81, 241))
        self.buttonBox.setOrientation(QtCore.Qt.Vertical)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.info_panel = QtWidgets.QListWidget(stats_window)
        self.info_panel.setGeometry(QtCore.QRect(650, 90, 420, 661))
        self.info_panel.setStyleSheet("background-color: rgb(252, 252, 252);")
        self.info_panel.setObjectName("info_panel")
        self.grph_cb = QtWidgets.QComboBox(stats_window)
        self.grph_cb.setGeometry(QtCore.QRect(30, 55, 450, 22))
        self.grph_cb.setObjectName("grph_cb")
        self.grph_cb.setStyleSheet("background-color: rgb(252, 252, 252);")
        self.graphicsView = QtWidgets.QGraphicsView(stats_window)
        self.graphicsView.setGeometry(QtCore.QRect(30, 90, 600, 661))
        self.graphicsView.setStyleSheet("background-color: rgb(252, 252, 252);")
        self.graphicsView.setObjectName("graphicsView")

        self.retranslateUi(stats_window)
        self.buttonBox.accepted.connect(stats_window.accept) # type: ignore
        self.buttonBox.rejected.connect(stats_window.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(stats_window)
        
        ui.ui2.grph_cb.currentTextChanged.connect(self.showGraphs)
        
    def retranslateUi(self, stats_window):
        _translate = QtCore.QCoreApplication.translate
        stats_window.setWindowTitle(_translate("stats_window", "For Interview Purpose Only, Andy Chan"))
        self.label_1.setText(_translate("stats_window", cfg.strategy_name + " - Backtest Results"))
        
        i = 0
        for grph_key in cfg.fig_dict.keys():
            self.grph_cb.addItem("")
            self.grph_cb.setItemText(i, _translate("stats_window", grph_key))
            i += 1
        
    def showStatsInfo(self):
        for _, item in enumerate(cfg.stats_summary):
            if type(item) == str :
                self.info_panel.addItem(item)
                self.info_panel.addItem(' ')
            elif type(item) == list:
                self.info_panel.addItems(item)
                self.info_panel.addItem('----------------------------------------')
    
    def showGraphs(self):
        canvas = FigureCanvas(cfg.fig_dict[self.grph_cb.currentText()])
        proxy = QtWidgets.QGraphicsProxyWidget()
        proxy.setWidget(canvas)
        scene = QtWidgets.QGraphicsScene()
        scene.addItem(proxy)
        self.graphicsView.setScene(scene)


class Ui_BT_input_window(object):
    def setupUi(self, BT_input_window):
        BT_input_window.setObjectName("BT_input_window")
        BT_input_window.setFixedSize(354, 544)
        self.pushButton = QtWidgets.QPushButton(BT_input_window)
        self.pushButton.setGeometry(QtCore.QRect(20, 470, 305, 23))
        self.pushButton.setObjectName("pushButton")
        self.line = QtWidgets.QFrame(BT_input_window)
        self.line.setGeometry(QtCore.QRect(10, 450, 330, 16))
        self.line.setFrameShape(QtWidgets.QFrame.HLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.test_beg_yr_fld = QtWidgets.QLineEdit(BT_input_window)
        self.test_beg_yr_fld.setGeometry(QtCore.QRect(170, 100, 161, 20))
        self.test_beg_yr_fld.setObjectName("test_beg_yr_fld")
        self.train_set_period_fld = QtWidgets.QLineEdit(BT_input_window)
        self.train_set_period_fld.setGeometry(QtCore.QRect(170, 140, 161, 20))
        self.train_set_period_fld.setObjectName("train_set_period_fld")
        self.label = QtWidgets.QLabel(BT_input_window)
        self.label.setGeometry(QtCore.QRect(20, 60, 91, 16))
        self.label.setObjectName("label")
        self.label_2 = QtWidgets.QLabel(BT_input_window)
        self.label_2.setGeometry(QtCore.QRect(20, 100, 111, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(BT_input_window)
        self.label_3.setGeometry(QtCore.QRect(20, 140, 91, 16))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(BT_input_window)
        self.label_4.setGeometry(QtCore.QRect(20, 260, 101, 16))
        self.label_4.setObjectName("label_4")
        self.label_5 = QtWidgets.QLabel(BT_input_window)
        self.label_5.setGeometry(QtCore.QRect(20, 220, 121, 16))
        self.label_5.setObjectName("label_5")
        self.test_set_period_fld = QtWidgets.QLineEdit(BT_input_window)
        self.test_set_period_fld.setGeometry(QtCore.QRect(170, 180, 161, 20))
        self.test_set_period_fld.setObjectName("test_set_period_fld")
        self.sim_sec_cnt_min_fld = QtWidgets.QLineEdit(BT_input_window)
        self.sim_sec_cnt_min_fld.setGeometry(QtCore.QRect(190, 260, 51, 20))
        self.sim_sec_cnt_min_fld.setObjectName("sim_sec_cnt_min_fld")
        self.label_6 = QtWidgets.QLabel(BT_input_window)
        self.label_6.setGeometry(QtCore.QRect(20, 180, 91, 16))
        self.label_6.setObjectName("label_6")
        self.label_7 = QtWidgets.QLabel(BT_input_window)
        self.label_7.setGeometry(QtCore.QRect(20, 340, 91, 16))
        self.label_7.setObjectName("label_7")
        self.label_8 = QtWidgets.QLabel(BT_input_window)
        self.label_8.setGeometry(QtCore.QRect(20, 300, 121, 16))
        self.label_8.setObjectName("label_8")
        self.label_9 = QtWidgets.QLabel(BT_input_window)
        self.label_9.setGeometry(QtCore.QRect(20, 380, 91, 16))
        self.label_9.setObjectName("label_9")
        self.roll_freq_fld = QtWidgets.QLineEdit(BT_input_window)
        self.roll_freq_fld.setGeometry(QtCore.QRect(170, 340, 161, 20))
        self.roll_freq_fld.setObjectName("roll_freq_fld")
        self.num_of_sec_chosen_fld = QtWidgets.QLineEdit(BT_input_window)
        self.num_of_sec_chosen_fld.setGeometry(QtCore.QRect(170, 380, 161, 20))
        self.num_of_sec_chosen_fld.setObjectName("num_of_sec_chosen_fld")
        self.sim_sec_cnt_max_fld = QtWidgets.QLineEdit(BT_input_window)
        self.sim_sec_cnt_max_fld.setGeometry(QtCore.QRect(280, 260, 51, 20))
        self.sim_sec_cnt_max_fld.setObjectName("sim_sec_cnt_max_fld")
        self.roll_increm_yr_fld = QtWidgets.QLineEdit(BT_input_window)
        self.roll_increm_yr_fld.setGeometry(QtCore.QRect(170, 300, 161, 20))
        self.roll_increm_yr_fld.setObjectName("roll_increm_yr_fld")
        self.label_10 = QtWidgets.QLabel(BT_input_window)
        self.label_10.setGeometry(QtCore.QRect(20, 420, 91, 16))
        self.label_10.setObjectName("label_10")
        self.initial_NAV_fld = QtWidgets.QLineEdit(BT_input_window)
        self.initial_NAV_fld.setGeometry(QtCore.QRect(170, 420, 161, 20))
        self.initial_NAV_fld.setObjectName("initial_NAV_fld")
        self.test_method_cb = QtWidgets.QComboBox(BT_input_window)
        self.test_method_cb.setGeometry(QtCore.QRect(170, 60, 161, 22))
        self.test_method_cb.setObjectName("test_method_cb")
        self.test_method_cb.addItem("")
        self.test_method_cb.addItem("")
        self.label_11 = QtWidgets.QLabel(BT_input_window)
        self.label_11.setGeometry(QtCore.QRect(160, 260, 31, 16))
        self.label_11.setObjectName("label_11")
        self.label_12 = QtWidgets.QLabel(BT_input_window)
        self.label_12.setGeometry(QtCore.QRect(250, 260, 31, 16))
        self.label_12.setObjectName("label_12")
        self.optim_param_cb = QtWidgets.QComboBox(BT_input_window)
        self.optim_param_cb.setGeometry(QtCore.QRect(170, 220, 161, 22))
        self.optim_param_cb.setObjectName("optim_param_cb")
        self.optim_param_cb.addItem("")
        self.label_13 = QtWidgets.QLabel(BT_input_window)
        self.label_13.setGeometry(QtCore.QRect(20, 20, 321, 21))
        font = QtGui.QFont()
        font.setFamily("Calibri")
        font.setPointSize(14)
        font.setBold(True)
        font.setWeight(75)
        self.label_13.setFont(font)
        self.label_13.setObjectName("label_13")
        self.progressBar = QtWidgets.QProgressBar(BT_input_window)
        self.progressBar.setGeometry(QtCore.QRect(20, 500, 336, 23))
        self.progressBar.setProperty("value", 0)
        self.progressBar.setObjectName("progressBar")
        
        self.retranslateUi(BT_input_window)
        #self.buttonBox.accepted.connect(BT_input_window.accept) # type: ignore
        #self.buttonBox.rejected.connect(BT_input_window.reject) # type: ignore
        QtCore.QMetaObject.connectSlotsByName(BT_input_window)
        
        self.pushButton.clicked.connect(self.runBacktest)
        self.test_method_cb.currentTextChanged.connect(self.fldEnableDisable)

    def retranslateUi(self, BT_input_window):
        _translate = QtCore.QCoreApplication.translate
        BT_input_window.setWindowTitle(_translate("BT_input_window", "For Interview Purpose Only, Andy Chan"))
        self.pushButton.setText(_translate("BT_input_window", "Backtest"))
        self.test_beg_yr_fld.setText(_translate("BT_input_window", "2008"))
        self.train_set_period_fld.setText(_translate("BT_input_window", "0"))
        self.label.setText(_translate("BT_input_window", "Test Method"))
        self.label_2.setText(_translate("BT_input_window", "Test begining year"))
        self.label_3.setText(_translate("BT_input_window", "Train Set Period"))
        self.label_4.setText(_translate("BT_input_window", "Sector Count Range"))
        self.label_5.setText(_translate("BT_input_window", "Parameter(s) to Optimize"))
        self.test_set_period_fld.setText(_translate("BT_input_window", "11"))
        self.sim_sec_cnt_min_fld.setText(_translate("BT_input_window", "3"))
        self.label_6.setText(_translate("BT_input_window", "Test Set Period"))
        self.label_7.setText(_translate("BT_input_window", "Rolling Frequency"))
        self.label_8.setText(_translate("BT_input_window", "Rolling Incremental Year"))
        self.label_9.setText(_translate("BT_input_window", "No. Sector Chosen"))
        self.roll_freq_fld.setText(_translate("BT_input_window", "1"))
        self.num_of_sec_chosen_fld.setText(_translate("BT_input_window", "4"))
        self.sim_sec_cnt_max_fld.setText(_translate("BT_input_window", "8"))
        self.roll_increm_yr_fld.setText(_translate("BT_input_window", "0"))
        self.label_10.setText(_translate("BT_input_window", "Initial NAV"))
        self.initial_NAV_fld.setText(_translate("BT_input_window", "100000"))
        self.test_method_cb.setItemText(0, _translate("BT_input_window", "single period"))
        self.test_method_cb.setItemText(1, _translate("BT_input_window", "rolling"))
        self.label_11.setText(_translate("BT_input_window", "Min."))
        self.label_12.setText(_translate("BT_input_window", "Max."))
        self.optim_param_cb.setItemText(0, _translate("BT_input_window", "sharpe"))
        self.label_13.setText(_translate("BT_input_window", "Backtest Input Window"))
        
    def fldEnableDisable(self):
        if self.test_method_cb.currentText() == "rolling":
            self.num_of_sec_chosen_fld.setEnabled(False)
            self.roll_increm_yr_fld.setEnabled(True)
            self.roll_freq_fld.setEnabled(True)
        elif self.test_method_cb.currentText() == "single period":
            self.roll_increm_yr_fld.setText('0')
            self.roll_increm_yr_fld.setEnabled(False)
            self.roll_freq_fld.setText('1')
            self.roll_freq_fld.setEnabled(False)
            self.num_of_sec_chosen_fld.setEnabled(True)
        
    def runBacktest(self):
        try:
            cfg.test_method = self.test_method_cb.currentText()
            cfg.test_beg_yr = int(self.test_beg_yr_fld.text())
            cfg.train_set_period = int(self.train_set_period_fld.text())
            cfg.test_set_period = int(self.test_set_period_fld.text())
            cfg.optim_param = self.optim_param_cb.currentText()
            cfg.sim_sec_cnt_min = int(self.sim_sec_cnt_min_fld.text())
            cfg.sim_sec_cnt_max = int(self.sim_sec_cnt_max_fld.text())
            cfg.roll_increm_yr = int(self.roll_increm_yr_fld.text())
            cfg.roll_freq = int(self.roll_freq_fld.text())
            cfg.num_of_sec_chosen = int(self.num_of_sec_chosen_fld.text())
            cfg.initial_NAV = int(self.initial_NAV_fld.text())

        except ValueError:
            self.formatWarning()

        else:
            num_inputs_list = [cfg.test_beg_yr, cfg.train_set_period, cfg.test_set_period, cfg.sim_sec_cnt_min, \
                          cfg.sim_sec_cnt_max, cfg.roll_increm_yr, cfg.roll_freq, \
                              cfg.num_of_sec_chosen, cfg.initial_NAV]

            for _, item in enumerate(num_inputs_list):
                if item < 0:
                    warn_msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Data Value Inconsistency', 'Please input positive number')
                    warn_msg.exec_()
                    return
            if cfg.sim_sec_cnt_max > 11:
                warn_msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Data Value Inconsistency', 'Can only choose up to 11 sectors at maximum')
                warn_msg.exec_()
                return
            
            self.pushButton.setEnabled(False)
            progress = 0
            self.progressBar.setValue(progress)
            
            start_time = time.time()
            print("\n")
            print(cfg.mkt_idx_name, "BACK TEST", "start from", cfg.test_beg_yr)
            
            cfg.setupFolder('ssr')
            
            cfg.stats_summary = []
            cfg.fig_dict = {}
            
            for csv_key in cfg.pre_csv.keys():
                up.routing(csv_key)
                progress += 10
                self.progressBar.setValue(progress)
            
            if cfg.test_method == 'rolling':
                bts.rollWindowTest()
            elif cfg.test_method == 'single period':
                bts.oneTimeTest()
            self.progressBar.setValue(70)
    
            print("Backtesting Completed...")
            print("\n")
            print("--- Time used: %s seconds ---" % (round(time.time()-start_time, 2)))
            
            self.stats_window = QtWidgets.QDialog()
            self.ui2 = Ui_stats_window()
            self.ui2.setupUi(self.stats_window)
            self.ui2.showStatsInfo()
            self.ui2.showGraphs()
            self.stats_window.show()
            
            self.pushButton.setEnabled(True)
            self.progressBar.setValue(100)

    def formatWarning(self):
       warn_msg = QtWidgets.QMessageBox(QtWidgets.QMessageBox.Warning, 'Data Format Inconsistency', 'Please make sure data format is correct (e.g. no decimal, words)')
       warn_msg.exec_()


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    BT_input_window = QtWidgets.QDialog()
    ui = Ui_BT_input_window()
    ui.setupUi(BT_input_window)
    ui.fldEnableDisable()
    BT_input_window.show()
    sys.exit(app.exec_())
    
