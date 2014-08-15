import unittest
import os
import tempfile
import numpy as num
from pyrocko import fdsn, util, trace, iris_ws


def tts(t):
    if t is not None:
        return util.time_to_str(t)
    else:
        return '...'

stt = util.str_to_time


class FDSNStationTestCase(unittest.TestCase):

    def test_read_samples(self):
        ok = False
        for fn in ['geeil.iris.xml', 'geeil.geofon.xml']:
            fpath = self.file_path(fn)
            x = fdsn.station.load_xml(filename=fpath)
            for network in x.network_list:
                assert network.code == 'GE'
                for station in network.station_list:
                    assert station.code == 'EIL'
                    for channel in station.channel_list:
                        assert channel.code[:2] == 'BH'
                        for stage in channel.response.stage_list:
                            ok = True

            assert ok

            assert len(x.get_pyrocko_stations()) in (3, 4)
            for s in x.get_pyrocko_stations():
                assert len(s.get_channels()) == 3

            assert len(x.get_pyrocko_stations(
                time=stt('2010-01-15 10:00:00'))) == 1

    def test_retrieve(self):
        for site in ['geofon', 'iris']:
            fsx = fdsn.ws.station(site=site,
                                  network='GE', 
                                  station='EIL',
                                  level='channel')

            assert len(fsx.get_pyrocko_stations(
                time=stt('2010-01-15 10:00:00'))) == 1

    def file_path(self, fn):
        return os.path.join(os.path.dirname(__file__), 'stationxml', fn)

    def test_retrieve_big(self):
        for site in ['iris']:
            fpath = self.file_path('%s_1014-01-01_all.xml' % site)

            if not os.path.exists(fpath):
                with open(fpath, 'w') as f:
                    source = fdsn.ws.station(
                        site=site,
                        startbefore=stt('2014-01-01 00:00:00'),
                        endafter=stt('2014-01-02 00:00:00'),
                        level='station', parsed=False, matchtimeseries=True)

                    while True:
                        data = source.read(1024)
                        if not data:
                            break
                        f.write(data)

            fsx = fdsn.station.load_xml(filename=fpath)
            for station in fsx.get_pyrocko_stations():
                print station

            print len(fsx.get_pyrocko_stations())

    def test_response(self):
        tmin = stt('2014-01-01 00:00:00')
        tmax = stt('2014-01-02 00:00:00')
        sx = fdsn.ws.station(
            site='iris',
            network='IU',
            channel='?HZ',
            startbefore=tmin,
            endafter=tmax,
            level='channel', format='text', matchtimeseries=True)

        for nslc in sx.nslc_code_list:
            print nslc
            
            net, sta, loc, cha = nslc
            sxr = fdsn.ws.station(
                site='iris',
                network=net,
                station=sta,
                location=loc,
                channel=cha,
                startbefore=tmin,
                endafter=tmax,
                level='response', matchtimeseries=True)

            fi = iris_ws.ws_resp(
                network=net,
                station=sta,
                location=loc,
                channel=cha,
                tmin=tmin,
                tmax=tmax)
            
            _, fn = tempfile.mkstemp()
            fo = open(fn, 'w')
            while True:
                d = fi.read(1024)
                if not d:
                    break

                fo.write(d)

            fo.close()
            

            resp_sx = sxr.get_pyrocko_response(nslc, timespan=(tmin, tmax))
            resp_er = trace.Evalresp(fn, target='vel', nslc_id=nslc, time=tmin)
            fmin = 0.001
            fmax = 100.
            channel = sx.get_channels(nslc, timespan=(tmin, tmax))[0]
            if channel.sample_rate:
                fmax = channel.sample_rate.value * 0.5

            f = num.exp(num.linspace(num.log(fmin), num.log(fmax), 500))
            try:
                t_sx = resp_sx.evaluate(f)
                t_er = resp_er.evaluate(f)
                import pylab as lab

                abs_dif = num.abs(num.abs(t_sx) - num.abs(t_er)) / num.max(num.abs(t_er))

                mda = num.mean(abs_dif[f<0.5*fmax])

                pha_dif = num.abs(num.angle(t_sx) - num.angle(t_er))

                mdp = num.mean(pha_dif[f<0.5*fmax])

                print mda, mdp

                if mda > 0.03 or mdp > 0.04:
                    


                    lab.gcf().add_subplot(2,1,1)
                    lab.plot(f, num.abs(t_sx), color='black')
                    lab.plot(f, num.abs(t_er), color='red')
                    lab.xscale('log')
                    lab.yscale('log')


                    lab.gcf().add_subplot(2,1,2)
                    lab.plot(f, num.angle(t_sx), color='black')
                    lab.plot(f, num.angle(t_er), color='red')
                    lab.xscale('log')
                    lab.show()

                else:
                    print 'ok'
            except:
                print 'failed: ', nslc

                
                pass





import time
gt = None
def lap():
    global gt
    t = time.time()
    if gt is not None:
        diff = t - gt
    else:
        diff = 0

    gt = t
    return diff


if __name__ == '__main__':
    util.setup_logging('test_fdsn_station', 'warning')
    unittest.main()
