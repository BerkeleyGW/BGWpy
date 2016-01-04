from .pwscfinput import PWscfInput


def get_scf_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts, wtks):
    """Construct a Quantum Espresso scf input."""
    inp = PWscfInput()
    
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


def get_bands_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts, wtks, nbnd=None):
    """Construct a Quantum Espresso bands input."""
    inp = get_scf_input(prefix, pseudo_dir, pseudos, structure, ecutwfc, kpts, wtks)
    inp.control['calculation'] = 'bands'
    if nbnd is not None:
        inp.system['nbnd'] = nbnd
    return inp



