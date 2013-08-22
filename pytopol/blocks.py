


from .validate import ValidateMixin



# -----------------------------------------------
#
# -----------------------------------------------
class Molecule(ValidateMixin):
    _valuetypes = dict(
        chains      = list,
        atoms       = list,
        residues    = list,
        bonds       = list,
        angles      = list,
        dihedrals   = list,
        impropers   = list,
        cmaps       = list,
        _anumb_to_atom = dict,
        forcefield  = str,
    )

    _allowed_values = dict(
        forcefield  = ['', 'charmm']
    )

    def __init__(self):
        self.chains    = []   
        self.atoms     = []   
        self.residues  = []

        self.bonds     = []
        self.angles    = []
        self.dihedrals = []
        self.impropers = []
        self.cmaps     = []

        self.forcefield= ''
        self._anumb_to_atom = {}


    def anumb_to_atom(self, anumb):
        '''Returns the atom object corresponding to an atom number'''

        assert isinstance(anumb, int), "anumb must be integer"

        if len(self._anumb_to_atom) == 0:   # empty dictionary

            if len(self.atoms) != 0:
                for atom in self.atoms:
                    self._anumb_to_atom[atom.number] = atom
                return self._anumb_to_atom[anumb]
            else:
                print("no atoms in the molecule")
                return False

        else:
            if anumb in self._anumb_to_atom:
                return self._anumb_to_atom[anumb]
            else:
                print("no such atom number (%d) in the molecule" % (numb))
                return False

    
    def renumber_atoms(self):

        if len(self.atoms) != 0:
            
            # reset the mapping
            self._anumb_to_atom = {}

            for i,atom in enumerate(self.atoms):
                atom.number = i+1   # starting from 1

        else:
            print("the number of atoms is zero - no renumbering")





# -----------------------------------------------
#
# -----------------------------------------------
class Chain(ValidateMixin):
    _valuetypes = dict(
        name    = str,
        residues= list,
        molecule= Molecule
    )

    def __init__(self):
        self.residues = []

# -----------------------------------------------
#
# -----------------------------------------------
class Residue(ValidateMixin):
    _valuetypes = dict(
        name    = str,
        number  = int,
        chain   = Chain,
        chain_name = str,
        atoms   = list,
    )

    def __init__(self):
        self.atoms  = []




# -----------------------------------------------
#
# -----------------------------------------------
class Atom(ValidateMixin):
    _valuetypes = dict(
        name    = str,
        number  = int,
        flag    = str,        # HETATM
        coords  = list,
        residue = Residue,
        occup   = float,
        bfactor = float,
        altlocs = list,
        atomtype= str,
        charge  = float,
        radius  = float,
        mass    = float,
        lje     = float,       # energy
        ljl     = float,       # length
        lje14   = float,
        ljl14   = float,
        chain   = str,
        resname = str,
        resnumb = int,
        altloc  = str,         # per atoms

    )

    def __init__(self):

        self.coords = []        # a list of coordinates (x,y,z) of models
        self.altlocs= []        # a list of (altloc_name, (x,y,z), occup, bfactor)



    def get_atomtype(self):
        if hasattr(self, 'atomtype'):
            return self.atomtype
        else:
            print("atom %s doesn't have atomtype" % self)
            return False





# # # # # # # # # # # # # # # # # # # # # # # # # # # # # #




# -----------------------------------------------
#
# -----------------------------------------------
class Param(ValidateMixin):
    _valuetypes = dict(
        kind    = str,
        coeffs  = tuple,
    )

    _allowed_values = dict(
        kind    = ['bond', 'angle', 'dihedral', 'improper', 'cmap' ],
    )

    def __init__(self, kind):
        self.kind   = kind
        self.coeffs = tuple()




# -----------------------------------------------
#
# -----------------------------------------------
class Bond(ValidateMixin):
    _valuetypes = dict(
        atom1   = Atom,
        atom2   = Atom,
        order   = int,     # if a bond is single/double or triple
        function= str,
        param   = Param
    )

    def __init__(self):
        self.param = Param('bond')



# -----------------------------------------------
#
# -----------------------------------------------
class Angle(ValidateMixin):
    _valuetypes = dict(
        atom1   = Atom,
        atom2   = Atom,
        atom3   = Atom,
        param   = Param
    )

    def __init__(self):
        self.param = Param('angle')



# -----------------------------------------------
#
# -----------------------------------------------
class Dihedral(ValidateMixin):
    _valuetypes = dict(
        atom1   = Atom,
        atom2   = Atom,
        atom3   = Atom,
        atom4   = Atom,
        param   = Param,       # shouldn't be used for charmm
        charmm_param = list,   # for charmm dihedrals with several multiplicities
    )

    def __init__(self):
        self.param = Param('dihedral')



# -----------------------------------------------
#
# -----------------------------------------------
class Improper(ValidateMixin):
    _valuetypes = dict(
        atom1   = Atom,
        atom2   = Atom,
        atom3   = Atom,
        atom4   = Atom,
        param   = Param
    )

    def __init__(self):
        self.param = Param('improper')



# -----------------------------------------------
#
# -----------------------------------------------
class CMap(ValidateMixin):
    _valuetypes = dict(
        atom1   = Atom,
        atom2   = Atom,
        atom3   = Atom,
        atom4   = Atom,
        atom5   = Atom,
        atom6   = Atom,
        atom7   = Atom,
        atom8   = Atom,
        param   = Param
    )

    def __init__(self):
        self.param = Param('cmap')
