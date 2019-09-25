import os

from . import TestTask

from .. import data
from .. import Structure
from ..Abinit import AbinitScfTask, AbinitWfnTask, Abi2BgwTask, AbinitBgwFlow

# Note: The tests are redundant. The issue being that
# tests cannot be interdependent.

class TestAbinitTaskMaker(TestTask):

    _structure_fname = data.structure_Si
    
    # Common arguments for tasks.
    common = dict(
        structure = Structure.from_file(_structure_fname),
        prefix = 'Si',
        pseudo_dir = data.pseudo_dir,
        pseudos = data.pseudos_Si,
        ngkpt = [2,2,2],
        kshift = [.5,.5,.5],
        ecut = 10.0,
        nband = 9,
        ecuteps = 10.0,
        with_density=True,
        )

    def get_wfnbgwflow(self, scftask, **kwargs):
        """Construct a AbinitBgwFlow."""
        kwargs.setdefault('dirname', os.path.join(self.tmpdir, 'DFT'))
        kwargs.update(charge_density_fname = scftask.charge_density_fname)
        for key, val in self.common.items():
            kwargs.setdefault(key, val)

        return AbinitBgwFlow(**kwargs)


    def get_scftask(self, **kwargs):
        """Construct a ScfTask."""
        kwargs.setdefault('dirname', os.path.join(self.tmpdir, 'SCF'))
        for key, val in self.common.items():
            kwargs.setdefault(key, val)

        return AbinitScfTask(**kwargs)
        
    def get_wfntask(self, scftask, **kwargs):
        """Construct a WfnTask."""
        kwargs.setdefault('dirname', os.path.join(self.tmpdir, 'Wfn'))
        kwargs.update(charge_density_fname = scftask.charge_density_fname)
        for key, val in self.common.items():
            kwargs.setdefault(key, val)

        return AbinitWfnTask(**kwargs)
        
    def get_wfn2bgwtask(self, scftask, wfntask, **kwargs):
        """Construct a Abi2BgwTask."""
        kwargs.update(dirname = wfntask.dirname,
            wfng_flag = True,
            rhog_flag = True,
            vxcg_flag = True,
            wfn_fname = wfntask.wfn_fname,
            rho_fname = scftask.rho_fname,
            vxc_fname = scftask.vxc_fname)

        for key, val in self.common.items():
            kwargs.setdefault(key, val)

        return Abi2BgwTask(**kwargs)


class TestAbinitTasks(TestAbinitTaskMaker):

    def test_scftask(self):
        """Test density calculation."""
        task = self.get_scftask()
        task.write()
        task.run()
        task.report()
        self.assertCompleted(task)

    def test_wfntask(self):
        """Test density and wavefunction calculation."""
        scftask = self.get_scftask()
        wfntask = self.get_wfntask(scftask)

        for task in (scftask, wfntask):
            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

    def test_abi2bgwtask(self):
        """Test density and wavefunction calculation."""
        scftask = self.get_scftask()
        wfntask = self.get_wfntask(scftask)
        wfn2bgwtask = self.get_wfn2bgwtask(scftask, wfntask)

        for task in (scftask, wfntask, wfn2bgwtask):
            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

    def test_wfnbgwflow(self):
        """Test density calculation."""
        scftask = self.get_scftask()
        wfnbgwflow = self.get_wfnbgwflow(scftask)
        for task in (scftask, wfnbgwflow):
            task.write()
            task.run()
            task.report()
            self.assertCompleted(task)

