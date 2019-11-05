#!/usr/bin/env python

# Author: Martin Lints, martin.lints@ioc.ee
# Year: 2019 (originally 2017 for python2)

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 3
# of the License, or (at your option) any later version.

# commands constructed according to Agilent 33250A manual
  
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
  
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
  
#####################################################################


import pyvisa as visa
import time
import struct


class Agilent(object):
    """
    Class for communicating with Agilent Arbitrary Waveform Generator 33250A

    Initialize with
    Agilent(dev=u'ASRL/dev/ttyUSB0::INSTR', br=57600)
    where dev is the device (here using Linux notation and ttyUSB0)
    br is baudrate

    Methods
    ------------


    upload_array(arr): 64k only, slow version, do not use
    """

    def __init__(self, dev = u'ASRL/dev/ttyUSB0::INSTR', br = 57600):
        """
        start on dev/ttyUSB0 (modify code to change)
        br: baudrate (=57600)
        t_o : timeout
        """
        self.rm = visa.ResourceManager()
        #use self.rm.list_resources() to find resources
        self.ag = self.rm.open_resource(dev)
        self.ag.baud_rate = br
        self.ag.set_visa_attribute(visa.constants.VI_ATTR_ASRL_FLOW_CNTRL,
                                   visa.constants.VI_ASRL_FLOW_DTR_DSR)
        #visa.constants.VI_ASRL_FLOW_DTR_DSR)
        #visa.constants.VI_ASRL_FLOW_RTS_CTS)
        self.ag.write('*IDN?')
        print(self.ag.read())


    def upload_array(self, arr):
        """
        upload array of data to VOLATILE memory of Agilent

        right now only accepts array of 64000 elements
        Slow version, do not use. Use upload_binary instead
        """
        self.ag.write_raw('DATA:DAC VOLATILE' )
        # pause for 1 ms like manual requires
        time.sleep(1e-2)
        for i in xrange(1600):
            print("doing {}th of 64000".format(i*40))
            ctstr1 = ', '.join(map(str, arr[i*40:(i+1)*40]/2))
            #self.ag.write_raw(u', {}'.format(ctstr1))
            self.ag.write_raw(', {}'.format(ctstr1))
            time.sleep(0.1)

        #self.ag.write_raw(u'\n')
        self.ag.write_raw('\n')


    def upload_binary(self, arr):
        """binary upload version:
         also only accepts array of 64000 elements
        """
        self.ag.write("form:bord swap")
        binarry = b"".join([struct.pack("<h", val) for val in arr])
        self.ag.write_raw(b'data:dac volatile, #6128000') #6 cmd decimals,128k num
        time.sleep(0.5)
        self.ag.write_raw(binarry) # python3: already bytes
        self.ag.write_raw(b'\n')
        

    def save_volatile(self, arbname="MYARB"):
        """
        At the moment, saves to "MYARB" AND SELECTS IT
        """
        #  Copy the arbitrary waveform to non-volatile memory, using DATA:COPY
        self.ag.write('DATA:COPY {}, VOLATILE'.format(arbname))
        #  Select the arbitrary waveform to output FUNC:USER
        # (user-defined as opposed to internal functions)
        self.ag.write('FUNC:USER {}'.format(arbname))


    def burst(self, ncyc=1):
        """
        Example of a method for running the code by burst:
        We select burst mode with relevant arguments
        setup the trigger source, enable output and trigger the burst
        """ 
        self.ag.write('OUTP OFF')
        self.ag.write('BURS:MODE TRIG')
        self.ag.write('BURS:INT:PER 1') #set burst period (interval for int. trig 1 us to 50sec
        self.ag.write('BURS:PHAS 0')
        self.ag.write('TRIG:SOUR BUS')
        self.ag.write('BURS:STAT ON')
        self.ag.write('OUTP ON')
        self.ag.write('*TRG')

    def close(self):
        self.ag.close()

    def write(self, txt):
        """
        write commands in text mode
        """
        self.ag.write(txt)
        
    def read(self):
        """Read the returned data"""
        return self.ag.read()
        
if __name__ == "__main__":
    import numpy as np
    from pylab import *
    wg = Agilent()
    
    # construct the signal
    N = 64000
    f0 = 200e2
    f1 = 1e7
    t1 = 1e-3
    tv = np.linspace(0, t1, N)
    phi = 2*np.pi*(f0*tv + ((f1-f0)*tv**2)/(2*t1))
    ct = (2047*np.sin(phi)).astype(int)


    #uplaod the signal
    wg.upload_binary(ct)
    


    wg.save_volatile('buu') # 
    #wg.burst()  # burst needs more work

    

    wg.write('DATA:COPY MYARB, VOLATILE')
    wg.write('FUNC:USER MYARB')
    wg.write('FUNC USER')
    wg.write('OUTP ON')
    wg.write('OUTP OFF')
    
    wg.close()

    #wg.burst()
