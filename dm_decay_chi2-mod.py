# -*- coding: utf-8 -*-
"""
Constraints on the dark matter decay model.

TODO:
    1. Solve the problem of the large discrepancy in the orders

Created on Wed Jan 07 13:47:42 2015

@author: Hao Wang
@date: 2015-05-07
"""

"""Set parameter scope"""
import numpy as np
import math
from scipy.integrate import odeint
from scipy.integrate import quad
from scan_params import *
import sys

'''
Input format.
'''
if len(sys.argv) != 2 or sys.argv[1] == '-h':
    print("[*]Usage: python dm_decay_chi2.py obs")
    print("[*]obs is one of the following numbers:")
    print("[*]0 - ohd")
    print("[*]1 - ohd+H0")
    print("[*]2 - sne")
    print("[*]3 - sne+ohd")
    print("[*]4 - sne+ohd+H0")
    print("[*]5 - sne+ohd+H0+Om")
    print("[*]")
    raise SystemExit

num_obs = int(sys.argv[1])
obs=['ohd', 'ohd+H0', 'sne', 'sne+ohd', 'sne+ohd+H0', 'sne+ohd+H0+Om']  # USE DIcTIONARY!!,!,!,!,!,!

z_ini = 1000.
omega_drI = 1.  # At large z_ini, no decay happened yet. Choose small but nonzero value as we are using logarithms.
omega_b0 = 0.04
omega_r0 = 4.94e-5

"""OHD data"""
ohd_file = np.loadtxt('ohd.txt', usecols=range(0, 3))
ohd_file = ohd_file[ohd_file[:, 0].argsort()]
ohd_data = ohd_file[:, 1]
ohd_error = ohd_file[:, 2]
ohd_z = ohd_file[:, 0]
ohd_x_output = np.log(1./(ohd_z+1.))

"""SNIa data"""
sne_file = np.loadtxt('SCPUnion2.1_mu_vs_z.txt', usecols=range(1, 4), skiprows=5)
sne_cov = np.loadtxt('SCPUnion2.1_covmat_sys.txt')
sne_inv_cov = np.linalg.inv(sne_cov)

sne_file = sne_file[sne_file[:, 0].argsort()]. # You cannot use this data with the invcov matrix, as it is sorted
sne_data = sne_file[:, 1]
sne_error = sne_file[:, 2]
sne_z = sne_file[:, 0]

"""constants. Use higher precision."""
mpc = 3.1e22  # m
kmsmpc = 1000/mpc  # s^-1
Hn = 100*kmsmpc  # s^-1, used to normalize equations
yr = 3.1e7  # s
t0 = 1.4e10*yr  # s

"""
ODE of omega_dm & omega_dr evolution

n.b. The first element of x_output (or z) must correspond to the initial condition
of y_ini in the ode code -- it's imposed by odeint.

x    -> ln(a)
y[0] -> omega_dm
y[1] -> omega_dr

"""
def deriv(y, x, param):
   # w = 1./3
    tau = param[0]
    omega_lambda = param[1]
    omega_b0 = param[2]
    omega_r0 = param[3]
    omega_b = omega_b0*math.exp(-3*x)
    omega_r = omega_r0*math.exp(-4*x)
    if y[0]+y[1]+omega_lambda+omega_b+omega_r < 0:
        print y, x, tau
        print 'Total density is negative now. [Om, Or, Tau] = ', y[0], y[1], tau
        raise SystemExit

    E = math.sqrt(y[0]+y[1]+omega_lambda+omega_b+omega_r)
    du = -y[0]/(tau*E) - 3*y[0]
    dv = +y[0]/(tau*E) - 4*y[1]
    return [du, dv]

"""
ODE of ln(omega_dm) & ln(omega_dr) evolution
To solve the large order-of-magnitude difference accross the x-range.

x    -> ln(a)
y[0] -> ln(omega_dm)
y[1] -> ln(omega_dr)

"""
def deriv2(y, x , param):
    tau = param[0]
    omega_lambda = param[1]
    omega_b0 = param[2]
    omega_r0 = param[3]
    omega_b = omega_b0*math.exp(-3*x)
    omega_r = omega_r0*math.exp(-4*x)
    
    E = math.sqrt(math.exp(y[0])+math.exp(y[1])+omega_lambda+omega_b+omega_r)
    du = -1./(tau*E) - 3
    dv = math.exp(y[0]-y[1])/(tau*E) - 4
    return [du, dv]

"""Solve ODE to get hubble parameter at any x==ln(a); n.b. H0 factor included """
def get_hubble(omega_dmI, omega_lambdaI, tau, x):
    #print 'get_hubble argument x: ', x 
    x_tmp = np.array(x)
    # x_output's first element must correspond to the initial y[:] value, hence
    # construct a two-element array by adding initial x to our interested x.
    x_output = np.insert(x_tmp, 0, math.log(1./(1+z_ini)))
    #om_history = odeint(deriv, [omega_dmI, omega_drI], x_output, args=([tau,
    #    omega_lambda, omega_b0, omega_r0],))
    #omega_dmHistory = om_history[:, 0]
    #omega_drHistory = om_history[:, 1]
    om_history = odeint(deriv2, [math.log(omega_dmI), math.log(omega_drI)], 
            x_output, args=([tau, omega_lambdaI, omega_b0, omega_r0],))
    print om_history
    omega_lambda = omega_lambdaI*np.ones(len(x_output))
    omega_b = np.array([omega_b0*math.exp(-3*xi) for xi in x_output])  # Try np.exp?
    omega_r = np.array([omega_r0*math.exp(-4*xi) for xi in x_output])  # np.exp, rm math
    omega_dmHistory = np.array([math.exp(ln_odm) for ln_odm in om_history[:,
        0]])
    omega_drHistory = np.array([math.exp(ln_odr) for ln_odr in om_history[:,
        1]])
    return np.sqrt(omega_dmHistory+omega_drHistory+omega_b+omega_r+
            omega_lambda)[1:]*(Hn/kmsmpc)


