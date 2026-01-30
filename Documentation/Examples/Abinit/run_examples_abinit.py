#!/usr/bin/env python
"""
Run all Abinit examples with centralized parameters.

This script runs the complete BGW calculation pipeline for Abinit,
including density calculation, wavefunction generation, epsilon calculation,
sigma calculation, kernel calculation, and absorption spectrum calculation.
It also includes complete workflow examples (GW and BSE flows).
"""

# Import modules dynamically due to hyphens in filenames
import importlib

# Import modules
t11 = importlib.import_module("t11-Density")
t12 = importlib.import_module("t12-Wfn")
t13 = importlib.import_module("t13-Wfnq")
t14 = importlib.import_module("t14-Wfn_co")
t15 = importlib.import_module("t15-Wfn_fi")
t16 = importlib.import_module("t16-Wfnq_fi")
t21 = importlib.import_module("t21-Epsilon")
t22 = importlib.import_module("t22-Sigma")
t23 = importlib.import_module("t23-Kernel")
t24 = importlib.import_module("t24-Absorption")
t32 = importlib.import_module("t32-GW")
t33 = importlib.import_module("t33-BSE")


def main():
    """Run all Abinit examples with centralized parameters."""

    # ==============================================================================
    # Global Parameters - Modify these to customize the calculation
    # ==============================================================================

    # Common parameters dictionary
    params = {
        # k-points grid
        "ngkpt": [2, 2, 2],
        # Energy cutoffs (Ha for Abinit)
        "ecut": 5.0,  # Wavefunction cutoff energy
        "ecuteps": 5.0,  # Epsilon matrix cutoff energy
        # MPI parameters - change as needed
        "nproc": 4,
        "nproc_per_node": 4,
        "mpirun": "mpirun",
        "nproc_flag": "-n",
        "nproc_per_node_flag": "--npernode",
    }

    # ==============================================================================
    # Run Examples
    # ==============================================================================

    print("=" * 80)
    print("Starting Abinit BGW Examples")
    print("=" * 80)

    # Step 1: Density calculation
    print("\n[1/12] Running Density calculation (t11)...")
    t11.run_t11_density(**params)

    # Step 2: Wfn calculation
    print("\n[2/12] Running Wfn calculation (t12)...")
    t12.run_t12_wfn(**params)

    # Step 3: Wfnq calculation
    print("\n[3/12] Running Wfnq calculation (t13)...")
    t13.run_t13_wfnq(**params)

    # Step 4: Wfn_co calculation
    print("\n[4/12] Running Wfn_co calculation (t14)...")
    t14.run_t14_wfn_co(**params)

    # Step 5: Wfn_fi calculation
    print("\n[5/12] Running Wfn_fi calculation (t15)...")
    t15.run_t15_wfn_fi(**params)

    # Step 6: Wfnq_fi calculation
    print("\n[6/12] Running Wfnq_fi calculation (t16)...")
    t16.run_t16_wfnq_fi(**params)

    # Step 7: Epsilon calculation
    print("\n[7/12] Running Epsilon calculation (t21)...")
    t21.run_t21_epsilon(**params)

    # Step 8: Sigma calculation
    print("\n[8/12] Running Sigma calculation (t22)...")
    t22.run_t22_sigma(**params)

    # Step 9: Kernel calculation
    print("\n[9/12] Running Kernel calculation (t23)...")
    t23.run_t23_kernel(**params)

    # Step 10: Absorption calculation
    print("\n[10/12] Running Absorption calculation (t24)...")
    t24.run_t24_absorption(**params)

    # Step 11: Complete GW workflow
    print("\n[11/12] Running complete GW workflow (t32)...")
    t32.run_t32_gw(**params)

    # Step 12: Complete BSE workflow
    print("\n[12/12] Running complete BSE workflow (t33)...")
    t33.run_t33_bse(**params)

    print("\n" + "=" * 80)
    print("Abinit examples completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
