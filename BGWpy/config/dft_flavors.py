
def is_dft_flavor_abinit(dft_flavor):
    flavor = str(dft_flavor).lower().strip()
    aliases = ('abinit', 'abi')
    if flavor in aliases:
        return True
    return False

def is_dft_flavor_espresso(dft_flavor):
    flavor = str(dft_flavor).lower().strip()
    aliases = ('espresso', 'qe', 'quantumespresso', 'quantum espresso',
               'pw' 'pwscf')
    if flavor in aliases:
        return True
    return False

def check_dft_flavor(dft_flavor):
    """Check that dft_flavor is a valid value."""
    allowed_values = ('abinit', 'espresso')
    if is_dft_flavor_abinit(dft_flavor):
        return dft_flavor
    elif is_dft_flavor_espresso(dft_flavor):
        return dft_flavor
    else:
        raise ValueError("Allowed values for dft_flavor are :{}\n. Got '{}'."
                         .format(allowed_values, dft_flavor))
