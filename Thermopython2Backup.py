from ast import Eq, Pass
import fractions
from runpy import run_path
import numpy as np
import scipy as sp
import sympy as sy
import matplotlib as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import PillowWriter
import scipy.interpolate

#Stoffdaten Wasser
T_W = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
p_s = [0.0061, 0.0087, 0.0123, 0.170, 0.0234, 0.317, 0.0424, 0.0562, 0.0737, 0.0958, 0.1233, 0.1574, 0.1992]

p_s_interpol = scipy.interpolate.interp1d(T_W, p_s)

#Stoffdaten Propan
T_P = [-8.73, 1.73, 11.82, 31.89, 57.26, 66.83]
h_P_g= [565.09, 576.77, 587.59, 607.25, 626.02, 629.80]
h_P_f = [178.44, 204.33, 230.10, 284.09, 359.36, 390.79]

h_P_g_interpoation = scipy.interpolate.interp1d(T_P, h_P_g)
h_P_f_interpolation = scipy.interpolate.interp1d(T_P, h_P_f)

#Stoffdaten R134a

T_R = [10, 5, 0 , -5, -10, -15, -20, -25, -30, -35, -40]
r_R134a = 1

#Konstanten
Mdot_Luft = 2.2 #kg/s
P_Buero = 1.013 #bar
Cp_Luft = 1.006 #kJ/kg*K
Cp_Dampf = 1.92 #kJ/kg*K
Cp_CO2 = 0.8169 #kJ/kg*K
T_Ing = 36.5 #°C
Rd = 2500 #kJ/kg

class Gebaüde:
    def __init__(self, tAussen, tWunsch, nIng, phiWunsch):
        #Klassen-Variablen
        self.tAussen = tAussen
        self.tWunsch = tWunsch
        self.nIng = nIng
        self.phiWunsch = phiWunsch
       
    def calcQWand(tAussen, tWunsch):
        Y_Beton = 1.35 #[W/K*m]
        Y_Putz = 0.25 #[W/K*m]
        Y_Daemmung = 0.035 #[W/K*m]
        A_Wand = 400 #[m^2]
        Alpha_Wand = 5 #[W/Km^2]
        R_Beton = 0.36/(Y_Beton*A_Wand)
        R_Putz = 0.04/(Y_Putz*A_Wand)
        R_Daemmung = 0.02/(Y_Daemmung*A_Wand)
        R_ges = R_Beton + R_Putz + R_Daemmung
        k = ((Alpha_Wand)**(-1) + R_ges*A_Wand)**(-1)
        Q_Waende = 4*A_Wand*k*(tAussen - tWunsch)*10**(-3) #(kW)
        return Q_Waende

    def calcQ_Ing(nIng, tWunsch):
        Q_Ing = nIng * 2.7682*10**(-3) * 1.7 * (T_Ing - tWunsch) #[kW]
        return Q_Ing
        
    def calcx(tUnknown, phiWunsch):
        def calcpd(tUnknown, phiWunsch):
            pd = phiWunsch * p_s_interpol(tUnknown)
            return(pd)
        pd = calcpd(tUnknown, phiWunsch)
        xd = 0.622*pd/(1-pd)
        return(xd)

class Waermeuebertrager:
    def __init__(self, tE, xE, tWunsch):
        self.tE = tE
        self.xE = xE
        self.tWunsch = tWunsch

    def calcH_in(xE, tE):
        hIn = Mdot_Luft*Cp_Luft*tE + Mdot_Luft * xE * (Cp_Dampf * tE + Rd)
        return(hIn)

    def calcWÜ(xE, tE, tWunsch, rAM, mAM : float) -> float:
     xd_WÜ = (-mAM*rAM + Mdot_Luft*Cp_Luft*(tE-tWunsch) + Mdot_Luft*xE*(Cp_Dampf*tE+Rd))/(Cp_Dampf*tWunsch+Rd)
     p_d_WÜ =  xd_WÜ/(0.622+xd_WÜ)
     phi_WÜ_nach = p_d_WÜ/p_s_interpol(tWunsch)
     delta_x = xd_WÜ - xE(tWunsch)
     return xd_WÜ, p_d_WÜ, phi_WÜ_nach, delta_x

