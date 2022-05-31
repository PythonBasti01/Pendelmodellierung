from ast import Eq
import fractions
import numpy as np
import scipy as sp
import sympy as sy
import matplotlib as plt
from matplotlib import animation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.animation import PillowWriter
import scipy.interpolate




#--------------------------------------------------------------------------------------------------------------------------------------
#Tabelle für Wasser
#--------------------------------------------------------------------------------------------------------------------------------------

T_W = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60]
p_s = [0.0061, 0.0087, 0.0123, 0.170, 0.0234, 0.317, 0.0424, 0.0562, 0.0737, 0.0958, 0.1233, 0.1574, 0.1992]

p_s_interpol = scipy.interpolate.interp1d(T_W, p_s)



#--------------------------------------------------------------------------------------------------------------------------------------
#Tabelle für Propan
#--------------------------------------------------------------------------------------------------------------------------------------

T_P = [-8.73, 1.73, 11.82, 31.89, 57.26, 66.83]
h_P_g= [565.09, 576.77, 587.59, 607.25, 626.02, 629.80]
h_P_f = [178.44, 204.33, 230.10, 284.09, 359.36, 390.79]

h_P_g_interpoation = scipy.interpolate.interp1d(T_P, h_P_g)
h_P_f_interpolation = scipy.interpolate.interp1d(T_P, h_P_f)

def r_P(T):
    r = h_P_g_interpoation(T)-h_P_f_interpolation(T)
    return(r)


#--------------------------------------------------------------------------------------------------------------------------------------
#Initialisierung der Variablen (EINGABEAUFFORDERUNG!!!)
#--------------------------------------------------------------------------------------------------------------------------------------



T_aussen = 42 #[°C]
T_wunsch = 12 #[°C]
phi_wunsch = 0.80 #[-]
N_Ing = 120 #[-]
T_Ing = 38 #[°C]
m_L_dot = 2.2 #[kg/s]
cp_L = 1.006 #[kJ/kg*K]
cp_D = 1.92 #[kJ/kg*K]
r_D = 2500 #[kJ/kg]
T_Propan = 10 #[°C]
m_dot_Propan = 0.76 #[kg/s]


#--------------------------------------------------------------------------------------------------------------------------------------
#Funktion für Wärmestrom Wände
#--------------------------------------------------------------------------------------------------------------------------------------

y_Beton = 1.35 #[W/K*m]
y_Putz = 0.25 #[W/K*m]
y_Daemmung = 0.035 #[W/K*m]
A_Wand = 400 #[m^2]
alpha_Wand = 5 #[W/Km^2]

R_Beton = 0.36/(y_Beton*A_Wand)
R_Putz = 0.04/(0.25*400)
R_Daemmung = 0.02/(0.035*400)
R_ges = R_Beton + R_Putz + R_Daemmung

k = ((alpha_Wand)**(-1) + R_ges*A_Wand)**(-1)

Q_dot_Wände = 4*A_Wand*k*(T_aussen - T_wunsch)*10**(-3) #(kW) 


"""Feuchte Luft"""
#--------------------------------------------------------------------------------------------------------------------------------------
#Funktionen für Partialdruck
#--------------------------------------------------------------------------------------------------------------------------------------

def p_d(T_undefined):
    pd = phi_wunsch * p_s_interpol(T_undefined)
    return(pd)


#--------------------------------------------------------------------------------------------------------------------------------------
#Funktionen für Partialdruck
#--------------------------------------------------------------------------------------------------------------------------------------

def x_d(T_undefined):
    pd = phi_wunsch * p_s_interpol(T_undefined)
    xd = 0.622*pd/(1-pd)
    return(xd)

"""Bilanzen und Funtionen für das Ingenieurbüro"""
#--------------------------------------------------------------------------------------------------------------------------------------
#Funktion Wärmestrom Ingenieure
#--------------------------------------------------------------------------------------------------------------------------------------

Q_dot_Ing = N_Ing * 2.7682*10**(-3) * 1.7 * (T_Ing - T_wunsch) #[kW]


#--------------------------------------------------------------------------------------------------------------------------------------
#Wärmebilanz Ingenieurbüro
#--------------------------------------------------------------------------------------------------------------------------------------

T_ende = sy.symbols('T_ende')

H_dot_in = m_L_dot*cp_L*T_wunsch + m_L_dot * x_d(T_wunsch)*(cp_D * T_wunsch+ r_D)
H_dot_out = m_L_dot*cp_L*T_ende + m_L_dot * x_d(T_wunsch) * (cp_D * T_ende + r_D)

eq1 = sy.Eq((-1)*H_dot_out + H_dot_in + Q_dot_Ing + Q_dot_Wände, 0)
sol_T_ende = sy.solve(eq1, T_ende)


#--------------------------------------------------------------------------------------------------------------------------------------
#Berechnung der neuen relativen Feuchte
#--------------------------------------------------------------------------------------------------------------------------------------



"""Wärmetauscher"""
#--------------------------------------------------------------------------------------------------------------------------------------
#Variante mit Propan
#--------------------------------------------------------------------------------------------------------------------------------------

#Ausgangstemperaturumdefinieren und Ausgangsenthalpiestrom aus Büro
T_Ende2 = sol_T_ende[0]
H_dot_out = m_L_dot*cp_L*T_Ende2 + m_L_dot * x_d(T_wunsch) * (cp_D * T_Ende2 + r_D)
H_dot_L_WÜ_in = H_dot_out 

#Wärmebilanz im WÜ

x = True

if x:
    x_d_WÜ = (-m_dot_Propan*r_P(T_wunsch) + m_L_dot*cp_L*(T_Ende2-T_wunsch) + m_L_dot*x_d(T_wunsch)*(cp_D*T_Ende2+r_D))/(cp_D*T_wunsch+r_D)

    p_d_WÜ = x_d_WÜ/(0.622+x_d_WÜ)
    phi_WÜ_nach = p_d_WÜ/p_d(T_wunsch)

    while x_d_WÜ < 0:
        print("Der Propanmassenstrom ist zu Groß, geben die einen neuen Wert ein")
        m_dot_Propan_neu = input()
        
      
 

      
        
 


#else:
    #p_d_WÜ = x_d_WÜ/(0.622+x_d_WÜ)
    #phi_WÜ_nach = p_d_WÜ/p_d(T_wunsch)
    #print("Die den Wärmeübertrager verlassende feuchte Luft hat eine relative Feuchte von \u03C6",phi_WÜ_nach*100,"%")



    

    









