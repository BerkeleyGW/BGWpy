import os
from os.path import join as pjoin
import subprocess

from ..core import Workflow
from ..BGW import get_kpt_grid, get_kpt_grid_nosym
from ..QE import get_scf_input, get_bands_input, get_wfn_pp_input, get_wfn_rho_pp_input
from ..Wannier90 import PW2WanInput, Sig2WanInput, Wannier90Input


class WannierInterpFlow(Workflow):

    def __init__(self, dirname, nproc, prefix, pseudo_dir, pseudos,
                 structure,
                 ecutwfc,
                 ngkpt,
                 kshift,
                 kbounds,
                 klabels,
                 nbnd_occ,
                 nbnd,
                 nspin,
                 eqp,
                 nwann,
                 sigma_log,
                 **kwargs):

        self.dirname = dirname
        self.prefix = prefix
        self.sigma_log = sigma_log
        self.mpirun_n = kwargs.pop('mpirun_n', 'aprun -n')
        self.nproc = nproc

        kpts_sh, wtks_sh = get_kpt_grid(structure, ngkpt, kshift=kshift)
        kpts_nosym, wtks_nosym = get_kpt_grid_nosym(ngkpt, 3*[.0])

        self.scf = get_scf_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts_sh, wtks_sh)
        self.wfn = get_bands_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, nbnd,
                                   kpts_nosym, wtks_nosym)

        self.pw2wan = PW2WanInput(prefix)

        self.sig2wan = Sig2WanInput(prefix, nbnd, nspin, eqp, 'sigma_hp.log')

        self.wannier = Wannier90Input(structure, nbnd, nwann, kbounds, klabels, mp_grid=ngkpt,
                                           kpts=kpts_nosym, projections=None)

        self.GWwannier = Wannier90Input(structure, nbnd, nwann, kbounds, klabels, mp_grid=ngkpt,
                                             kpts=kpts_nosym, projections=None)

    def get_run(self):

        links = ''
        sigma_log = self.sigma_log

        if os.path.relpath(os.path.dirname(self.sigma_log)) == os.path.relpath(self.dirname):
            links = ''
        else:
            rel_sigma_log = os.path.relpath(self.sigma_log, self.dirname)
            links = 'ln -nfs {} sigma_hp.log'.format(rel_sigma_log)

        return """
#!/usr/bin/env bash

# Executables
MPIRUN="{mpirun_n} {nproc}"
MPIRUNS="{mpirun_n} 1"
PW="pw.x"
WANNIER="wannier90.x"
PW2WAN="pw2wannier90.x"
SIG2WAN="sig2wan.x"

{links}
ln -nfs {prefix}.mmn  {prefix}_GW.mmn
ln -nfs {prefix}.amn  {prefix}_GW.amn
ln -nfs {prefix}.nnkp {prefix}_GW.nnkp


echo `date`
echo '1) Computing ground state density'
$MPIRUN $PW -in ./scf.in &> ./scf.out

echo `date`
echo '2) Computing  wavefunctions'
$MPIRUN $PW -in ./wfn.in &> ./wfn.out

echo `date`
echo '3) Preprocessing wannier90'
$MPIRUNS $WANNIER -pp {prefix}

echo `date`
echo '4) Running pw2wan'
$MPIRUN $PW2WAN -in ./pw2wan.in &> pw2wan.out

echo `date`
echo '5) Running wannier90'
$MPIRUNS $WANNIER {prefix}

echo `date`
echo '6) Running sig2wan'
$MPIRUNS $SIG2WAN &> sig2wan.out

echo `date`
echo '7) Running wannier90'
$MPIRUNS $WANNIER {prefix}_GW

echo 'All done'
echo `date`

""".format(prefix=self.prefix, links=links, nproc=self.nproc, mpirun_n=self.mpirun_n)


    def write(self):

        # Create main directory
        subprocess.call(['mkdir', '-p', self.dirname])

        # Make run file
        with open(pjoin(self.dirname, 'run.sh'), 'write') as f:
            f.write(self.get_run())

        self.scf.write(pjoin(self.dirname, 'scf.in'))
        self.wfn.write(pjoin(self.dirname, 'wfn.in'))
        self.pw2wan.write(pjoin(self.dirname, 'pw2wan.in'))
        self.sig2wan.write(pjoin(self.dirname, 'sig2wan.inp'))
        self.wannier.write(pjoin(self.dirname, '{}.win'.format(self.prefix)))
        self.GWwannier.write(pjoin(self.dirname, '{}_GW.win'.format(self.prefix)))



