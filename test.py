import numpy as np
import scipy as scp
import sympy as sym
import matplotlib.pyplot as plt
import scipy.integrate as integrate

#Präambel der mit dem zu Wählenden Paket zu erwähnenden Funktionen
pi = np.pi
sqrt = np.sqrt
cos = np.cos
sin = np.sin


#DGL






def DGL(omega_1, t, phi_1):
    g=9.81
    l1=1
    domega_1_d = -(g/l1)*sin(phi_1)
    return [domgea_1_d]

t = np.linspace(0, 10, 2000)
phi_1_init = 0

z = integrate.odeint(DGL, S_init, t, args=(g, l1))


print(z)
