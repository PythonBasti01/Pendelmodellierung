import sys
from tkinter import VERTICAL
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider, QLabel, QLineEdit)
from matplotlib.ft2font import HORIZONTAL
from matplotlib.pyplot import connect, grid
import sympy as sym
import math
import scipy.interpolate

#Stoffdaten Wasser
T_W = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
p_s = [0.0061, 0.0087, 0.0123, 0.170, 0.0234, 0.317, 0.0424, 0.0562, 0.0737, 0.0958, 0.1233, 0.1574, 0.1992]

p_s_interpol = scipy.interpolate.interp1d(T_W, p_s)

#Stoffdaten Propan
T_P = [-8.73, 1.73, 11.82, 31.89, 57.26, 66.83]
h_P_g= [565.09, 576.77, 587.59, 607.25, 626.02, 629.80]
h_P_f = [178.44, 204.33, 230.10, 284.09, 359.36, 390.79]

#Konstanten
Mdot_Luft = 2.2 #kg/s
Cp_Luft = 1.006 #kJ/kg*K
Cp_Dampf = 1.92 #kJ/kg*K
Rd = 2500 #kJ/kg

class Gebaüde:
    def __init__(self, tAussen, tWunsch, nIng, phiWunsch):
        #Klassen-Variablen
        self.tAussen = tAussen
        self.tWunsch = tWunsch
        self.nIng = nIng
        self.phiWunsch = phiWunsch

        def calc_k(A_Wand):
            Y_Beton = 1.35 #[W/K*m]
            Y_Putz = 0.25 #[W/K*m]
            Y_Daemmung = 0.035 #[W/K*m]
            Alpha_Wand = 5 #[W/Km^2]
            R_Beton = 0.36/(Y_Beton*A_Wand)
            R_Putz = 0.04/(Y_Putz*A_Wand)
            R_Daemmung = 0.02/(Y_Daemmung*A_Wand)
            R_ges = R_Beton + R_Putz +R_Daemmung
            return ((Alpha_Wand)**(-1) + R_ges*A_Wand)**(-1)
       
        self.T_Ing = 36.5 #°C
        self.A_Wand = 400 #[m^2]
        self.k = calc_k(self.A_Wand)

        
    def calcQWand(self):
        return 4*self.A_Wand*self.k*(self.tAussen - self.tWunsch)*10**(-3) #(kW)

    def calcQ_Ing(self):
        return self.nIng * 2.7682*10**(-3) * 1.7 * (self.T_Ing - self.tWunsch) #[kW]
        
    # absolute feuchte
    def calcx(self):
        pd = self.phiWunsch * p_s_interpol(self.tWunsch)
        xd = 0.622*pd/(1-pd)
        return xd
    
    def calc(self):
        return self.calcQWand(), self.calcQ_Ing(), self.calcx()

class Waermeuebertrager:
    def __init__(self, tE, xE, tWunsch):
        self.tE = tE
        self.xE = xE
        self.tWunsch = tWunsch

    def calcH_in(self):
        return  Mdot_Luft*Cp_Luft*self.tE + Mdot_Luft * self.xE * (Cp_Dampf * self.tE + Rd)

    def calcWÜ(self, rAM, mAM):
     xd_WÜ = (-mAM*rAM + Mdot_Luft*Cp_Luft*(self.tE-self.tWunsch) + Mdot_Luft*self.xE*(Cp_Dampf*self.tE+Rd))/(Cp_Dampf*self.tWunsch+Rd)
     p_d_WÜ =  xd_WÜ/(0.622+xd_WÜ)
     phi_WÜ_nach = p_d_WÜ/p_s_interpol(self.tWunsch)
     delta_x = xd_WÜ - self.xE
     return xd_WÜ, p_d_WÜ, phi_WÜ_nach, delta_x

class Propan(Waermeuebertrager):
    def __init__(self, tE, xE, tWunsch):
        super().__init__(tE, xE, tWunsch)
        self.h_P_g_interpoation = scipy.interpolate.interp1d(T_P, h_P_g)
        self.h_P_f_interpolation = scipy.interpolate.interp1d(T_P, h_P_f)

    def calcR_Propan(self, T):
        return self.h_P_g_interpoation(T) - self.h_P_f_interpolation(T)
          
