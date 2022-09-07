import sys
from textwrap import wrap
from tkinter import VERTICAL
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QGridLayout, QGroupBox,
                             QMenu, QPushButton, QRadioButton, QVBoxLayout, QWidget, QSlider, QLabel)
from matplotlib.ft2font import HORIZONTAL
from matplotlib.pyplot import connect, grid

from Endtemperaturmethode import*

class Berechnung:
    def __init__(self):
        self.tAussen = 18
        self.tWunsch = 20
        self.nIng = 10
        self.phiWunsch = 0.1
        self.kuehlmittel_is_co2 : bool = True
        self.gleichstrom : bool = True
        self.mdot = 1
        self.phiOut = 0
        self.delta_x = 0

    def set_ta(self, ta):
        self.ta = ta

    def berechne_buero(self) -> str:
        self.IngBuero = Gebaüde(self.tAussen, self.tWunsch, self.nIng, self.phiWunsch)
        self.qWand = self.IngBuero.calcQWand()
        self.qIng = self.IngBuero.calcQ_Ing()
        self.xBuero = self.IngBuero.calcx()
        self.tEnde = self.IngBuero.calc_tEnde()
        self.Waermeübertrager = Waermeuebertrager(self.tEnde, self.xBuero, self.tWunsch)
        self.hIn = self.Waermeübertrager.calcH_in()

        result = self.berechne_CO2() if self.kuehlmittel_is_co2 else self.berechne_propan() 
        return result + "<br>" + self.get_wasser_kondensation_message()

    def get_wasser_kondensation_message(self):
        if Mdot_Luft * self.delta_x < 1:
            return f"""Es muss ein Massenstrom von {"{:1.2}".format(-Mdot_Luft * self.delta_x)}kg/s eingespritzt werden."""
        else:
            return f"""Es kondensiert ein Massenstrom von {"{:1.2}".format(Mdot_Luft * self.delta_x)}kg/s im Wärmeübertrager aus."""

        
    def berechne_propan(self) -> str:
        self.Propan = Propan(self.xBuero, self.tEnde, self.tWunsch)
        self.tMittel = 0.5*(self.tEnde + self. tWunsch)
        self.rPropan = self.Propan.calcR_Propan(self.tMittel)
        self.x, self.p, self.phiOut, self.delta_x = self.Propan.calcWÜ(self.rPropan, self.mdot)
        return f"""
    <code>Endtemperatur:  {"{:1.2f}".format(self.tEnde)}</code><br>
    <code>x:  {"{:1.2f}".format(self.x)}</code><br>
    <code>p:  {"{:1.2f}".format(self.p)}</code><br>
    <code>φ:  {"{:1.2f}".format(self.phiOut)}</code><br>
    <code>Δx: {"{:1.2f}".format(self.delta_x)}</code><br>
        """

    def berechne_CO2(self) -> str:
        self.WaermeübertragerCO2 = WaermeübertragerCO2(self.mdot, self.gleichstrom)
        t2 = self.WaermeübertragerCO2.calcT2(self.hIn, self.mdot)
        self.cValue = self.WaermeübertragerCO2.calcC(self.mdot)
        self.epsilons = self.WaermeübertragerCO2.calcEpsilons(t2, self.tWunsch, self.tEnde)
        self.nvalue = self.WaermeübertragerCO2.calcParameters(self.cValue[0], self.cValue[1], self.epsilons[0], self.epsilons[1])
        self.thetas = self.WaermeübertragerCO2.calcThetas(self.epsilons[0], self.epsilons[1], self.nvalue[0], self.nvalue[1])
        if self.gleichstrom == True: 
            self.WaermeübertragerCO2.gleichstrom = True
        else:
            self.WaermeübertragerCO2.gleichstrom = False
        return f"""
    <code>Endtemperatur: {"{:1.2f}".format(self.tEnde)}</code><br>
    <code>θ1: {"{:1.2f}".format(self.thetas[0])},  θ2: {"{:1.2f}".format(self.thetas[1])}</code><br>
    <code>ε1: {"{:1.2f}".format(self.epsilons[0])}, ε2: {"{:1.2f}".format(self.epsilons[1])}</code><br>
    <code>n1: {"{:1.2f}".format(self.nvalue[0])},  n2: {"{:1.2f}".format(self.nvalue[1])}</code><br>
        """

