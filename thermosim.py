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
        
    def change_values(self, ta, tw, nIng, phi):
        self.tAussen = ta
        self.tWunsch = tw
        self.nIng = nIng
        self.phi = phi
        
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

