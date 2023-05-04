# This code is part of OpenFE and is licensed under the MIT license.
# For details, see https://github.com/OpenFreeEnergy/openfe
"""
Reusable utility methods to validate input systems to OpenMM-based alchemical
Protocols.
"""
from typing import Dict, List, Optional, Tuple
from openff.toolkit import Molecule as OFFMol
from gufe import (
    Component, ChemicalSystem, SolventComponent, ProteinComponent,
    SmallMoleculeComponent
)


def get_alchemical_components(
        stateA: ChemicalSystem,
        stateB: ChemicalSystem,
) -> Dict[str, List[Component]]:
    """
    Checks the equality between Components of two end state ChemicalSystems
    and identify which components do not match.

    Parameters
    ----------
    stateA : ChemicalSystem
      The chemical system of end state A.
    stateB : ChemicalSystem
      The chemical system of end state B.

    Returns
    -------
    alchemical_components : Dict[str, List[Component]]
      Dictionary containing a list of alchemical components for each state.

    Raises
    ------
    ValueError
      If there are any duplicate components in states A or B.
    """
    matched_components = {}
    alchemical_components: Dict[str, List[Component]] = {
        'stateA': [], 'stateB': [],
    }

    for keyA, valA in stateA.components.items():
        for keyB, valB in stateB.components.items():
            if valA.to_dict() == valB.to_dict():
                if valA not in matched_components.keys():
                    matched_components[valA] = valB
                else:
                    # Could be that either we have a duplicate component
                    # in stateA or in stateB
                    errmsg = (f"state A components {keyA}: {valA} matches "
                              "multiple components in stateA or stateB")
                    raise ValueError(errmsg)

    # populate stateA alchemical components
    for valA in stateA.components.values():
        if valA not in matched_components.keys():
            alchemical_components['stateA'].append(valA)

    # populate stateB alchemical components
    for valB in stateB.components.values():
        if valB not in matched_components.values():
            alchemical_components['stateB'].append(valB)

    return alchemical_components


def validate_solvent(state: ChemicalSystem, nonbonded_method: str):
    """
    Checks that the ChemicalSystem component has the right solvent
    composition for an input nonbonded_methtod.

    Parameters
    ----------
    state : ChemicalSystem
      The chemical system to inspect.
    nonbonded_method : str
      The nonbonded method to be applied for the simulation.

    Raises
    ------
    ValueError
      * If there are multiple SolventComponents in the ChemicalSystem.
      * If there is a SolventComponent and the `nonbonded_method` is
        `nocutoff`.
      * If the SolventComponent solvent is not water.
    """
    solv = [comp for comp in state.values()
            if isinstance(comp, SolventComponent)]

    if len(solv) > 0 and nonbonded_method.lower() == "nocutoff":
        errmsg = "nocutoff cannot be used for solvent transformations"
        raise ValueError(errmsg)

    if len(solv) == 0 and nonbonded_method.lower() == 'pme':
        errmsg = "PME cannot be used for vacuum transform"
        raise ValueError(errmsg)

    if len(solv) > 1:
        errmsg = "Multiple SolventComponent found, only one is supported"
        raise ValueError(errmsg)

    if len(solv) > 0 and solv[0].smiles != 'O':
        errmsg = "Non water solvent is not currently supported"
        raise ValueError(errmsg)


def validate_protein(state: ChemicalSystem):
    """
    Checks that the ChemicalSystem's ProteinComponent are suitable for the
    alchemical protocol.

    Parameters
    ----------
    state : ChemicalSystem
      The chemical system to inspect.

    Raises
    ------
    ValueError
      If there are multiple ProteinComponent in the ChemicalSystem.
    """
    nprot = sum(1 for comp in state.values()
                if isinstance(comp, ProteinComponent))

    if nprot > 1:
        errmsg = "Multiple ProteinComponent found, only one is supported"
        raise ValueError(errmsg)


ParseCompRet = Tuple[
    Optional[SolventComponent], Optional[ProteinComponent],
    Dict[SmallMoleculeComponent, OFFMol],
]


def get_components(state: ChemicalSystem) -> ParseCompRet:
    """
    Establish all necessary Components for the transformation.

    Parameters
    ----------
    state : ChemicalSystem
      ChemicalSystem to get all necessary components from.

    Returns
    -------
    solvent_comp : Optional[SolventComponent]
      If it exists, the SolventComponent for the state, otherwise None.
    protein_comp : Optional[ProteinComponent]
      If it exists, the ProteinComponent for the state, otherwise None.
    openff_mols : Dict[str, openff.toolkit.Molecule]
    """
    solvent_comp = [comp for comp in state.values()
                    if isinstance(comp, SolventComponent)]
    if len(solvent_comp) == 0:
        solvent_comp = None
    else:
        solvent_comp = solvent_comp[0]

    protein_comp = [comp for comp in state.values()
            if isinstance(comp, ProteinComponent)]
    if len(protein_comp) == 0:
        protein_comp = None
    else:
        protein_comp = protein_comp[0]

    off_small_mols = {}
    for comp in state.components.values():
        if isinstance(comp, SmallMoleculeComponent):
            off_small_mols[comp] = comp.to_openff()

    return solvent_comp, protein_comp, off_small_mols