class Window(QWidget):
    def __init__(self):
        super(Window, self).__init__(None)
        self.calculator = Berechnung()
        self.IngBüro = Gebaüde
        self.result = "Ergebniss"
        self.ingRegler = QSlider(Qt.Horizontal)
        self.twRegler = QSlider(Qt.Horizontal)
        self.taRegler = QSlider(Qt.Horizontal)
        self.phiRegler = QSlider(Qt.Horizontal)
        self.massRegler = QSlider(Qt.Horizontal)
        self.ingRegler.valueChanged.connect(self.getwert_R1)
        self.twRegler.valueChanged.connect(self.getwert_R2)
        self.taRegler.valueChanged.connect(self.getwert_R3) 
        self.phiRegler.valueChanged.connect(self.getwert_R4)
        self.massRegler.valueChanged.connect(self.getWert_R5)
        self.massRegler.valueChanged.connect(self.attributzuweisung)#


       
        self.anzeige1 = QLabel(self)
        self.anzeige2 = QLabel(self)
        self.anzeige3 = QLabel(self)
        self.anzeige4 = QLabel(self)
        self.anzeige5 = QLabel(self)
        self.anzeige6 = QLabel(self)

        self.setWindowTitle("Klimaanlagen Simulation")

        self.mass_selector = self.generate_co2_mass_selector()
        self.result_field = self.generate_result_field()

        self.grid = QGridLayout()
        self.grid.addWidget(self.generate_slider_area(), 0,0,3,1)
        self.grid.addWidget(self.generate_coolant_selector(),0,1)
        self.grid.addWidget(self.mass_selector, 1,1)
        self.grid.addWidget(self.result_field, 2,1)
        self.setLayout(self.grid)

    def generate_regler_box(self, slider, name, min, max, anzeige):  #      
        box = QGroupBox(name)
        slider.setMinimum(min)#
        slider.setMaximum(max)#
        slider.valueChanged.connect(self.attributzuweisung)
        vbox = QVBoxLayout()
        vbox.addWidget(slider)
        vbox.addWidget(anzeige)
        box.setLayout(vbox)
        return box

    def generate_slider_area(self):
        groupBox = QGroupBox("Parametereinstellung")
        vBox = QVBoxLayout()
        vBox.addWidget(self.generate_regler_box(self.ingRegler, "Ingeneuranzahl",0, 50, self.anzeige1))
        vBox.addWidget(self.generate_regler_box(self.twRegler, "Wunschtemperatur",12, 18, self.anzeige2))
        vBox.addWidget(self.generate_regler_box(self.taRegler, "Aussentemperatur",20, 42, self.anzeige3))
        vBox.addWidget(self.generate_regler_box(self.phiRegler, "\u03C6-Wunsch",0, 100, self.anzeige4))
        groupBox.setLayout(vBox)
        return groupBox

    def toggle_mass_selector_field(self, co2):
        self.calculator.kuehlmittel_is_co2 = co2
        self.grid.removeWidget(self.mass_selector)
        if co2:
            self.mass_selector = self.generate_co2_mass_selector()
        else:
            self.mass_selector = self.generate_propan_mass_selector()
        self.grid.addWidget(self.mass_selector, 1,1)


    def update_result_field(self):
        self.grid.removeWidget(self.result_field)
        self.result_field = self.generate_result_field()
        self.grid.addWidget(self.result_field, 2,1)

    def generate_coolant_selector(self):
        groupBox = QGroupBox("Kühlmittelauswahl")
        radio1 = QRadioButton("C02")
        radio2 = QRadioButton("Propan")
        
        radio1.toggled.connect(self.set_KuehlmittelTrue)
        radio2.toggled.connect(self.set_KuehlmittelFalse)
        radio1.toggled.connect(self.toggle_mass_selector_field)
        radio1.setChecked(True)

        vbox = QVBoxLayout()
        vbox.addWidget(radio1)
        vbox.addWidget(radio2)
        vbox.addWidget(self.generate_mass_regler())
        vbox.addWidget(self.anzeige5)
        vbox.addStretch(1)
        groupBox.setLayout(vbox)
        return groupBox


    def set_KuehlmittelTrue(self):
        self.calculator.kuehlmittel_is_co2 == True
        self.attributzuweisung()
        return self.calculator.kuehlmittel_is_co2

    def set_KuehlmittelFalse(self):
        self.calculator.kuehlmittel_is_co2 == False
        self.attributzuweisung
        return self.calculator.kuehlmittel_is_co2 

    def set_GleichstromTrue(self):
        self.calculator.kuehlmittel_is_co2 == True
        return self.calculator.kuehlmittel_is_co2

    def set_GleichstromFalse(self):
        self.calculator.kuehlmittel_is_co2 == False
        return self.calculator.kuehlmittel_is_co2

    def generate_propan_mass_selector(self):
        box = QGroupBox("Massenstrom")
        self.anzeige6 = QLabel(self)
        self.b3 = QPushButton('Gegenstromwärmeübertrager')
        self.b4 = QPushButton('Gleichstromwärmeübertrager')

        #self.b3.clicked.connect(self.b3_clicked)
        self.b3.clicked.connect(lambda : self.calculator.gleichstrom == False)
        self.b3.clicked.connect(self.attributzuweisung)
        #self.b4.clicked.connect(self.b4_clicked)
        self.b4.clicked.connect(lambda : self.calculator.gleichstrom == True)
        self.b4.clicked.connect(self.attributzuweisung)
        


        grid = QGridLayout()
        grid.addWidget(self.b3,2,0)
        grid.addWidget(self.b4,2,1)
        box.setLayout(grid)
        return box

    def generate_co2_mass_selector(self):
        box = QGroupBox("Wärmeübertragerauswahl")
        self.anzeige6 = QLabel(self)
        self.b3 = QPushButton('Gegenstromwärmeübertrager')
        self.b4 = QPushButton('Gleichstromwärmeübertrager')
        #self.b3.clicked.connect(self.b3_clicked)
        self.b3.clicked.connect(self.set_GleichstromFalse)
        self.b3.clicked.connect(self.attributzuweisung)
        #self.b4.clicked.connect(self.b4_clicked)
        self.b4.clicked.connect(self.set_GleichstromTrue)
        self.b4.clicked.connect(self.attributzuweisung)

        grid = QGridLayout()
        grid.addWidget(self.b3,2,0)
        grid.addWidget(self.b4,2,1)
        box.setLayout(grid)
        return box          

    def getwert_R1(self):
       wertR1 = str(self.ingRegler.value())
       self.anzeige1.setText("<code>" + wertR1 + "</code> Ingenieure")

    def getwert_R2(self):
       wertR2 = str(self.twRegler.value())
       self.anzeige2.setText("<code>" + wertR2 + "</code>°C")

    def getwert_R3(self):
        wertR3 = str(self.taRegler.value())
        self.anzeige3.setText("<code>" + wertR3 + "</code>°C")

    def getwert_R4(self):
        wertR4 = str(self.phiRegler.value())
        self.anzeige4.setText("<code>" + wertR4 + "</code>%")

    def getWert_R5(self):
         self.calculator.mdot = self.massRegler.value()/10000
         print(self.calculator.mdot)
         wertR5 = self.massRegler.value()/100
         self.anzeige5.setText("Der Massenstrom beträgt: <code>" + "{:1.4f}".format(wertR5) + "</code>kg/s")
         return(wertR5)


    def generate_mass_regler(self):
        pRegler = QGroupBox()
        vbox = QVBoxLayout()
        self.massRegler.setMinimum(1)
        self.massRegler.setMaximum(5000000)
        vbox.addWidget(self.massRegler)
        pRegler.setLayout(vbox)
        return pRegler
       


    def generate_result_field(self):
        groupBox = QGroupBox("Ergebniss")
        vBox = QVBoxLayout()
        vBox.addWidget(QLabel(self.result))
        groupBox.setLayout(vBox)
        return groupBox

    def attributzuweisung(self):
        self.calculator.tAussen = self.taRegler.value()
        self.calculator.tWunsch = self.twRegler.value()
        self.calculator.nIng = self.ingRegler.value()
        self.calculator.phiWunsch = self.phiRegler.value()/100
        self.result = self.calculator.berechne_buero()
        self.update_result_field()#

    
    def b1_clicked(self):
        self.close()
        return





        
        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Window()
    ex.show()
    sys.exit(app.exec_())
