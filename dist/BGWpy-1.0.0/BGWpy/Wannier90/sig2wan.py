
from ..core import Writable

__all__ = ['Sig2WanInput']

class Sig2WanInput(Writable):

    def __init__(self, prefix, nbnd, nspin=1, eqp=1, sigma_file='sigma_hp.log', prefix_gw=None):

        self.prefix = prefix
        self.prefix_gw = prefix_gw if prefix_gw else prefix + '_GW'
        self.nspin = nspin
        self.nbnd = nbnd
        self.eqp = eqp
        self.sigma_file = sigma_file

    def __str__(self):
        return """
{sigma:<30} ! Sigma output file to read k-points, eigenvalues and symmetries from
{nspin:<30} ! spin component to read from sigma_hp.log file
{eqp:<30} ! set to 0 or 1 to read eqp0 or eqp1 from sigma_hp.log file
{nnkp:<30} ! Wannier90 input file to read k-points from
{eig:<30} ! file where the output of sig2wan is written
{nbnd:<30} ! number of bands to write out
""".format(sigma=self.sigma_file, nnkp=self.prefix+'.nnkp', eig=self.prefix_gw+'.eig',
           nspin=self.nspin, eqp=self.eqp, nbnd=self.nbnd).lstrip()