class WaermeübertragerCO2:
    def __init__(self, mCO2, gleichstrom):
        self.mCO2 = mCO2
        self.t1 = 5 # C
        self.Cp_CO2 = 0.8169 #kJ/kg*K
        self.gleichstrom = gleichstrom

    def calcC(self, mCO2):
        w1 = Mdot_Luft * Cp_Luft
        w2 = mCO2 * self.Cp_CO2
        return w1/w2, w2/w1

    def calcT2(self, t1, h_in_wü, mCO2):
        return t1 + h_in_wü/(self.Cp_CO2*mCO2)

    def calcEpsilons(self, t1, t2, tw, sol_te):
        epsilon1 = (sol_te-tw)/(sol_te-t1)
        epsilon2 = (t2-t1)/(sol_te-t1)
        return epsilon1, epsilon2

    def calcThetas(self, epsilon1, epsilon2, n1, n2):
        theta1 = epsilon1/n1
        theta2 = epsilon2/n2
        return theta1,theta2

    def calcParameters(self, c1, c2, epsilon1, epsilon2):
        
        def calcGegenstrom():
            c = [1-c1*epsilon1, 1-c2*epsilon2]
            e = [1-epsilon1, 1-epsilon2]
            ce = [1-c1*epsilon1, 1-c2*epsilon2]
            n1 = 1/c[0] * math.log(e[0] / ce[0])
            n2 = 1/c[1] * math.log(e[1] / ce[1])
            return n1,n2

        def calcGleichstrom():
            z = [1+c1, 1+c2]
            s = [1-epsilon1*z[0], 1-epsilon2*z[1]]
            n1 = s[0]/ z[0]
            n2 = s[1]/ z[1]
            return n1, n2
        
        return calcGleichstrom() if self.gleichstrom else calcGegenstrom()

#Konstanten
Mdot_Luft = 2.2 #kg/s
Cp_Luft = 1.006 #kJ/kg*K
Cp_Dampf = 1.92 #kJ/kg*K
Rd = 2500 #kJ/kg

ingGebäude = Gebaüde

class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.ingRegler = QSlider(Qt.Horizontal)
        self.twRegler = QSlider(Qt.Horizontal)
        self.taRegler = QSlider(Qt.Horizontal)
        self.phiRegler = QSlider(Qt.Horizontal)
        self.b1 = QPushButton("Fertig")
        self.ingRegler.valueChanged.connect(self.getwert_R1)
        self.twRegler.valueChanged.connect(self.getwert_R2)
        self.taRegler.valueChanged.connect(self.getwert_R3) 
        self.phiRegler.valueChanged.connect(self.getwert_R4)
        self.b1.clicked.connect(self.b1_clicked)
        self.Win2 = Window2()
        self.b1.clicked.connect(self.Win2.show)
        self.ingRegler.valueChanged[int].connect(self.Attributzuweisung)
        self.twRegler.valueChanged[int].connect(self.Attributzuweisung)
        self.taRegler.valueChanged[int].connect(self.Attributzuweisung)
        self.phiRegler.valueChanged[int].connect(self.Attributzuweisung)
        self.IngBüro = Gebaüde
       

        self.anzeige1 = QLabel(self)
        self.anzeige2 = QLabel(self)
        self.anzeige3 = QLabel(self)
        self.anzeige4 = QLabel(self)

        grid = QGridLayout()
        grid.addWidget(self.Regler1(), 0, 0)
        grid.addWidget(self.anzeige1,0,1)
        grid.addWidget(self.Regler2(), 1, 0)
        grid.addWidget(self.anzeige2,1,1)
        grid.addWidget(self.Regler3(), 2, 0)
        grid.addWidget(self.anzeige3,2,1)
        grid.addWidget(self.Regler4(), 3, 0)
        grid.addWidget(self.anzeige4,3,1)
        grid.addWidget(self.b1, 4, 0)
        self.setLayout(grid)

        self.setWindowTitle("Einstellung Parameter")

    def Regler1(self):
        regler1 = QGroupBox("Ingenieuranzahl")
        self.ingRegler.setMinimum(0)
        self.ingRegler.setMaximum(50)
        vbox = QVBoxLayout()
        vbox.addWidget(self.ingRegler)
        regler1.setLayout(vbox)

        return regler1

    def Regler2(self):
        regler2 = QGroupBox("Wunschtemperatur")
        self.twRegler.setMinimum(12)
        self.twRegler.setMaximum(18)
        r2Box = QVBoxLayout()
        r2Box.addWidget(self.twRegler)
        regler2.setLayout(r2Box)

        return regler2

    def Regler3(self):
        regler3 = QGroupBox("Außentemperatur")
        vbox = QVBoxLayout()
        self.taRegler.setMinimum(20)
        self.taRegler.setMaximum(42)
        vbox.addWidget(self.taRegler)
        regler3.setLayout(vbox)

        return regler3

    def Regler4(self):
        Regler4 = QGroupBox("\u03C6-Wunsch")
        self.phiRegler.setMinimum(0)
        self.phiRegler.setMaximum(100)
        vbox = QVBoxLayout()
        vbox.addWidget(self.phiRegler)
        Regler4.setLayout(vbox)

        return Regler4

    def getwert_R1(self):
       wertR1 = str(self.ingRegler.value())
       self.anzeige1.setText(wertR1)

    def getwert_R2(self):
       wertR2 = str(self.twRegler.value())
       self.anzeige2.setText(wertR2)

    def getwert_R3(self):
        wertR3 = str(self.taRegler.value())
        self.anzeige3.setText(wertR3)

    def getwert_R4(self):
        wertR4 = str(self.phiRegler.value())
        self.anzeige4.setText(wertR4)

    def Attributzuweisung(self):
        wR1 = self.ingRegler.value()
        wR2 = self.twRegler.value()
        wR3 = self.taRegler.value()
        wR4 = self.phiRegler.value()/100
        ingGebäude(wR1,wR2,wR3,wR4)

    def b1_clicked(self):
        self.close()
        

