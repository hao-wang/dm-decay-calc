from matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from io_params import *
import sys

'''
The only argument is choosing OHD('ohd') or SNe('sne')
'''
if len(sys.argv) != 2 or sys.argv[1] == '-h':
    print("[*]Usage: python dm_decay_chi2.py obs")
    print("[*]obs is one of the following numbers:")
    print(obs)
    raise SystemExit

num_obs = int(sys.argv[1])
print('Using', obs[num_obs], 'as observable.')

big = 16

fid = "chi2file-"+obs[num_obs]+'-'+str(n_omega_dm)+'-'+str(n_omega_lambda)+\
        '-'+str(n_tau)+'.bin'
#fid = "chi2file-"+str(n_omega_dm)+'-'+str(n_omega_lambda)+'-'+str(n_tau)+'-sum.bin'

chi = np.fromfile(fid)
chi2 = chi.reshape(n_omega_dm, n_omega_lambda, n_tau)
minchi2 = np.amin(chi2)
dchi2 = chi2-minchi2

'''Integrate over the third (tau) dimension'''
chi2_omol = -2*np.log(np.sum(np.exp(-dchi2/2.), axis=2))
minchi2_omol = np.min(chi2_omol)
[peak_om_index, peak_ol_index] = np.unravel_index(np.argmin(chi2_omol), 
        np.shape(chi2_omol))
peak_om = omega_dm_array[peak_om_index]
peak_ol = omega_lambda_array[peak_ol_index]
dchi2_omol = chi2_omol-minchi2_omol
fig = Figure()
canvas = FigureCanvas(fig)
ax  = fig.add_subplot(121)
contourOmOl = ax.contour(omega_lambda_array, omega_dm_array, 
        dchi2_omol, levels=[2.3, 5.0], colors=('r', 'b'))
ax.plot(peak_ol, peak_om, 'r*')
ax.set_xlabel(r'$\Omega_\Lambda$', fontsize=big)
ax.set_ylabel(r'$\Omega_{dm}$', fontsize=big)

'''Integrate over the second (omega_lambda) dimension'''
chi2_omtau = -2*np.log(np.sum(np.exp(-dchi2/2.), axis=1))
minchi2_omtau = np.min(chi2_omtau)
[peak_om_index, peak_tau_index] = np.unravel_index(np.argmin(chi2_omtau), 
        np.shape(chi2_omtau))
peak_om = omega_dm_array[peak_om_index]
peak_tau = tau_array[peak_tau_index]
dchi2_omtau = chi2_omtau-minchi2_omtau
bx = fig.add_subplot(122)
contourOmTau = bx.contour(tau_array, omega_dm_array, dchi2_omtau, 
        levels=[2.3, 5.0], colors=('r', 'b'))
bx.plot(peak_tau, peak_om, 'r*')
bx.set_xlabel(r'$\tau$', fontsize=big)
#bx.set_ylabel(r'$\Omega_m$', fontsize=big)
bx.set_xscale("log")
canvas.print_figure('ol-om+tau-om-'+obs[num_obs]+'.eps')