"""Luminosity distance is the integration of 1/H over z"""
def integrand(z, omega_dmI, omega_lambdaI, tau):
    x = np.log(1.0/(1.0+z))
    return 1.0/get_hubble(omega_dmI, omega_lambdaI, tau, x)


"""Calculate D_L (in [Mpc]); used in the calculation of mu (for SNIa)"""
def get_dl(omega_dmI, omega_lambdaI, tau, z):
    c = 299792.46
    return (1.0+z)*c*quad(integrand, 0, z, args=(omega_dmI, omega_lambdaI, tau))[0]

"""
Construct D_L array w.r.t observed redshifts
TODO:
    1. Get 'real' LCDM luminosity distance, instead of an approximation.
    2. Add Omega_dmI as a constraint. (can not be too small)
"""
dl_theory = []
for z in sne_z:
    dl_theory.append(round(get_dl(0.2, 0.01, 1000, z), 2))


'''Omega_dm0 as an observable'''
def get_chi2_Omegadm0(omega_dmI, omega_lambdaI, tau):
    return 0.


'''Hubble constant as an observable'''
def get_chi2_hubble(omega_dmI, omega_lambdaI, tau):
    H0, H0_error = 73.8, 2.4  # [kmsmpc]
    x_H0 = 0.0  # x==ln(a(H0)=1)
    ohd_theory = get_hubble(omega_dmI, omega_lambdaI, tau, x_H0)  # Move x to the first place
    chi2_hubble = np.power(ohd_theory[0] - H0, 2)/np.power(H0_error, 2)


'''For each parameter set (initial value), get chi2'''   
def get_chi2_ohd(omega_dmI, omega_lambdaI, tau):
    ohd_theory = get_hubble(omega_dmI, omega_lambdaI, tau, ohd_x_output)
    chi2_ohd = np.sum(np.power(ohd_theory-ohd_data, 2)/np.power(ohd_error, 2))
    return chi2_ohd


"""With system error + covariance"""
def get_chi2_sne2(omega_dmI, omega_lambdaI, tau):
    mu = []
    for z in sne_z:
        tmp = 5*np.log10(get_dl(omega_dmI, omega_lambdaI, tau, z))+25.0
        mu.append(tmp)
    chi2_sne=np.dot(mu-sne_data, np.dot(mu-sne_data, sne_inv_cov))
    return chi2_sne


"""No covariance information"""
def get_chi2_sne(omega_dmI, omega_lambdaI, tau):
    chi2_sne=0
    for iz, z in enumerate(sne_z):
        dl = get_dl(omega_dmI, omega_lambdaI, tau, z)
        mu = 5*np.log10(dl)+25.0
        chi2_sne += np.power((mu-sne_data[iz]), 2)/np.power(sne_error[iz], 2)
    return chi2_sne


"""Currently we are not adding up two chi2's, but plot them separately."""
def get_chi2(omega_dmI, omega_lambdaI, tau):
    if num_obs == 0:
        return get_chi2_ohd(omega_dmI, omega_lambdaI, tau) 
    elif num_obs == 1:
        return get_chi2_sne2(omega_dmI, omega_lambdaI, tau)
    elif num_obs == 2:
        return get_chi2_sne2(omega_dmI, omega_lambdaI, tau) + \
                 get_chi2_ohd(omega_dmI, omega_lambdaI, tau)
    elif num_obs == 3:
        return get_chi2_sne2(omega_dmI, omega_lambdaI, tau) + \
                 get_chi2_ohd(omega_dmI, omega_lambdaI, tau) + \
                 get_chi2_hubble(omega_dmI, omega_lambdaI, tau)
    elif num_obs == 4:
        return get_chi2_sne2(omega_dmI, omega_lambdaI, tau) + \
                 get_chi2_ohd(omega_dmI, omega_lambdaI, tau) + \
                 get_chi2_hubble(omega_dmI, omega_lambdaI, tau) + \
                 get_chi2_Omegadm0(omega_dmI, omega_lambdaI, tau)
    else:
        print("No such observation probe available / Under construction.")
        raise SystemExit


'''Fill in the chi2 matrix'''
chi2 = np.zeros((n_omega_dm, n_omega_lambda, n_tau))
minchi2 = 100000
for iom, omega_dmI in enumerate(omega_dm_array):
    for iol, omega_lambdaI in enumerate(omega_lambda_array):
        for itau, logtau in enumerate(logtau_array):
            tau = np.exp(logtau)
            tmp = get_chi2(omega_dmI, omega_lambdaI, tau)
            print omega_dmI, omega_lambdaI, logtau, tmp
            if minchi2 > tmp:
                minchi2 = tmp
                peakOm, peakOl, peakTau = omega_dmI, omega_lambdaI, tau

            chi2[iom, iol, itau] = tmp  # So wrong.
       
fid="chi2file-"+num_obs+'-'+str(n_omega_dm)+'-'+str(n_omega_lambda)+'-'+str(n_tau)+'.bin'
chi2file = chi2.tofile(fid)