class Propan(Waermeuebertrager):
    def __init__(self, tE, xE, tWunsch):
        self.tE = tE
        self.xE = xE
        self.tWunsch = tWunsch

    def calcR_Propan(T):
        r = h_P_g_interpoation(T) - h_P_f_interpolation(T)
        return(r)
          
class R134a(Waermeuebertrager):
    def __init__(self, tE, xE, tWunsch):
        self.tE = tE
        self.xE = xE
        self.tWunsch = tWunsch 

class WaermeübertragerCO2:
    def __init__(self, mCO2, t1):
        self.mCO2 = mCO2
        self.t1 = t1

    def calcC(mCO2):
        w1 = Mdot_Luft * Cp_Luft
        w2 = mCO2 * Cp_CO2
        c1 = fractions(w1, w2)
        c2 = fractions(w2,w1)
        return c1,c2

    def calcT2(t1, h_in_wü, mCO2):
        t2 = t1 + h_in_wü/(Cp_CO2*mCO2)
        return t2

    def calcEpsilons(t1, t2, tw, sol_te):
        epsilon1 = (sol_te-tw)/(sol_te-t1)
        epsilon2 = (t2-t1)/(sol_te-t1)
        return epsilon1, epsilon2

    def calcThetas(epsilon1, epsilon2, n1, n2):
        theta1 = epsilon1/n1
        theta2 = epsilon2/n2
        return theta1,theta2

class Gegenstrom(WaermeübertragerCO2):
    def __init__(self, mCO2, t1):
       super().__init__(mCO2, t1)

    def calcNgegen(c1,c2,epsilon1, epsilon2):
        c = np.array[1-c1*epsilon1, 1-c2*epsilon2]
        e = np.array[1-epsilon1, 1-epsilon2]
        ce = np.array[1-c1*epsilon1, 1-c2*epsilon2]
        n1 = fractions(1,c[0])*np.log(fractions(e[0],ce[0]))
        n2 = fractions(1,c[1])*np.log(fractions(e[1],ce[1]))
        return n1,n2

class Gleichstrom(WaermeübertragerCO2):
    def __init__(self, mCO2, t1):
       super().__init__(mCO2, t1)
    
    def calcN_gleich(c1,c2,epsilon1, epsilon2):
        z = np.array[1+c1, 1+c2]
        s = np.array[1-epsilon1*z[0], 1-epsilon2*z[1]]
        n1 = fractions(s[0], z[0])
        n2 = fractions(s[1], z[1])
        return n1, n2
   
#Hauptprogramm
tA = 0
tW = 0
nIng = -1
phiWun = -1

while tA < 20 or tA > 42:
 print("Einhgabe Außentemperatur")
 tA = float(input().strip())

while tW < 12 or tW > 18:
 print("Eingabe Wunschtemperatur")
 tW = float(input().strip())

while nIng < 0 or nIng > 50:
 print("Eingabe Ingenieuranzahl")
 nIng = float(input().strip())

while phiWun < 0 or phiWun > 1:
 print("Eingabe Wunschfeuchte der Luft")
 phiWun = float(input().strip())


ingBuero = Gebaüde(tA, tW, nIng, phiWun)
qWand = ingBuero.calcQWand(tA, tW)
qIng = ingBuero.calcQ_Ing(self, nIng, tW)
xBuero = ingBuero.calcx(tW, phiWun)

#Lufttemperatur bei verlassen des Raumes
tE = sy.symbols('tE')
hIn = Mdot_Luft*Cp_Luft*tW + Mdot_Luft * xBuero*(Cp_Dampf * tW+ Rd)
hOut = Mdot_Luft*Cp_Luft*tE + Mdot_Luft * xBuero * (Cp_Dampf * tE + Rd)
eq1 = sy.Eq((-1)*hOut + hIn + qIng + qWand, 0)
sol_tE= float(sy.solve(eq1, tE)[0])

#Auswahl des Kühlmittels 
w = "Kohlenstoffdioxid"
x = "Propan"
y = "R134a"

print("Eingabe des Arbeitsmittels")
z = input()
while x != z or y != z or w != z:       
 print("Gebe Arbeitsmittel ein")
 z = input()

