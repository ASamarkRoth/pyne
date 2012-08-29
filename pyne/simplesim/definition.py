#!/usr/bin/env python

"""The ``definition`` module can be imported as such::

    from pyne.simplesim import definition

Below is the reference for this module.

"""
# TODO check overwriting warning.
# TODO test the exceptions for getting *_num() not in list/dict.
import abc
import collections
import pickle
import json
import warnings

import numpy as np

from pyne import material
from pyne.simplesim import cards

class IDefinition(object):
    """
    TODO
    """
    __metaclass__ = abc.ABCMeta

    def __init__(self, fname=None, verbose=True):
        """
        TODO
        """
        self.verbose = verbose
        if fname is not None:
            if self.verbose:
                print "Opening definition stored in %s." % fname
            self._open(fname)
        else:
            if self.verbose:
                print "Creating a new definition."
            self._create_new()

    @abc.abstractmethod
    def _create_new(self):
        """Definition started from scratch. Initialize all fields. """
        raise NotImplementedError

    @abc.abstractmethod
    def save(self, fname):
        """Save object data to a JSON file."""
        fid = open(fname, 'w')
        #pickle.dump(self, fid)
        fid.write(DefinitionEncoder(indent=3).encode(self))
        fid.close()

    @abc.abstractmethod
    def _open(self, fname):
        """Open object data from a JSON file."""
        # TODO Ensure the file exists.
        fid = open(fname)
        self = pickle.load(fname)
        fid.close()

    def _assert_unique(self, card_type, card):
        """Checks that the name on a card has not already been used for another
        card.

        """
        # TODO Don't require the user to pass the card_type string.
        if card_type == 'cell':
            dict_to_check = self.cells
        elif card_type == 'surface':
            dict_to_check = self.surfaces
        elif card_type == 'material':
            dict_to_check = self.materials
        elif card_type == 'source':
            dict_to_check = self.source
        elif card_type == 'tally':
            dict_to_check = self.tally
        elif card_type == 'misc':
            dict_to_check = self.misc
        elif card_type == 'transformation':
            dict_to_check = self.transformations
        elif card_type == 'dist':
            dict_to_check = self.dists
        else:
            raise ValueError("The input ``card_type`` must be either "
                    "'cell', 'surface', 'material', 'source', "
                    "'tally', or 'misc'.")
        if card.name in dict_to_check and self.verbose:
            warnings.warn("Card {0!r}, type {1!r} is already part of the "
                    "definition; overwriting.".format(card.name, card_type))
            #raise UserWarning("Card {0!r}, type {0!r} is already part of the "
            #        "definition; overwriting.".format(card.name, card_type))
            #raise Exception("The %s name %s has already been used for "
            #        "another %s" % (card_type, card.name, card_type))

    @property
    def verbose(self): return self._verbose

    @verbose.setter
    def verbose(self, value): self._verbose = value


