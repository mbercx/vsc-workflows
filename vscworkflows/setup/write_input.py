# coding: utf8
# Copyright (c) Marnik Bercx, University of Antwerp
# Distributed under the terms of the MIT License

import os

from monty.serialization import loadfn

from pymatgen import Structure
from quotas import QSlab

from vscworkflows.setup.sets import BulkRelaxSet, SlabRelaxSet

"""
Setup scripts for the various calculations.

"""

__author__ = "Marnik Bercx"
__copyright__ = "Copyright 2018, Marnik Bercx, University of Antwerp"
__version__ = "pre-alpha"
__maintainer__ = "Marnik Bercx"
__email__ = "marnik.bercx@uantwerpen.be"
__date__ = "Jun 2019"

MODULE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          "../../set_configs")

DFT_FUNCTIONAL = "PBE_54"


def _load_yaml_config(filename):
    config = loadfn(os.path.join(MODULE_DIR, "%s.yaml" % filename))
    return config


def _load_functional(functional):
    # Set up the functional
    if functional[0] != "pbe":
        functional_config = _load_yaml_config(functional[0] + "Set")
        functional_config["INCAR"].update(functional[1])
        return functional_config["INCAR"]
    else:
        return {}


def _set_up_directory(directory, functional, calculation):
    # Set up the calculation directory
    if directory == "":
        directory = os.path.join(os.getcwd(), functional[0])
        if functional[0] == "pbeu":
            directory += "_" + "".join(k + str(functional[1]["LDAUU"][k]) for k
                                       in functional[1]["LDAUU"].keys())
        directory += "_" + calculation
    else:
        directory = os.path.abspath(directory)

    return directory

# TODO: Check this method
def optimize(structure, directory="", functional=("pbe", {}),
             is_metal=False):
    """
    Set up a standard geometry optimization calculation for a structure. Optimizes
    both the atomic positions as well as the unit cell (ISIF=3).

    Args:
        structure: pymatgen.Structure OR path to structure file for which to set up the
            geometry optimization calculation.
        directory (str): Path to the directory in which to set up the
            geometry optimization.
        functional (tuple): Tuple with the functional choices. The first element
            contains a string that indicates the functional used ("pbe", "hse", ...),
            whereas the second element contains a dictionary that allows the user
            to specify the various functional tags. E.g. ("hse", {"LAEXX": 0.2}).
        is_metal (bool): Flag that indicates the material being studied is a
            metal, which changes the smearing from Gaussian to second order
            Methfessel-Paxton of 0.2 eV.

    Returns:
        str: Path to the directory in which the calculation is set up.

    """
    # Set up the calculation directory
    directory = _set_up_directory(directory, functional, "optimize")
    try:
        os.makedirs(directory)
    except FileExistsError:
        pass

    # In case the structure is given as a string, load it from the specified path
    if isinstance(structure, str):
        structure = Structure.from_file(structure)

    structure.to("json", os.path.join(directory, "initial_cathode.json"))

    # Set up the calculation
    user_incar_settings = {}

    # Set up the functional
    user_incar_settings.update(_load_functional(functional))

    # Check if a magnetic moment was provided for the sites. If so, perform a
    # spin-polarized calculation
    if "magmom" in structure.site_properties.keys():
        user_incar_settings.update({"ISPIN": 2, "MAGMOM": True})

    # For metals, use Methfessel Paxton smearing
    if is_metal:
        user_incar_settings.update({"ISMEAR": 2, "SIGMA": 0.2})

    # Set up the geometry optimization
    geo_optimization = BulkRelaxSet(structure=structure,
                                    user_incar_settings=user_incar_settings,
                                    potcar_functional=DFT_FUNCTIONAL)

    # Write the setup files to the geometry optimization directory
    geo_optimization.write_input(directory)

    return directory


def slab_optimize(slab, fix_part, fix_thickness, directory="",
                  functional=("pbe", {}), is_metal=False):
    """
    Set up a geometric optimization for a two dimensional slab.

    Args:
        slab (QSlab): Quotas version of a Slab object, or path to the json file that
            contains the details of the QSlab.
        directory (str): Path to the directory in which to set up the
            geometry optimization.
        functional (tuple): Tuple with the functional choices. The first element
            contains a string that indicates the functional used ("pbe", "hse", ...),
            whereas the second element contains a dictionary that allows the user
            to specify the various functional tags. E.g. ("hse", {"LAEXX": 0.2}).
        fix_part:
        fix_thickness:
        is_metal (bool): Flag that indicates the material being studied is a
            metal, which changes the smearing from Gaussian to second order
            Methfessel-Paxton of 0.2 eV.

    Returns:
        relax_dir: Full path to the directory where the geometry
        optimization was set up.
    """
    # Set up the calculation directory
    directory = _set_up_directory(directory, functional, "optimize")
    try:
        os.makedirs(directory)
    except FileExistsError:
        pass

    # In case the slab is given as a string, load it from the specified path
    if isinstance(slab, str):
        slab = QSlab.from_file(slab)

    user_incar_settings = {}

    # Set up the functional
    user_incar_settings.update(_load_functional(functional))

    # Check if a magnetic moment was provided for the sites. If so, perform a
    # spin-polarized calculation
    if "magmom" in slab.site_properties.keys():
        user_incar_settings.update({"ISPIN": 2, "MAGMOM": True})

        slab.add_site_property("magmom", [0] * len(slab.sites))

    # For metals, use Methfessel Paxton smearing
    if is_metal:
        user_incar_settings.update({"ISMEAR": 2, "SIGMA": 0.2})

    calculation = SlabRelaxSet(structure=slab,
                               user_incar_settings=user_incar_settings,
                               potcar_functional=DFT_FUNCTIONAL)

    calculation.fix_slab_bulk(thickness=fix_thickness,
                              part=fix_part)

    # Write the setup files to the calculation directory
    calculation.write_input(directory)

    return directory