
import os, logging, time
from pytopol.parsers.psf import PSFSystem
from pytopol.parsers.par import ParType
import blocks


module_logger = logging.getLogger('mainapp.charmmpar')

'''
http://www.ks.uiuc.edu/Training/Tutorials/namd/namd-tutorial-unix-html/node23.html
'''


class CharmmPar(object):
    """ A class for reading CHARMM PAR/PRM files. """

    def __init__(self, *args):
        """ Constructor.

        Args:
            One or more strings. Each string specifies path to one par file.

        Attributes:
            lgr         : logging.Logger
            fnames      : a list of paths to the par files
            bondpars    : ParType, bonds
            anglepars   : ParType, angles
            dihedralpars: ParType, dihedrals
            improperpars: ParType, impropers
            nonbonding  : ParType, nonbonding
            cmappars    : ParType, cmaps
            nbfix       : ParType, nbfix

        """

        self.lgr = logging.getLogger('mainapp.charmmpar.CharmmPar')
        self.lgr.debug(">> entering CharmmPar")


        self.fnames = args
        self.bondpars     = ParType(sym=True, mult=False, name='bond'      )
        self.anglepars    = ParType(sym=True, mult=False, name='angle'     )
        self.dihedralpars = ParType(sym=True, mult=True,  name='dihedral'  )
        self.improperpars = ParType(sym=True, mult=False, name='improper'  )
        self.nonbonding   = ParType(sym=False,mult=False, name='nonbonding')
        self.nbfix        = ParType(sym=True, mult=False, name='nbfix')
        self.cmappars     = ParType(sym=False,mult=False, name='cmap')

        for p in args:
            self._parse_charmmpar(p)
            self.lgr.debug(self.__repr__())

        self.lgr.debug("<< leaving CharmmPar")



    def __repr__(self):
        return "%3d bonding, %3d angle, %3d dih, %3d imp, %3d nonbonding and %2d cmaps" % (
                len(self.bondpars), len(self.anglepars), len(self.dihedralpars),
                len(self.improperpars), len(self.nonbonding), len(self.cmappars))


    def _parse_charmmpar(self, fname):
        """ A method for parsing CHARMM PAR/PRM files. """

        self.lgr.debug("parsing parameter file: %s" % fname)
        t1 = time.time()

        # sections of the par file (doesn't include CMAP, which will be parsed separately)
        main_parts = {
          'BOND':   {'nfields':(4,),     'nheader':2, 'cont':self.bondpars    },
          'ANGL':   {'nfields':(5,7),    'nheader':3, 'cont':self.anglepars   },
          'TETH':   {'nfields':(5,7),    'nheader':3, 'cont':self.anglepars   },
          'DIHE':   {'nfields':(7,10,13),'nheader':4, 'cont':self.dihedralpars},
          'IMPR':   {'nfields':(7,10,13),'nheader':4, 'cont':self.improperpars},
          'IMPH':   {'nfields':(7,10,13),'nheader':4, 'cont':self.improperpars},
          'NONB':   {'nfields':(4,7),    'nheader':1, 'cont':self.nonbonding  },
          'NBON':   {'nfields':(4,7),    'nheader':1, 'cont':self.nonbonding  },
          'NBFI':   {'nfields':(4,),     'nheader':2, 'cont':self.nbfix       },
         }

        # check if the file exists
        if not os.path.exists(fname):
            raise IOError("the '%s' CHARMM PAR file doesn't exist" % fname)

        # cache all of lines
        with open(fname) as f:
            _lines = f.readlines()

        # check if this is a stream file
        is_stream_file = False
        stream_i = None
        stream_j = len(_lines)
        for m, line in enumerate(_lines):
            if line.startswith('read para'):
                is_stream_file = True
                stream_i = m + 1
                continue
            if is_stream_file:
                if line.strip().lower() == 'end':
                    stream_j = m

        if is_stream_file:
            _lines = _lines[stream_i:stream_j]


        # helper function to parse a line -------------------------------------
        def _parse_par_line(line, _curr_par):

            f = line.split()

            # check the number of fields
            if not len(f) in main_parts[_curr_par]['nfields']:
                return False, "section %s - number of fields didn't match: %d \n  %s" % (
                        _curr_par, len(f), line)

            if _curr_par in ('BOND',):
                if len(f) == 4:
                    at1, at2, kb, b0 = f
                    main_parts[_curr_par]['cont'].add_parameter((at1,at2), (float(kb),float(b0)))

            elif _curr_par in ('ANGL', 'TETH'):
                if len(f) == 5:
                    at1, at2, at3, ktetha, tetha0 = f
                    main_parts[_curr_par]['cont'].add_parameter(
                            (at1,at2,at3), (float(ktetha),float(tetha0), None, None) )
                elif len(f) == 7:
                    at1, at2, at3, ktetha, tetha0, kub, s0 = f
                    main_parts[_curr_par]['cont'].add_parameter(
                            (at1,at2,at3), (float(ktetha),float(tetha0), float(kub), float(s0)) )
                else:
                    raise ValueError(line)

            elif _curr_par in ('DIHE',):
                key = (f[0], f[1], f[2], f[3])
                nsets = int((len(f)-4)/3)
                for i in range(nsets):
                    kchi = float(f[4+ i*3+0])
                    n    = int  (f[4+ i*3+1])
                    delta= float(f[4+ i*3+2])
                    main_parts[_curr_par]['cont'].add_parameter(key, (kchi, n, delta) )


            elif _curr_par in ('IMPR', 'IMPH'):
                key = (f[0], f[1], f[2], f[3])
                nsets = int((len(f)-4)/3)
                for i in range(nsets):
                    kpsi = float(f[4+ i*3+0])
                    psi0 = float(f[4+ i*3+2])
                    main_parts[_curr_par]['cont'].add_parameter(key, (kpsi, psi0) )

            elif _curr_par in ('NONB', 'NBON'):
                if len(f) == 4:
                    at, tmp, epsilon, rmin2 = f
                    main_parts[_curr_par]['cont'].add_parameter(
                            at, (float(epsilon), float(rmin2), None, None) )
                elif len(f)==7:
                    at, tmp, epsilon, rmin2, tmp, epsilon14, rmin2_14 = f
                    main_parts[_curr_par]['cont'].add_parameter(
                            at, (float(epsilon), float(rmin2), float(epsilon14), float(rmin2_14)) )
                else:
                    raise ValueError(line)

            elif _curr_par in ('NBFI',):
                if len(f) == 4:
                    at1, at2, epsilon, rmin = f
                    main_parts[_curr_par]['cont'].add_parameter((at1,at2), (float(epsilon),float(rmin)))
                else:
                    raise NotImplementedError

            else:
                raise NotImplementedError

            return True, "OK"


        def _parse_cmap_lines(lines, cmappars):
            # assuming the cmap grid is 24x24

            n = 0   # should be zero for modulus
            p = []
            key = None
            for i, line in enumerate(lines):
                if n % (24*24) == 0:

                    if len(p) >0:
                        if len(p) != 24 * 24:
                            print('warning - not enough item for the cmap', key)
                        cmappars.add_parameter(key, p)

                    key = tuple(line.split()[:8])

                    p = []
                    n = 1

                else:
                    p += list(map(float, line.split()))
                    n = len(p)

            # last one
            if len(p) > 0:
                if len(p) != 24 * 24:
                    print('warning - not enough item for the cmap', key)
                cmappars.add_parameter(key, p)



        # go over the lines in the file
        _main_sections = tuple(main_parts.keys())
        _curr_par      = None

        cm_lines = [] # for caching CMAP lines
        continuation = None

        for ln, line in enumerate(_lines):
            if continuation:
                line = continuation + line
            if '!' in line:
                line = line[0: line.index('!')]
            line = line.strip()

            if line == '':
                continue

            if line.endswith('-'):
                continuation = line[0:-1] + " "
                continue
            continuation = None

            if line=='END' or line=='end':
                break

            elif line.startswith('*'):
                pass

            elif line.startswith('cutnb'):
                pass

            elif line.startswith(( 'HBOND', 'ATOM')):
                _curr_par = None

            elif line.startswith('CMAP'):
                _curr_par = 'CMAP'

            elif line.startswith(_main_sections):
                _curr_par = line[:4]

            elif _curr_par is not None:
                # parsing normal line that has parameter data

                if _curr_par == 'CMAP':
                    cm_lines.append(line)
                else:
                    result, msg = _parse_par_line(line, _curr_par)

                    if result is False:
                        self.lgr.error(msg)
                        return False

        if len(cm_lines) > 0:
            _parse_cmap_lines(cm_lines, self.cmappars)

        t2 = time.time()
        self.lgr.debug("parsing took %4.1f seconds" % (t2-t1))






    def add_params_to_system(self, system, panic_on_missing_param=True):
        self.lgr.debug("adding parameters to the system...")
        assert isinstance(system , PSFSystem)

        added_atomtypes = []
        added_bondtypes = []
        added_angletypes = []
        added_dihedraltypes = []
        added_impropertypes = []
        added_cmaptypes = []

        system.forcefield = 'charmm'

        for mi, mol in enumerate(system.molecules):

            for atom in mol.atoms:
                at = atom.get_atomtype()
                if not at:
                    raise ValueError('atom type for atom %s was not found' % atom)

                if at in added_atomtypes:
                    continue

                added_atomtypes.append(at)
                p = self.nonbonding.get_parameter(at)

                if len(p) != 1:
                    msg = "for atom type %s, %d parameters found (expecting 1, found: %s)" % (at, len(p), p)
                    if not panic_on_missing_param:
                        self.lgr.error(msg)
                        continue
                    else:
                        raise ValueError(msg)

                assert len(p[0]) == 4
                lje, ljl, lje14, ljl14 = p[0]

                newat = blocks.AtomType('charmm')
                newat.atype = at
                newat.mass  = atom.mass
                newat.charge= atom.charge
                newat.charmm['param']['lje'] = lje
                newat.charmm['param']['ljl'] = ljl
                newat.charmm['param']['lje14'] = lje14
                newat.charmm['param']['ljl14'] = ljl14
                system.atomtypes.append(newat)



            for bond in mol.bonds:
                at1 = bond.atom1.get_atomtype()
                at2 = bond.atom2.get_atomtype()

                if (at1, at2) in added_bondtypes or (at2, at1) in added_bondtypes:
                    continue

                added_bondtypes.append((at1, at2))
                p = self.bondpars.get_parameter((at1, at2))

                if len(p) != 1:
                    msg = "for bond %s-%s, %d parameters found (expecting 1, found %s)" % (at1, at2, len(p), p)
                    if not panic_on_missing_param:
                        self.lgr.error(msg)
                        continue
                    else:
                        raise ValueError(msg)

                assert len(p[0]) == 2
                kb, b0 = p[0]

                newbt = blocks.BondType('charmm')
                newbt.atype1 = at1
                newbt.atype2 = at2
                newbt.charmm['param']['kb'] = kb
                newbt.charmm['param']['b0'] = b0
                system.bondtypes.append(newbt)



            for angle in mol.angles:
                at1 = angle.atom1.get_atomtype()
                at2 = angle.atom2.get_atomtype()
                at3 = angle.atom3.get_atomtype()

                if (at1, at2, at3) in added_angletypes or (at3, at2, at1) in added_angletypes:
                    continue

                added_angletypes.append((at1, at2, at3))
                p = self.anglepars.get_parameter((at1, at2, at3))

                if len(p) != 1:
                    msg = "for angle %s-%s-%s, %d parameters found (expecting 1, found %s)" % (
                        at1, at2, at3, len(p),p)
                    if not panic_on_missing_param:
                        self.lgr.error(msg)
                        continue
                    else:
                        raise ValueError(msg)

                assert len(p[0]) == 4
                ktetha, tetha0, kub, s0 = p[0]
                kub = kub if kub else 0
                s0  = s0  if s0  else 0

                newagt = blocks.AngleType('charmm')
                newagt.atype1 = at1
                newagt.atype2 = at2
                newagt.atype3 = at3
                newagt.charmm['param']['ktetha'] = ktetha
                newagt.charmm['param']['tetha0'] = tetha0
                newagt.charmm['param']['kub']    = kub
                newagt.charmm['param']['s0']     = s0

                system.angletypes.append(newagt)



            for dihedral in mol.dihedrals:
                at1 = dihedral.atom1.get_atomtype()
                at2 = dihedral.atom2.get_atomtype()
                at3 = dihedral.atom3.get_atomtype()
                at4 = dihedral.atom4.get_atomtype()

                if (at1, at2, at3, at4) in added_dihedraltypes or (at4, at3, at2, at1) in added_dihedraltypes:
                    continue

                added_dihedraltypes.append((at1, at2 , at3, at4))
                p = self.dihedralpars.get_charmm_dihedral_wildcard((at1, at2, at3, at4))

                if len(p) == 0:
                    msg = "for dihedral %s-%s-%s-%s no parameter was found" % (at1, at2, at3, at4)
                    if not panic_on_missing_param:
                        self.lgr.error(msg)
                        continue
                    else:
                        raise ValueError(msg)

                newdih = blocks.DihedralType('charmm')
                newdih.atype1 = at1
                newdih.atype2 = at2
                newdih.atype3 = at3
                newdih.atype4 = at4

                for dp in p:
                    kchi, n, delta = dp

                    m = {'kchi':kchi, 'n':n, 'delta': delta}
                    newdih.charmm['param'].append(m)

                system.dihedraltypes.append(newdih)



            for improper in mol.impropers:
                at1 = improper.atom1.get_atomtype()
                at2 = improper.atom2.get_atomtype()
                at3 = improper.atom3.get_atomtype()
                at4 = improper.atom4.get_atomtype()

                if (at1, at2, at3, at4) in added_impropertypes or (at4, at3, at2, at1) in added_impropertypes:
                    continue

                added_impropertypes.append((at1, at2, at3, at4))
                p = self.improperpars.get_charmm_improper_wildcard((at1, at2, at3, at4))

                if len(p) != 1:
                    msg = "for improper %s-%s-%s-%s, %d parameters found (expecting 1, found %s)" % (
                        at1, at2, at3, at4, len(p), p)
                    if not panic_on_missing_param:
                        self.lgr.error(msg)
                        continue
                    else:
                        raise ValueError(msg)

                assert len(p[0]) == 2
                kpsi, psi0 = p[0]

                newimp = blocks.ImproperType('charmm')
                newimp.atype1 = at1
                newimp.atype2 = at2
                newimp.atype3 = at3
                newimp.atype4 = at4

                # newimp.charmm['param']['kpsi'] = kpsi
                # newimp.charmm['param']['psi0'] = psi0

                m = {}
                m['kpsi'] = kpsi
                m['psi0'] = psi0

                newimp.charmm['param'].append(m)

                system.impropertypes.append(newimp)



            for cmap in mol.cmaps:
                at1 = cmap.atom1.get_atomtype()
                at2 = cmap.atom2.get_atomtype()
                at3 = cmap.atom3.get_atomtype()
                at4 = cmap.atom4.get_atomtype()
                at5 = cmap.atom5.get_atomtype()
                at6 = cmap.atom6.get_atomtype()
                at7 = cmap.atom7.get_atomtype()
                at8 = cmap.atom8.get_atomtype()

                if ((at1, at2, at3, at4, at5, at6, at7, at8)) in added_cmaptypes:
                    continue

                added_cmaptypes.append((at1, at2, at3, at4, at5, at6, at7, at8))
                p = self.cmappars.get_parameter((at1, at2, at3, at4, at5, at6, at7, at8))

                if len(p) != 1:
                    msg = "for cmap: %s-%s-%s-%s-%s-%s-%s-%s, %d parameters found (expecting 1, found %s)" % (
                        at1, at2, at3, at4, at5, at6, at7, at8, len(p), p)
                    if not panic_on_missing_param:
                        self.lgr.error(msg, len(p))
                        continue
                    else:
                        raise ValueError(msg)

                assert len(p[0]) == 24*24, '%d != %d' % (len(p[0]), 24*24)
                newcmt = blocks.CMapType('charmm')
                newcmt.atype1 = at1
                newcmt.atype2 = at2
                newcmt.atype3 = at3
                newcmt.atype4 = at4
                newcmt.atype5 = at5
                newcmt.atype6 = at6
                newcmt.atype7 = at7
                newcmt.atype8 = at8
                newcmt.charmm['param'] = p[0]

                system.cmaptypes.append(newcmt)


            for nbkey in list(self.nbfix._data.keys()):
                if mi != 0:
                    continue   # just for the first molecule

                at1, at2 = nbkey
                p = self.nbfix.get_parameter((at1, at2))
                if len(p) == 0:
                    continue  #

                print('adding pair param to the mol for %s-%s' % (at1,at2))

                if len(p) != 1:
                    msg = "for pair %s-%s, %d parameters found (expecting 1, found %s)" % (at1, at2, len(p), p)
                    if not panic_on_missing_param:
                        self.lgr.error(msg)
                        continue
                    else:
                        raise ValueError(msg)

                assert len(p[0]) == 2
                eps, rmin = p[0]
                newnb = blocks.InteractionType('charmm')
                newnb.atype1 = at1
                newnb.atype2 = at2
                newnb.charmm['param']['lje'] = eps
                newnb.charmm['param']['ljl'] = rmin

                system.interactiontypes.append(newnb)

if __name__ == '__main__':
    import sys
    c = CharmmPar(sys.argv[1])
    print(c)



