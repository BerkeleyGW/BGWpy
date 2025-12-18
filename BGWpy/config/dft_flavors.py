from __future__ import annotations


def is_dft_flavor_abinit(dft_flavor):
    flavor = str(dft_flavor).lower().strip()
    aliases = ("abinit", "abi")
    return flavor in aliases


def is_dft_flavor_espresso(dft_flavor):
    flavor = str(dft_flavor).lower().strip()
    aliases = ("espresso", "qe", "quantumespresso", "quantum espresso", "pwpwscf")
    return flavor in aliases


def check_dft_flavor(dft_flavor):
    """Check that dft_flavor is a valid value."""
    allowed_values = ("abinit", "espresso")
    if is_dft_flavor_abinit(dft_flavor) or is_dft_flavor_espresso(dft_flavor):
        return dft_flavor
    msg = f"Allowed values for dft_flavor are :{allowed_values}\n. Got '{dft_flavor}'."
    raise ValueError(msg)