class SystemDefinition(IDefinition):
    """This class creates a system definition as is done in MCNPX: homogeneous
    regions in space in the reactor, called cells, are defined through the
    intersection, union, etc of surfaces and are filled by materials. The
    definition of materials is done using the `material` module of PyNE.

    """
    def __init__(self, fname=None, verbose=True):
        """Creates a new reactor definition or loads one from a JSON file."""
        super(SystemDefinition, self).__init__(fname, verbose)

    def _create_new(self):
        self._surfaces = collections.OrderedDict()
        self._materials = collections.OrderedDict()
        self._cells = collections.OrderedDict()

    def add_cell(self, cell):
        """

        """
        if self.verbose:
            print "Adding cell %s." % cell.name
        # Only add the cell if a cell with the same name hasn't been added
        # already.
        self._assert_unique('cell', cell)
        # Add all surfaces that aren't already added. Do this by walking the
        # region tree and calling _add_unique_surfaces() at the leaves.
        cell.region.walk(self._add_unique_surfaces)
        # Only add the material if this is not a void cell and if it doesn't
        # already exist.
        if (cell.material and cell.material.name not in self.materials):
            self.add_material(cell.material)
        # Constituent surfaces and material have been added, so we can added
        # the cell.
        self._cells[cell.name] = cell

    def add_surface(self, surface):
        """This method is only used by the user for surfaces that are not on a
        cell card. Surfaces on a cell card are added automatically. Duplication
        is checked by card name, not by using Python's 'is' operator to compare
        the objects.

        """
        self._assert_unique('surface', surface)
        self._surfaces[surface.name] = surface

    def _add_unique_surfaces(self, regionleaf):
        name = regionleaf.surface.name
        if self.verbose:
            print "Trying to add surface {0!r}...".format(name)
        if name not in self.surfaces:
            self.add_surface(regionleaf.surface)
            if self.verbose:
                print "  Surface {0!r} added successfully.".format(name)
        else:
            if self.verbose:
                print ("  Surface {0!r} already exists in the "
                        "definition.".format(name))

    def add_material(self, material):
        """This method is only used by the user for materials that are not on a
        cell card.  Materials on cell cards are added automatically.

        """
        if material.name == None or material.name == '':
            raise ValueError("The ``name`` property of the material cannot "
                    "be empty.")
        self._assert_unique('material', material)
        self._materials[material.name] = material

    def cell_num(self, name):
        # TODO removing cards.
        # Must add one because indices start at 0 but card numbers at 1.
        if name not in self.cells:
            raise StandardError("Cell {0!r} is not in the system.".format(
                    name))
        return self.cells.keys().index(name) + 1

    def surface_num(self, name):
        # Must add one because indices start at 0 but card numbers at 1.
        if name not in self.surfaces:
            raise StandardError("Surface {0!r} is not in the system.".format(
                    name))
        num = self.surfaces.keys().index(name) + 1
        if isinstance(self.surfaces[name], cards.Facet):
            return num + self.surfaces[name].number / 10
        return num

    def material_num(self, name):
        # Must add one because indices start at 0 but card numbers at 1.
        if name not in self.materials:
            raise StandardError("Material {0!r} is not in the system.".format(
                    name))
        return self.materials.keys().index(name) + 1

    def remove_cell(self, name):
        raise Exception("Not implemented.")

    def remove_surface(self, name):
        raise Exception("Not implemented.")

    def remove_material(self, name):
        raise Exception("Not implemented.")

    def save(self, fname):
        """Saves definition to a JSON file. It is unlikely that the class will
        be amenable to json.dump()."""
        super(SystemDefinition, self).save(fname)

    def _open(self, fname):
        super(SystemDefinition, self)._open(fname)

    @property
    def surfaces(self):
        """Ordered dictionary of surfaces (from :py:class:`cards.ISurface`)."""
        # TODO document that the user should not add cards directly, but can
        # modify them if so inclined.
        return self._surfaces

    @property
    def materials(self):
        """Ordered dictionary of materials (from :py:mod:`pyne.material`)."""
        return self._materials

    @property
    def cells(self):
        """Ordered dictionary of cells (:py:class:`cards.Cell` or subclass)."""
        return self._cells


