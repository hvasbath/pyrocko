import numpy as num

from pyrocko.guts import Float
from pyrocko import moment_tensor, gf

from .base import SourceGenerator
from ..base import ScenarioError

km = 1e3
guts_prefix = 'pf.scenario'


class RectangularSourceGenerator(SourceGenerator):
    depth_min = Float.T(default=0.0)
    depth_max = Float.T(default=5*km)

    strike = Float.T(
        optional=True)
    dip = Float.T(
        optional=True)
    rake = Float.T(
        optional=True)
    depth = Float.T(
        optional=True)
    width = Float.T(
        optional=True)
    length = Float.T(
        optional=True)

    def get_source(self, ievent):
        rstate = self.get_rstate(ievent)
        time = rstate.uniform(self.time_min, self.time_max)
        lat, lon = self.get_latlon(ievent)
        depth = rstate.uniform(self.depth_min, self.depth_max)
        magnitude = rstate.uniform(self.magnitude_min, self.magnitude_max)

        moment = moment_tensor.magnitude_to_moment(magnitude)

        # After Mai and Beroza (2000)
        length = num.exp(-6.27 + 0.4*num.log(moment))
        width = num.exp(-4.24 + 0.32*num.log(moment))

        length = length if not self.length else self.length
        width = width if not self.width else self.width
        depth = depth if not self.depth else self.depth

        if self.strike is None and self.dip is None and self.rake is None:
            strike, rake = rstate.uniform(-180., 180., 2)
            dip = rstate.uniform(0., 90.)
        else:
            if None in (self.strike, self.dip, self.rake):
                raise ScenarioError(
                    'RectangularFaultGenerator: '
                    'strike, dip, rake'
                    ' must be used in combination')

            strike = self.strike
            dip = self.dip
            rake = self.rake

        source = gf.RectangularSource(
            time=float(time),
            lat=float(lat),
            lon=float(lon),
            magnitude=magnitude,

            depth=float(depth),
            length=float(length),
            width=float(width),
            strike=float(strike),
            dip=float(dip),
            rake=float(rake))

        return source

    def add_map_artists(self, automap):
        for source in self.get_sources():
            automap.gmt.psxy(
                in_rows=source.outline(cs='lonlat'),
                L='+p2p,black',
                W='1p,black',
                G='black',
                *automap.jxyr)