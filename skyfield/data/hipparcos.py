import os
import gzip
from skyfield.functions import to_polar
from skyfield.starlib import Star
from skyfield.timelib import T0
from skyfield.units import Angle

import binascii

days = T0 - 2448349.0625
url = 'ftp://cdsarc.u-strasbg.fr/cats/I/239/hip_main.dat.gz'

# from:
# https://stackoverflow.com/questions/3703276/how-to-tell-if-a-file-is-gzip-compressed
# to determine if a file is gzip compressed
def is_gz_file(filepath):
    """ determine if a file is gzipped using its first 2 bytes as a 
    magic number.

    A file that is like .tar.gz is not considered gzip compressed using
    this method.

    """
    with open(filepath, 'rb') as test_f:
        return binascii.hexlify(test_f.read(2)) == b'1f8b'

def gzopen( filename ):
    """ return a file-like object, if determining if it's gzipped or not """
    if is_gz_file( filename ):
        return gzip.GzipFile( filename )
    else:
        return open( filename )

class HipparcosError(Exception):
    pass

class Hipparcos(object):
    """ An Hipparcos catalog object, creates itself from a file
    structured like ftp://cdsarc.u-strasbg.fr/cats/I/239/hip_main.dat.gz
    the file can be gzip compressed or not

    """

    filename = None
    
    def __init__( self,
                  filename ):

        # check if the file exists
        if not os.path.isfile( filename ):
            raise HipparcosError( filename + ' does not exist.' )

        self.filename = filename

    def __getitem__( self, key ):
        """ 
        Access like a dictionary the key can be a string or integer
        into the Hipparcos catalog
        """
        return self.get( key )
        
    def get( self, which ):
        """Return a single star, or a list of stars, from the Hipparcos catalog.

        A call like `get('54061')` returns a single `Star` object, while
        `get(['54061', '53910'])` returns a list of stars.

        """
        if isinstance( which, list ):
            r = list()
            for w in which:
                # a bit of recursion to make this work with lists
                r.append( self.get( w ) )
            return r
        
        pattern = ('H|      %6s' % str( which ) ).encode('ascii')
        for star in self.load(lambda line: line.startswith(pattern)):
            return star

    def load( self, match_function ):
        """Yield the Hipparcos stars for which `match_function(line)` is true."""

        with gzopen( self.filename ) as f:
            for line in f:
                if match_function(line):
                    yield self.parse(line)
       
    def parse( self, line ):
        """Return a `Star` build by parsing a Hipparcos catalog entry `line`."""
        # See ftp://cdsarc.u-strasbg.fr/cats/I/239/ReadMe
        star = Star(
            ra=Angle(degrees=float(line[51:63])),
            dec=Angle(degrees=float(line[64:76])),
            ra_mas_per_year=float(line[87:95]),
            dec_mas_per_year=float(line[96:104]),
            parallax_mas=float(line[79:86]),
            names=[('HIP', int(line[8:14]))],
            )
        star._position_au += star._velocity_au_per_d * days
        distance, dec, ra = to_polar(star._position_au)
        star.ra = Angle(radians=ra, preference='hours')
        star.dec = Angle(radians=dec)
        return star


