import sys
from textwrap import wrap
from tkinter import VERTICAL
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QCheckBox, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider, QLabel, QLineEdit)
from matplotlib.ft2font import HORIZONTAL
from matplotlib.pyplot import connect, grid
import sympy as sy

from thermosim import*

class Werte:
    def __init__(self, tAussen, tWunsch, nIng, phiWunsch, mdot):
        self.tAussen = tAussen
        self.tWunsch = tWunsch
        self.nIng = nIng
        self.phiWunsch = phiWunsch
        self.kuehlmittel_is_co2 : bool = True
        self.gleichstrom : bool = True
        self.mdot = mdot
        self.IngBuero = Gebaüde(tAussen, tWunsch, nIng, phiWunsch)
        self.qWand = self.IngBuero.calcQWand()
        self.qIng = self.IngBuero.calcQ_Ing()
        self.xBuero = self.IngBuero.calcx()

    def calc_tE(self):
        tE = sy.symbols('tE')
        hIn = Mdot_Luft*Cp_Luft* self.tWunsch + Mdot_Luft * self.xBuero *(Cp_Dampf * self.tWunsch+ Rd)
        hOut = Mdot_Luft*Cp_Luft*tE + Mdot_Luft * self.xBuero  * (Cp_Dampf * tE + Rd)
        eq1 = sy.Eq((-1)*hOut + hIn + self.qIng + self.qWand, 0)
        sol_tE= float(sy.solve(eq1, tE)[0])
        return sol_tE

        
    def execute_propan(self):
        pass
    
    def execute_co2(self):
        pass
    
    def execute_calculation(self):
        ig = Gebaüde(self.tAussen, self.tWunsch, self.nIng, self.phiWunsch)
        if self.kuehlmittel_is_co2:
            self.execute_co2(ig)
        else:
            self.execute_propan(ig)
    
werte = Werte(0,0,0,0,0)

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__(None)
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
        self.IngBüro = Gebaüde
       
        self.anzeige1 = QLabel(self)
        self.anzeige2 = QLabel(self)
        self.anzeige3 = QLabel(self)
        self.anzeige4 = QLabel(self)

        grid = QGridLayout()
        grid.addWidget(self.generate_regler_box(self.ingRegler, "Ingeneuranzahl", 0, 50), 0, 0)
        grid.addWidget(self.anzeige1,0,1)
        grid.addWidget(self.generate_regler_box(self.twRegler, "Wunschtemperatur", 12, 18), 1, 0)
        grid.addWidget(self.anzeige2,1,1)
        grid.addWidget(self.generate_regler_box(self.taRegler, "Aussentemperatur", 20, 42), 2, 0)
        grid.addWidget(self.anzeige3,2,1)
        grid.addWidget(self.generate_regler_box(self.phiRegler, "\u03C6-Wunsch", 0, 100), 3, 0)
        grid.addWidget(self.anzeige4,3,1)
        grid.addWidget(self.b1, 4, 0)
        self.setLayout(grid)

        self.setWindowTitle("Einstellung Parameter")

    def generate_regler_box(self, slider, name, min, max):
        box = QGroupBox(name)
        slider.setMinimum(min)
        slider.setMaximum(max)
        slider.valueChanged.connect(self.attributzuweisung)
        vbox = QVBoxLayout()
        vbox.addWidget(slider)
        box.setLayout(vbox)
        return box

    def getwert_R1(self):
       wertR1 = str(self.ingRegler.value())
       self.anzeige1.setText(wertR1 + " Ingenieure")

    def getwert_R2(self):
       wertR2 = str(self.twRegler.value())
       self.anzeige2.setText(wertR2 + "°C")

    def getwert_R3(self):
        wertR3 = str(self.taRegler.value())
        self.anzeige3.setText(wertR3 + "°C")

    def getwert_R4(self):
        wertR4 = str(self.phiRegler.value())
        self.anzeige4.setText(wertR4 + "%")

    def attributzuweisung(self):
        global werte
        werte.tAussen = self.taRegler.value()
        werte.tWunsch = self.twRegler.value()
        werte.nIng = self.ingRegler.value()
        werte.phiWunsch = self.phiRegler.value()/100

    def b1_clicked(self):
        self.close()
        

class Window2(QWidget):
    def __init__(self):
        super(Window2, self).__init__(None)
        self.Propan_button = QPushButton("Propan")
        self.CO2_button = QPushButton("CO2")
        self.Propan_button.clicked.connect(self.close)
        self.CO2_button.clicked.connect(self.close)
        self.Win3 = PropanWindow()
        self.Win4 = CO2_Window()
        self.Propan_button.clicked.connect(self.Win3.show)
        self.CO2_button.clicked.connect(self.Win4.show)
        self.Regler5 = QSlider(Qt.Horizontal)
        self.anzeige5 = QLabel(self)
        self.Regler5.valueChanged.connect(self.getWertR5)

        self.anzQ = QLabel(self)

        grid = QGridLayout()
        grid.addWidget(self.Propan_button , 0, 0)
        grid.addWidget(self.CO2_button, 1, 0)
        grid.addWidget(self.Propanregler(),2,0)
        grid.addWidget(self.anzeige5,3,0)
        self.setLayout(grid)

        self.setWindowTitle("Wahl des Kältemittels")
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
         global werte
         werte.mdot = self.Regler5.value()/10000
         print(werte.mdot)

         wertR5 = self.Regler5.value()/10000
         self.anzeige5.setText("Der Massenstrom beträgt:" + str(wertR5) + "kg/s")
         return(wertR5)

class PropanWindow(QWidget):
   def __init__(self):
        super(PropanWindow, self).__init__(None)
        self.setWindowTitle("Simulationswerte für Propan")
        self.resize(400, 300)
        global werte
        self.fertigButt = QPushButton('Fertig')
        self.fertigButt.clicked.connect(self.fertig_clicked)

        grid = QGridLayout()
        grid.addWidget(self.fertigButt,0,0)
        self.setLayout(grid)
        


       


   def fertig_clicked(self):
    self.close()
   

class CO2_Window(QWidget):
   def __init__(self):
        super(CO2_Window, self).__init__(None)
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