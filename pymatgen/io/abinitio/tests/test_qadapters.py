# coding: utf-8
from __future__ import unicode_literals, division, print_function

from collections import OrderedDict
from pymatgen.util.testing import PymatgenTest
from pymatgen.io.abinitio.qadapters import *

class QadapterTest(PymatgenTest):

    def test_base(self):
        """
        Simple unit tests for Qadapter subclasses.
        A more complete coverage would require integration testing.
        """
        sub_classes = AbstractQueueAdapter.__subclasses__()

        modules = ["intel/compilerpro/13.0.1.117",
                   "fftw3/intel/3.3",
        ]

        shell_env = OrderedDict(
             [("PATH", "/user/abinit-7.4.3-public/tmp_intel13/src/98_main/:/user/bin:$PATH"),
              ("LD_LIBRARY_PATH", "/NAPS/intel13/lib:$LD_LIBRARY_PATH")])

        mpi_runner = MpiRunner("mpirun")

        # Test if we can instantiate the concrete classes with the abc protocol.
        for subc in sub_classes:

            # Make sure we have registered the class in qadapeter_class
            cls = qadapter_class(subc.QTYPE)
            self.assertTrue(cls == subc)

            # Create the adapter
            qad = cls(qparams=None, setup=None, modules=modules, shell_env=shell_env, omp_env=None, 
                      pre_run=None, post_run=None, mpi_runner=mpi_runner)

            # Test the programmatic interface used to change job parameters.
            self.assertFalse(qad.has_omp)
            self.assertTrue(qad.has_mpirun)
            qad.set_mpi_ncpus(2)
            self.assertTrue(qad.mpi_ncpus == 2)

            # Test the creation of the script
            script = qad.get_script_str("job.sh", "/launch/dir", "executable", "qout_path", "qerr_path", 
                                        stdin="STDIN", stdout="STDOUT", stderr="STDERR")

            # Test whether qad can be serialized with Pickle.
            deserialized_qads = self.serialize_with_pickle(qad, test_eq=False)

            for new_qad in deserialized_qads:
                new_script = new_qad.get_script_str("job.sh", "/launch/dir", "executable", "qout_path", "qerr_path", 
                                                    stdin="STDIN", stdout="STDOUT", stderr="STDERR")

                self.assertEqual(new_script, script)

    #def test_openmp(self)
    #    omp_env = {"OMP_NUM_THREADS": 2}
    #    for subc in AbstractQueueAdapter.__subclasses__()
    #        cls = qadapter_class(subc.QTYPE)
    #        # Create the adapter
    #        #qad = cls(qparams=None, setup=None, modules=modules, shell_env=shell_env, omp_env=omp_env, 
    #        #          pre_run=None, post_run=None, mpi_runner=mpi_runner)
    #        self.assertTrue(qad.has_omp)


class PbsProadapterTest(PymatgenTest):
    """Test suite for PbsPro adapter."""
    def test_params_from_partition(self):
        aequal = self.assertEqual
        p = Partition("test_partition", num_nodes=100, sockets_per_node=2, cores_per_socket=4)
        print("partition\n" + str(p))

        qad = PbsProAdapter()
        print(qad)

        qad.set_mpi_ncpus(4)
        params = qad.params_from_partition(p)
        print(params)
        # IN_CORE PURE MPI: MPI: 4, OMP: 1
        aequal(params, {'ompthreads': 1, 'ncpus': 1, 'select': 4, 'mpiprocs': 1})

        qad.set_omp_ncpus(2)
        params = qad.params_from_partition(p)
        print(params)
        # HYBRID MPI-OPENMP run, perfectly divisible among nodes:  MPI: 4, OMP: 2
        aequal(params, {'ompthreads': 2, 'ncpus': 8, 'select': 1, 'mpiprocs': 4})

        qad.set_mpi_ncpus(12)
        params = qad.params_from_partition(p)
        print(params)
        # HYBRID MPI-OPENMP run, perfectly divisible among nodes:  MPI: 12, OMP: 2
        aequal(params, {'ompthreads': 2, 'ncpus': 8, 'select': 3, 'mpiprocs': 4})

        qad.set_omp_ncpus(5)
        qad.set_mpi_ncpus(3)
        params = qad.params_from_partition(p)
        print(params)
        # HYBRID MPI-OPENMP, NOT commensurate with nodes:  MPI: 3, OMP: 5
        aequal(params, {'ompthreads': 5, 'ncpus': 5, 'select': 3, 'mpiprocs': 1})



import unittest
from pymatgen.io.abinitio.qadapters import Command
class CommandTest(unittest.TestCase):
    def test_command(self):
        """Test Command class"""
        command = Command("sleep 0.5")

        command.run(timeout=1)
        print(command)
        self.assertEqual(command.status, 0)
        self.assertFalse(command.killed)

        command.run(timeout=0.2)
        self.assertNotEqual(command.status, 0)
        self.assertTrue(command.killed)


if __name__ == '__main__':
    import unittest
    unittest.main()