class SimulationDefinition(IDefinition):
    """
    
    This is basically where all the data cards are stored. The easy name for
    this class is either OptionsDefinition (Serpent) or DataDefinition (MCNP),
    but I'm not too happy with either. I'd like any ideas for this. This may
    need to be subclassed for different codes, because different codes do not
    provide the same options.

    """
    def __init__(self, systemdef, fname=None, verbose=True):
        """Creates a new options definition or loads one from a file."""

        super(SimulationDefinition, self).__init__(fname, verbose)
        # TODO when saving a simulation def, the the system def should also be
        # saved, and so this assignment that happens on this next line
        # shouldn't happen this way.
        self.sys = systemdef

    def _create_new(self):
        """Initialize any attributes/properties."""

        self._source = collections.OrderedDict()
        self._tally = collections.OrderedDict()
        self._misc = collections.OrderedDict()

    def add_source(self, card):
        if not isinstance(card, cards.ISource):
            raise ValueError("Only cards subclassed from ``ISource`` can be "
                    "added by this method. User provided {0}.".format(card))
        self._assert_unique('source', card)
        self._source[card.name] = card

    def add_tally(self, card):
        # TODO check cells and surfaces? only if moving to string refs.
        if not isinstance(card, cards.ITally):
            raise ValueError("Only cards subclassed from ``ITally`` can be "
                    "added by this method. User provided {0}.".format(card))
        self._assert_unique('tally', card)
        self._tally[card.name] = card

    def add_misc(self, card):
        # TODO check references to tallies? only if moving to string refs.
        if not isinstance(card, cards.IMisc):
            raise ValueError("Only cards subclassed from ``IMisc`` can be "
                    "added by this method. User provided {0}.".format(card))
        self._assert_unique('misc', card)
        self._misc[card.name] = card

    def remove_source(self, name):
        raise Exception("Not implemented.")

    def remove_tally(self, name):
        raise Exception("Not implemented.")

    def remove_misc(self, name):
        raise Exception("Not implemented.")

    def save(self, fname):
        """Saves definition to a JSON file. It is unlikely that the class will
        be amenable to json.dump()."""
        super(SimulationDefinition, self).save(fname)

    def _open(self, fname):
        pass

    @property
    def sys(self):
        return self._sys

    @sys.setter
    def sys(self, value):
        self._sys = value

    @property
    def source(self):
        """Ordered dictionary of source cards (from :py:class:`cards.ISource`)

        """
        return self._source

    @property
    def tally(self):
        """Ordered dictionary of tallies (from :py:class:`cards.ITally`)."""
        return self._tally

    @property
    def misc(self):
        """Ordered dictionary of misc. cards (from :py:class:`cards.IMisc`)."""
        return self._misc