class Window2(Window):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.Propan_button = QPushButton("Propan")
        self.CO2_button = QPushButton("CO2")
        self.Propan_button.clicked.connect(self.select_Propan)
        self.CO2_button.clicked.connect(self.select_CO2)
        self.Win3 = Window3()
        self.Win4 = Window4()
        self.Propan_button.clicked.connect(self.Win3.show)
        self.CO2_button.clicked.connect(self.Win4.show)

        self.anzQ = QLabel(self)

        grid = QGridLayout()
        grid.addWidget(self.Propan_button , 0, 0)
        grid.addWidget(self.CO2_button, 0, 1)
        self.setLayout(grid)

        self.setWindowTitle("Wahl des Kältemittels")
        self.resize(400, 300)

    def select_Propan(self):
        self.close()

    def select_CO2(self):
        self.close()
    

class Window3(Window):
   def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.Regler5 = QSlider(Qt.Vertical)
        self.anzeige5 = QLabel(self)
        self.b2 = QPushButton('Fertig')
        self.b2.clicked.connect(self.b2_clicked)
        self.wW1 = Window.b1_clicked

        self.Regler5.valueChanged.connect(self.getWertR5)

        grid = QGridLayout()
        grid.addWidget(self.Propanregler(),0,0)
        grid.addWidget(self.anzeige5,0,1)
        grid.addWidget(self.b2,1,0)
        self.setLayout(grid)


        self.setWindowTitle("Prpanmassenstrom Regler")
        self.resize(400, 300)

   def Propanregler(self):
        pRegler = QGroupBox()
        vbox = QVBoxLayout()
        self.Regler5.setMinimum(1)
        self.Regler5.setMaximum(1000)
        vbox.addWidget(self.Regler5)
        pRegler.setLayout(vbox)
        return pRegler

   def getWertR5(self):
        wertR5 = self.Regler5.value()
        self.anzeige5.setText(str(wertR5))
        return(wertR5)

   def b2_clicked(self):
    wR5 = self.Regler5.value()
    self.close()
    return wR5

class Window4(Window):
   def __init__(self, parent=None):
        super(Window, self).__init__(parent)
        self.Regler6 = QSlider(Qt.Vertical)
        self.anzeige6 = QLabel(self)
        self.b3 = QPushButton('Gegenstromwärmeübertrager')
        self.b4 = QPushButton('Gleichstromwärmeübertrager')


        self.Regler6.valueChanged.connect(self.getWertR6)
        self.b3.clicked.connect(self.b3_clicked)
        self.b4.clicked.connect(self.b4_clicked)
       

        grid = QGridLayout()
        grid.addWidget(self.C02Regler(),0,0)
        grid.addWidget(self.anzeige6,0,1)
        grid.addWidget(self.b3,2,0)
        grid.addWidget(self.b4,2,1)
        self.setLayout(grid)

        self.setWindowTitle("CO2-Massenstromregler")


   def C02Regler(self):
    co2Regler = QGroupBox()
    vbox = QVBoxLayout()
    self.Regler6.setMinimum(1)
    self.Regler6.setMaximum(1000)
    vbox.addWidget(self.Regler6)
    co2Regler.setLayout(vbox)
    return co2Regler

   def getWertR6(self):
    wR6 = self.Regler6.value()
    self.anzeige6.setText(str(wR6))

   def b3_clicked(self): 
    wR6 = self.Regler6.value()
    self.close()
    return wR6

   def b4_clicked(self):
    wr6 = self.Regler6.value()
    self.close()
    return(wr6)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec_())