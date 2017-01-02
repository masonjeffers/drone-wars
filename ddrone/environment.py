from accesspoint import AccessPoint
import commands

class Environment:
    
    def __init__(self, d=None, s=None, v=False):
        
        self.device = d
        self.ssid = s
        self.accesspoints = None
        self.initialized = False
        self.verbose = v
        
        if (d and s):
            self.__initialize(d, s)
        
    def __initialize(self, d, s):
        
        self.device = d
        self.ssid = s
        self.accesspoints = self.__getaccesspoints(d, s)
        self.initialized = True
        
        if self.verbose: print "Environment initialized!"

    def __getaccesspoints(self, device, ssid):

        out = commands.searchssid(device, ssid)
        ssids = filter(lambda item: len(item) > 0, map(lambda line: (line.replace('SSID:','')).strip(), out.split('\n')))
        accesspoints = map(lambda ssid: AccessPoint(ssid), ssids)
        
        if self.verbose: print "FOUND: " + str(map(lambda accesspoint: accesspoint.ssid, accesspoints))

        return accesspoints