class MCNPSimulation(SimulationDefinition):
    """

    """
    def _create_new(self):
        """Initialize any attributes/properties."""
        super(MCNPSimulation, self)._create_new()
        self._transformations = collections.OrderedDict()
        self._tally_surfacecurrent = collections.OrderedDict()
        self._tally_surfaceflux = collections.OrderedDict()
        self._tally_cellflux = collections.OrderedDict()
        self._tally_cellenergydep = collections.OrderedDict()
        self._tally_cellfissiondep = collections.OrderedDict()
        self._tally_pulseheight = collections.OrderedDict()
        self._tally_detector = collections.OrderedDict()
        self._dists = collections.OrderedDict()

    def add_tally(self, card):
        """Adds a tally card to the simulation.

        Parameters
        ----------
        card : :py:class:`cards.ICard` or subclass
            The tally card to be added to the simulation.

        """
        super(MCNPSimulation, self).add_tally(card)
        if isinstance(card, cards.SurfaceCurrent):
            self._tally_surfacecurrent[card.name] = card
        elif isinstance(card, cards.SurfaceFlux):
            self._tally_surfaceflux[card.name] = card
        elif isinstance(card, cards.CellFlux):
            self._tally_cellflux[card.name] = card
        elif isinstance(card, cards.CellEnergyDeposition):
            self._tally_cellenergydep[card.name] = card
        elif isinstance(card, cards.CellFissionEnergyDeposition):
            self._tally_cellfissiondep[card.name] = card
        elif isinstance(card, (cards.CellPulseHeight,
                cards.CellChargeDeposition)):
            self._tally_pulseheight[card.name] = card
        elif isinstance(card, cards.IDetector):
            self._tally_detector[card.name] = card
        else:
            raise Exception("Unrecognized tally card {0}.".format(card))

    def tally_num(self, name):
        """Retrieve the number of a :py:class:`cards.ITally` card in the MCNP
        input file.

        Parameters
        ----------
        name : str
            Name of the tally. Names must be unique across all tally types.

        Returns
        -------
        tally_num : int
            The tally number for a given tally type. For the first cell flux
            tally, a value of 1 is returned, not 14.

        """
        card = self.tally[name]
        # Must add one because indices start at 0 but card numbers at 1.
        if isinstance(card, cards.SurfaceCurrent):
            return self._tally_surfacecurrent.keys().index(name) + 1
        elif isinstance(card, cards.SurfaceFlux):
            return self._tally_surfaceflux.keys().index(name) + 1
        elif isinstance(card, cards.CellFlux):
            return self._tally_cellflux.keys().index(name) + 1
        elif isinstance(card, cards.CellEnergyDeposition):
            return self._tally_cellenergydep.keys().index(name) + 1
        elif isinstance(card, cards.CellFissionEnergyDeposition):
            return self._tally_cellfissiondep.keys().index(name) + 1
        elif isinstance(card, (cards.CellPulseHeight,
                cards.CellChargeDeposition)):
            return self._tally_pulseheight.keys().index(name) + 1
        elif isinstance(card, cards.IDetector):
            return self._tally_detector.keys().index(name) + 1
        else:
            raise Exception("Unrecognized tally type. name {0}.".format(name))

    def remove_tally(self, name):
        raise Exception("Not implemented.")

    def add_transformation(self, card):
        """Adds a transformation card to the simulation.

        Parameters
        ----------
        card : :py:class:`cards.Transformation` or subclass
            The card to be added to the simulation.

        """
        if not isinstance(card, cards.Transformation):
            raise ValueError("Only ``Transformation``s can be "
                    "added by this method. User provided {0}.".format(card))
        self._assert_unique('transformation', card)
        self._transformations[card.name] = card

    def transformation_num(self, name):
        """Retrieve the number of a :py:class:`cards.Transformation` card in
        the MCNP input file.

        Parameters
        ----------
        name : str
            Name of the :py:class:`cards.Transformation`. Names must be unique
            across all transformations.

        Returns
        -------
        transformation_num : int
            The transformation number.

        """
        if name not in self.transformations:
            raise StandardError("Transformation {0!r} is not in "
                    "the simulation.".format(name))
        return self.transformations.keys().index(name) + 1

    def add_dist(self, card):
        """Adds a distribution card to the simulation.

        Parameters
        ----------
        card : :py:class:`cards.Distribution` or subclass
            The card to be added to the simulation.

        """
        if not isinstance(card, cards.Distribution):
            raise ValueError("Only ``Distribution`` cards can be "
                    "added by this method. User provided {0}.".format(card))
        self._assert_unique('dist', card)
        self._dists[card.name] = card

    def dist_num(self, name):
        """Retrieve the number of a :py:class:`cards.Distribution` card in
        the MCNP input file.

        Parameters
        ----------
        name : str
            Name of the :py:class:`cards.Distribution`. Names must be unique
            across all distributions, and perhaps across cell and surface
            cards.

        Returns
        -------
        dist_num : int
            The distribution number.

        """
        if name not in self.dists:
            raise StandardError("Distribution {0!r} is not in "
                    "the simulation.".format(name))
        return self.dists.keys().index(name) + 1

    @property
    def transformations(self):
        """Ordered dictionary of transformation cards (from
        :py:class:`cards.Transformation`).

        """
        return self._transformations

    @property
    def dists(self):
        """Ordered dictionary of distribution cards (from
        :py:class:`cards.Distribution`).

        """
        return self._dists


class DefinitionEncoder(json.JSONEncoder):
    # TODO circular reference issue.
    def default(self, obj):
        try:
            if isinstance(obj, cards.ISurface):
                # TODO something like this to get around the circular
                # reference.
                return obj.name
            if isinstance(obj, material.Material):
                # Issue with stlconverters.
                return repr(obj)
            if hasattr(obj, '__dict__'):
                mydict = obj.__dict__
                for key, val in mydict.items():
                    if isinstance(val, np.ndarray):
                        mydict[key] = val.tolist()
                return mydict
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            #if isinstance(obj, cards.Cell) or issubclass(obj, cards.Cell):
            #    print "cell"
            #    return ''
            return json.JSONEncoder.default(self, obj)
        except:
            print "exception: "
            print type(obj)
            print obj
            raise

