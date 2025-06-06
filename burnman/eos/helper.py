# This file is part of BurnMan - a thermoelastic and thermodynamic toolkit for the Earth and Planetary Sciences
# Copyright (C) 2012 - 2017 by the BurnMan team, released under the GNU
# GPL v2 or later.

from __future__ import absolute_import

import inspect
from . import slb
from . import mie_grueneisen_debye as mgd
from . import murnaghan
from . import birch_murnaghan as bm
from . import birch_murnaghan_4th as bm4
from . import modified_tait as mt
from . import macaw
from . import spock
from . import dks_liquid
from . import dks_solid
from . import hp
from . import cork
from . import vinet
from . import morse_potential
from . import reciprocal_kprime
from . import aa
from . import brosh_calphad
from .equation_of_state import EquationOfState


class CombinedMineralMethod(object):
    """Dummy class because CombinedMineral objects are derived
    from a mechanical Solution.
    Solution needs a method to call Mineral.set_state(),
    but a CombinedMineral should never have a method that
    is used for solutions."""

    def validate_parameters(self, params):
        pass

    pass


def create(method):
    """
    Creates an instance of an EquationOfState from a string,
    a class EquationOfState, or an instance of EquationOfState.
    """
    if isinstance(method, str):
        if method == "slb2":
            return slb.SLB2()
        elif method == "vinet":
            return vinet.Vinet()
        elif method == "morse":
            return morse_potential.Morse()
        elif method == "rkprime":
            return reciprocal_kprime.RKprime()
        elif method == "aa":
            return aa.AA()
        elif method == "mgd2":
            return mgd.MGD2()
        elif method == "mgd3":
            return mgd.MGD3()
        elif method == "slb3":
            return slb.SLB3()
        elif method == "slb3-conductive":
            return slb.SLB3Conductive()
        elif method == "murnaghan":
            return murnaghan.Murnaghan()
        elif method == "bm2":
            return bm.BM2()
        elif method == "bm3":
            return bm.BM3()
        elif method == "bm4":
            return bm4.BM4()
        elif method == "mt":
            return mt.MT()
        elif method == "macaw":
            return macaw.MACAW()
        elif method == "spock":
            return spock.SPOCK()
        elif method == "hp98":
            return hp.HP98()
        elif method == "hp_tmt":
            return hp.HP_TMT()
        elif method == "hp_tmtL":
            return hp.HP_TMTL()
        elif method == "cork":
            return cork.CORK()
        elif method == "dks_l":
            return dks_liquid.DKS_L()
        elif method == "dks_s":
            return dks_solid.DKS_S()
        elif method == "brosh_calphad":
            return brosh_calphad.BroshCalphad()
        elif method == "combined":
            return CombinedMineralMethod()
        else:
            raise Exception("unsupported material method " + method)
    elif isinstance(method, EquationOfState):
        return method
    elif inspect.isclass(method) and issubclass(method, EquationOfState):
        return method()
    else:
        raise Exception("unsupported material method " + method.__class__.__name__)
