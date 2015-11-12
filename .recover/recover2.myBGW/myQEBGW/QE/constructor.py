
from . import QuantumEspressoInput, 


def get_scf_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts, wtks):
    """Construct a Quantum Espresso scf input."""
    inp = QuantumEspressoInput()
    
    inp.control.update(
        prefix = prefix,
        pseudo_dir = pseudo_dir,
        calculation = 'scf',
        )
    
    inp.electrons.update(
        electron_maxstep = 100,
        conv_thr = 1.0e-10,
        mixing_mode = 'plain',
        mixing_beta = 0.7,
        mixing_ndim = 8,
        diagonalization = 'david',
        diago_david_ndim = 4,
        diago_full_acc = True,
        )
    
    inp.system['ecutwfc'] = ecutwfc,
    inp.set_kpoints_crystal(kpts, wtks)
    inp.structure = structure
    inp.pseudos = pseudos

    return inp


def get_bands_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, nbnd, kpts, wtks):
    """Construct a Quantum Espresso bands input."""
    inp = get_scf_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts, wtks)
    inp['calculation'] = 'bands'
    return inp


def get_wfn_pp_input(prefix, wfn_fname, ngkpt, kshift=3*[.0], qshift=3*[.0]):
    """Construct a PW2BGW wfn input."""
    inp = PW2BGWInput(
        prefix = prefix,
        real_or_complex = 2,
        wfng_file = wfn_fname,
        wfng_flag = True,
        wfng_kgrid = True,
        )

    inp.ngkpt = ngkpt
    inp.kshift = kshift
    inp.qshift = qshift

    return inp

def get_wfn_rho_pp_input(prefix, wfn_fname, rho_fname, ngkpt, kshift, nband)

    inp = get_wfn_pp_input(prefix, wfn_fname, ngkpt, kshift)
    inp.update(
        rhog_flag = True,
        rhog_file = rho_fname,
        vxcg_flag = False,
        vxcg_file = 'vxc.real',
        vxc_flag = True,
        vxc_file = 'vxc.dat',
        vxc_diag_nmin = 1,
        vxc_diag_nmax = nband,
        vxc_offdiag_nmin = 0,
        vxc_offdiag_nmax = 0,
        )

    return inp