if x == z:
    PropWU = Propan(sol_tE, xBuero, tW)
    tM = (sol_tE+tW)/2
    rProp = PropWU.calcR_Propan(tM)

    print("Eingabe Propanmassenstrom")
    mProp = float(input().strip())
    xd_WÜ, p_d_WÜ, phi_WÜ_nach, delta_x = PropWU.calcWÜ(xBuero, tE, tW, rProp, mProp)

    while xd_WÜ < 0:
        print("Der Propanmassenstrom ist zu groß, bitte erneut eingeben")
        mProp = float(input().strip())
        x_d_WÜ, p_d_WÜ, phi_WÜ_nach, delta_x = PropWU.calcWÜ(xBuero, tE, tW, rProp, mProp)
        
        if phi_WÜ_nach > phiWun or phi_WÜ_nach == phiWun:
         print("Es kondensiert ein Massenstrom von ", Mdot_Luft*delta_x, "kg/s im Wärmeübertrager aus")
        if phi_WÜ_nach < phiWun:
         print("Es muss ein Massenstrom von", -1*Mdot_Luft*delta_x, "eingespritzt werden")
    

if y == z:
    R134aWU = R134a(sol_tE, xBuero, tW)
    tM = (sol_tE+tW)/2
    "rProp = PropWU.calcR_Propan(tM)"

    print("Eingabe Propanmassenstrom")
    mPR142a = float(input().strip())
    xd_WÜ, p_d_WÜ, phi_WÜ_nach, delta_x = R134aWU.calcWÜ(xBuero, tE, tW, rProp, mPR142a)

    while xd_WÜ < 0:
        print("Der 1,1,1,2 Tetrafluroethanmassenstrom ist zu groß, bitte erneut eingeben")
        mPR142a = float(input().strip())
        x_d_WÜ, p_d_WÜ, phi_WÜ_nach, delta_x = R134aWU.calcWÜ(xBuero, tE, tW, r_R134a, mPR142a)
        
        if phi_WÜ_nach > phiWun or phi_WÜ_nach == phiWun:
         print("Es kondensiert ein Massenstrom von ", Mdot_Luft*delta_x, "kg/s im Wärmeübertrager aus")
        if phi_WÜ_nach < phiWun:
         print("Es muss ein Massenstrom von", -1*Mdot_Luft*delta_x, "eingespritzt werden")

if z == w:
    print('Eingabe Gleichstrom oder Gegenstrom')
    u = input()
    while u != 'Gleichstrom' or u != 'Gegenstrom':
     print('WÜ erneut eingeben')
     u = input()

    print("Eingabe CO2 Massenstrom")
    mC02 = float(input().strip())
    while mC02 <= 0:
        print("Eingabe CO2 Massenstrom")
        mC02 = float(input().strip())
    
    #Allgemeine WÜ-Formeln mit hOut->Enthalpiestrom aus Buero
    c1, c2 = WaermeübertragerCO2.calcC(mC02)[0], WaermeübertragerCO2.calcC(mC02)[1]
    t2 = WaermeübertragerCO2.calcT2(sol_tE, hOut, mC02)
    eps1, eps2 = WaermeübertragerCO2.calcEpsilons(5,t2,tW,sol_tE)[0], WaermeübertragerCO2.calcEpsilons(5,t2,tW,sol_tE)[1]

    if u == 'Gleichstrom':
        n1, n2 = Gleichstrom.calcN_gleich(c1, c2, eps1, eps2)[0], Gleichstrom.calcN_gleich(c1, c2, eps1, eps2)[1]
        the1, the2 = Gleichstrom.calcThetas(eps1, eps2, n1, n2)[0], Gleichstrom.calcThetas(eps1, eps2, n1, n2)[1]  
        print(c1,c2,eps1,eps2,n1,n2, the1, the2)

    elif u == 'Gegenstrom':
        n1, n2 = Gegenstrom.calcNgegen(c1, c2, eps1, eps2)[0], Gegenstrom.calcNgegen(c1, c2, eps1, eps2)[1]
        the1, the2 = Gegenstrom.calcThetas(eps1, eps2, n1, n2)[0], Gegenstrom.calcThetas(eps1, eps2, n1, n2)[1]
        print(c1,c2,eps1,eps2,n1,n2, the1, the2)

    else:
        print('Fehlerhafte Eingabe')







  

        


     




