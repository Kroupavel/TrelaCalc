from cmd import Cmd
import numpy as np
import math 
import matplotlib
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import axes3d, Axes3D 
from scipy.integrate import odeint
import sys
import os.path

class Main(Cmd):
    def __init__(self):    
        """
        This program is responsible for the post-processing of the second and third order elastic constants (SOEC, TOEC).
        The input of the constants must be made through a file (see readme or example for more information)
        The input arguments are:  Input file, Output file, Pressure change, number of iteration steps, number of integration steps.
        The input file must be in the working directory. The name should be inputed without the .txt suffix.
        The output file will create a separate folder in the working directory of that name.
        If a folder of that name already exists it will use that folder and might overwrite files in it!
        The hydorstatic pressure applied in GPa. So to simulate 1 GPa, write 1.
        The number of iteration steps will determine the density of points for "surface integral" when calculating the directional Young moduli. 
        It also sets the smoothness of the final plots.
        This number affects the computing time the most so it is important to set it accordingly to desired result!:
        For normal plot 200-300 is a recomended value.
        For publication level graphs a 400-500 might be useful at a cost of higher computing time.
        If only numerical results are needed it can be set to 1 which will greatly decrease the computing time.
        The number of integration steps is for calculating the pressure derivatives. The effect on computing time is small.
        For normal pressure changes like 1,10,100 GPa the effect of n. of iteration steps is also small. However a 1000 is used as a standart value.   
        
        The output are three graphs (Young moduli (E) at zero pressure, the difference in E for given difference in pressure and the same graph normalized, all as a function of direction)
        Also a text file is created with numerical data (more details in store method).            
        """              
        if (len(sys.argv)!= 6): 
            self.inp = raw_input("Input file:")
            self.outfile = raw_input("Output file(Select or create a folder to which data is stored):") 
            self.pressure = float(raw_input("Applied pressure (in GPa):"))
            self.iteration = int(raw_input("number of iteration steps for surface integral (200-300 recomended):"))
            self.steps = int(raw_input("number of integration steps(1000 is a standart value):"))

        else:
            self.inp = str(sys.argv[1])
            self.outfile = str(sys.argv[2])
            self.pressure = float(sys.argv[3])
            self.iteration = int(sys.argv[4])
            self.steps = int(sys.argv[5])
            
        if self.outfile!="":
            if not os.path.exists(self.outfile):
                os.makedirs(self.outfile)

        a = Young()
        a.initialize(self.inp, self.outfile, self.pressure, self.iteration, self.steps)

class Young():
    def initialize(self, inp, output, pressure, iteration, steps):    
        """
        This program is responsible for afterprocessing of the second and third order elastic constants (SOEC, TOEC).
        The input of the constants must be made through a file (see readme or example for more information)
        The input arguments are:  Input file, Output file, Pressure change,
        number of iteration steps (200-300 are recomended for normal use, higher values will greatly increase the computing time but will give much smoother graphs)
        and number of integration steps (1000 is standartly used value but it seems to have little efect on precision and computing time)
        
        The output are three graphs (Young moduli (E) at zero pressure, the difference in E for given applied pressure and the same graph normalized, all as a function of direction)
        Also a text file is created with numerical data (more details in store method).            
        """              
        self.completeinput = inp+".txt"
        self.pressure = pressure
        self.iteration = iteration
        self.steps = steps
        self.outpath = output  
            
        self.theta = np.linspace(0,2*math.pi, self.iteration) # Surface integral of theta from 0 to two pi 
        self.phi = np.linspace(0,math.pi, self.iteration) # Surface integral of phi from 0 to pi. Together with theta covers all directions
        self.data = np.zeros((self.iteration**2,3)) # here the data for plot will be stored
        self.data2 = np.zeros((self.iteration**2,3)) # Every variable with 2 at the end is for the second set of data and carries out the same function as non integered variable. 
        
        #The loop below defines all necessary variables in the apropriate format
        self.preparearrays = ("x1","y1","z1","r1","x2","y2","z2","r2","difx","dify","difz","difr","xnorm","ynorm","znorm","rnorm")
        for name in self.preparearrays:
            exec("self.%s = np.zeros((self.iteration,self.iteration))" %name)
            
             
        self.process()
        
            
        
    def pres(self):
        """
        This method calls an additional script that calculates the change in SOEC 
        for a given change in pressure. 
        Needed input are SOEC and TOEC, the pressure change and the number of integration steps
        The output is an array of all the intermediate data used for calculation 
        e.g. if 1000 steps used there will be 1000 triplets of SOEC values
        """
        self.constants = list(np.genfromtxt(self.completeinput, dtype = float, comments = "#"))
        b = Integration(self.constants, float(self.pressure), self.steps)        
        self.c = np.zeros((self.steps,3)) # self.c is the array containing the SOEC as a function of pressure
        self.c = b.solve()
        
       
    def young(self):
        """
        This method uses the data from pres and calculates:
        Elastic compliances, Young moduli in 100, 110, 111 direction and anisotropy
        The values are calculated for all the small changes in SOEC from pres method
        This is not necessary atm but if more rigorous analysis is needed it might be useful.
        The results at zero and user pressure are stored in the output file. 
        """  
        
        self.res = np.zeros((self.steps,3)) # elastic compliances S11, S12, S44
        self.E = np.zeros((self.steps,3))
        self.anisotropy = np.array([0.0]*self.steps)
        # Calculates all the variables for all the data obtained from the integration
        for i in range(0, int(self.steps)): 
            self.denominator = (self.c[i,0]**2+self.c[i,0]*self.c[i,1]-2*self.c[i,1]**2)
        
            self.res[i,0] = (self.c[i,0]+self.c[i,1])/(self.denominator) #s11   
            self.res[i,1] = (-self.c[i,1]/(self.denominator)) #S12
            self.res[i,2] = 1/self.c[i,2] #S44
            
            #The two following variable should be equal to C11 and C12, can be used as check
            #self.check1= (self.res[i,0]+self.res[i,1])/((self.res[i,0]-self.res[i,1])*(self.res[i,0]+2*self.res[i,1]))
            #self.check2= (-1*self.res[i,1])/((self.res[i,0]-self.res[i,1])*(self.res[i,0]+2*self.res[i,1]))
           
            self.var = (self.res[i,0]-self.res[i,1]-0.5*self.res[i,2])
            self.E[i,0] = 1/self.res[i,0] #E100 
            self.E[i,1] = 1/(self.res[i,0]-0.5*self.var) #E110
            self.E[i,2] = 1/(self.res[i,0]-2*self.var/3) #E110 
            self.anisotropy[i] = 2*self.c[i,2]/(self.c[i,0]-self.c[i,1]) # Anisotropy
 
      

    def polycrystal(self):
        """
        This method calculates the polycrystal properties of the material such as:
        Polycrystalline shear at zero and user defined pressure. It uses both Voigt and Reuss method.
        Polycrystalline SOEC at zero pressure. Again, both the method of Voigt and Reuss is used
        The results are shown in the output file        
        """
        self.shearV = np.array([0.0, 0.0]) #  at zero, user defined pressure
        self.shearR = np.array([0.0, 0.0]) #  at zero, user defined pressure
        self.ptoecV = np.array([0.0, 0.0, 0.0]) # polycrystalline C123, C144, C456
        self.ptoecR = np.array([0.0, 0.0, 0.0]) # polycrystalline C123, C144, C456     
        self.help1 = np.matrix([self.c[0],self.c[-1]]) # TOEC at zero and user defined pressure
        self.help2 = np.matrix([self.res[0], self.res[-1]]) # Elastic compliances at zero and user defined pressure
        A= self.anisotropy[0]
        
        for i in range (0,2):
            self.shearV[i] = (self.help1[i,0]-self.help1[i,1]+3*self.help1[i,2])/5
            self.shearR[i] = 5/(4*(self.help2[i,0]-self.help2[i,1])+3*self.help2[i,2])
        # order of constants in self.constants C11, C12 C44, C111,C112, C123, C144, C166, C456  
        self.ptoecV[0] = (self.constants[3]+18*self.constants[4]+16*self.constants[5]-30*self.constants[6]-12*self.constants[7]+16*self.constants[8])/35    
        self.ptoecV[1] = (self.constants[3]+4*self.constants[4]-5*self.constants[5]+19*self.constants[6]+2*self.constants[7]-12*self.constants[8])/35
        self.ptoecV[2] = (self.constants[3]-3*self.constants[4]+2*self.constants[5]-9*self.constants[6]+9*self.constants[7]+9*self.constants[8])/35

        self.ptoecR[2] = (((5*A/(2*A+3))**3)/35)*(self.constants[3]-3*self.constants[4]+2*self.constants[5]-(9/(A**2)*(self.constants[6]-self.constants[7]))+(9/(A**3)*self.constants[8]))
        self.ptoecR[1] = (A/(2*A+3)*(self.constants[3]-self.constants[5]+3/A*(self.constants[6]+2*self.constants[7])-4*self.ptoecR[2]))/3
        self.ptoecR[0] = (9*self.ptoecV[0]+18*self.ptoecV[1]+8*self.ptoecV[2]-18*self.ptoecR[1]-8*self.ptoecR[2])/9
        
    def plotdata(self):
        """
        This method creates an arrays of x,y,z coordinates for every direction in 3D.
        The data is returned in a format suitable for plotting with plot_surface which is
        a 2D array of number of iteration in each dimension.
        Three sets of data is prepared:
        Young moduli as a function of direction at zero pressure
        The difference in Young moduli as a function of direction between zero and user defined pressure. 
        The normalized difference in Young moduli as a function of direction between zero and user defined pressure.
            The difference is normalized by the value of Young at zero pressure in that direction
        """
        self.compl = np.array([self.res[0], self.res[-1]]) # Take the needed values of compliances from previous results
        
        k=0 # Calculate the value of Young moduli for given theta and phi for both pressures.
        # The k integer distinguish between values at zero pressure and user pressure (stored to data2)
        for data in self.compl:
            i=0
            self.constant = 2*(data[0]-data[1]-0.5*data[2])
            for theta in self.theta:
                for phi in self.phi:
                    cosA = math.sin(phi)*math.cos(theta)
                    cosC = math.cos(phi)
                    self.cosines = ((1-cosA**2)*(cosA**2+cosC**2)-cosC**4)
                    Young = 1/(data[0]-(self.cosines*self.constant))
                    if k==0:
                        self.data[i] = [theta,phi,Young]
                    if k==1:
                        self.data2[i] = [theta, phi, Young]
                    i+= 1
            k=1
            
        # The r (radius) of the plot is the Young moduli    
        i=0 
        j=0 # Converts spherical coordinates to cartesian for the zero pressure
        for value in self.data:
           
            self.x1[j,i] = float(value[2]*math.cos(value[0])*math.sin(value[1]))
            self.y1[j,i] = float(value[2]*math.sin(value[0])*math.sin(value[1]))
            self.z1[j,i] = float(value[2]*math.cos(value[1]))
            self.r1[j,i] = float(value[2])
            i+=1
            if i==self.iteration:
                i=0
                j+=1
                
        i=0
        j=0 # Converts spherical coordinates to cartesian for the user pressure
        for value in self.data2:
           
            self.x2[j,i] = float(value[2]*math.cos(value[0])*math.sin(value[1]))
            self.y2[j,i] = float(value[2]*math.sin(value[0])*math.sin(value[1]))
            self.z2[j,i] = float(value[2]*math.cos(value[1]))
            self.r2[j,i] = float(value[2])
            i+=1
            if i==self.iteration:
                i=0
                j+=1
                
        # Calculates the difference of Young moduli which is what we are interested in.        
        self.difr = (self.r2-self.r1)
                
        # The difference is stored in a simple 1D list insted of a 2D array.
        # This is so that each value can be easier to call with an increasing integer in next part of the code
        difflist = list() 
        for value in self.difr:
            for another in value:
                difflist.append(another)
       
        
        # It is important to note, that x1-x2 doesn't work and deltax must be calculated from deltar
        
        i=0
        j=0 
        k=0 # Converts spherical coordinates to cartesian for the difference in Young moduli
        for value in self.data:
           
            self.difx[j,i] = float(difflist[k]*math.cos(value[0])*math.sin(value[1]))
            self.dify[j,i] = float(difflist[k]*math.sin(value[0])*math.sin(value[1]))
            self.difz[j,i] = float(difflist[k]*math.cos(value[1]))
            i+=1
            k+=1
            if i==self.iteration:
                i=0
                j+=1
                
              
        self.rnorm = np.divide(self.difr, self.r1)*100 # Change to percentages
        # Again a list of normalized radii is created
        normlist = list()
        for value in self.rnorm:
            for another in value:
                normlist.append(another)                
        i=0
        j=0
        k=0# Converts spherical coordinates to cartesian
        for value in self.data:
           
            self.xnorm[j,i] = float(normlist[k]*math.cos(value[0])*math.sin(value[1]))
            self.ynorm[j,i] = float(normlist[k]*math.sin(value[0])*math.sin(value[1]))
            self.znorm[j,i] = float(normlist[k]*math.cos(value[1]))
            self.rnorm[j,i] = float(normlist[k])
            k+=1
            i+=1
            if i==self.iteration:
                i=0
                j+=1
             

    def plot(self):  
        """
        This method takes the data prepared by plotdata method and plots it in 3D
        The value of Young moduli (or the difference in other plots) is shown by the colour 
        and the relative magnitude of the vector in that direction. 
        A colourbar is present to provide numerical data to each colour.
        3 Graphs are being plotted at the moment:
        The young moduli as a function of direction at zero pressure.
        The difference in Young moduli as a function of direction between zero and user defined pressure. 
        The normalized difference in Young moduli as a function of direction between zero and user defined pressure.
        The difference is normalized by the value of Young at zero pressure in that direction
        """
        # Plot of difference in Young moduli
        # Prepares the colour scheme to show the value of r not z     
        minim, maxim = self.difr.min(), self.difr.max()
        norm = matplotlib.colors.Normalize(minim, maxim)
        m = plt.cm.ScalarMappable(norm=norm, cmap='jet')     
        m.set_array(self.difr)
        fcolors = m.to_rgba(self.difr)
        
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title("The difference in Young moduli") 
        ax.plot_surface(self.difx, self.dify, self.difz, rstride=2, cstride=2,  facecolors=fcolors)
        cb = fig.colorbar(m)
        cb.ax.set_ylabel('Young moduli in GPa', rotation=270, labelpad=25)
        ax.set_xlabel('[100]')
        ax.set_ylabel('[010]')
        ax.set_zlabel('[001]')
        
        graphname = os.path.join(self.outpath, "Difference in E.png")
        plt.savefig(graphname)
        
        
        # Young moduli for zero pressure 
        minim, maxim = self.r1.min(), self.r1.max()
        norm = matplotlib.colors.Normalize(minim, maxim)
        n = plt.cm.ScalarMappable(norm=norm, cmap='jet')     
        n.set_array(self.r1)
        fcolors = n.to_rgba(self.r1)
        
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title("The Young moduli at zero pressure") 
        ax.plot_surface(self.x1, self.y1, self.z1, rstride=2, cstride=2,  facecolors=fcolors)
        cb = fig.colorbar(n)
        cb.ax.set_ylabel('Young moduli in GPa', rotation=270, labelpad=25)
        ax.set_xlabel('[100]')
        ax.set_ylabel('[010]')
        ax.set_zlabel('[001]')
        graphname = os.path.join(self.outpath, "Young moduli.png")
        plt.savefig(graphname)
        
        # Normalized difference in young moduli
        minim, maxim = self.rnorm.min(), self.rnorm.max()
        norm = matplotlib.colors.Normalize(minim, maxim)
        o = plt.cm.ScalarMappable(norm=norm, cmap='jet')     
        o.set_array(self.rnorm)
        fcolors = o.to_rgba(self.rnorm)
        
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.set_title("The normalised difference in young moduli") 
        ax.plot_surface(self.xnorm, self.ynorm, self.znorm, rstride=2, cstride=2,  facecolors=fcolors)
        cb = fig.colorbar(o)
        cb.ax.set_ylabel('Percentage change in Young moduli', rotation=270, labelpad=25)
        ax.set_xlabel('[100]')
        ax.set_ylabel('[010]')
        ax.set_zlabel('[001]')
        graphname = os.path.join(self.outpath, "Normalized difference in E.png")
        plt.savefig(graphname)
       
               
    def store(self):
        """This method stores data into user-specified file. The stored data is:
        Elastic compliances [S11, S12, S44] for no and the user defined pressure ( S in units of inverse GPa).
        Directional Young moduli in the direction 100, 110, 111 for no and user defined pressure (Young m. in GPa).
        Second order el. constants for no and user defined pressure (SOEC are in GPA)
        The anisotropy at zero and user defined pressure.
        Polycrystalline shear for zero and user definied pressure, calculated using both Voigt and Reuss method. (shear in GPa)
        Polycrystalline TOECs calculated for zero pressure using Voigt and Reuss method (in GPa)"""
        
        values = np.array([self.res[0],self.res[-1], self.E[0], self.E[-1], self.c[0], self.c[-1],np.array(self.anisotropy[0]), np.array(self.anisotropy[-1]), self.shearV, self.shearR, self.ptoecV, self.ptoecR ])
        texts = np.array([" # These are the elastic compliances with no pressure applied [S11, S12, S44]", " # These are the elastic compliances with %s GPa pressure applied [S11, S12, S44]\n" %self.pressure,\
            " # These are the directional Young's moduli with no pressure applied [E100, E110, E111]"," # These are the directional Young's moduli with %s GPA pressure applied [E100, E110, E111]\n" %self.pressure,\
            " # These are the SOEC with no pressure applied [C11, C12, C44]"," # These are the SOEC with %s GPA pressure applied [C11, C12, C44]\n" %self.pressure,\
            " # The anisotropy at zero pressure.", " # The anisotropy at %s GPa pressure.\n"%self.pressure,\
            " # These are the values of polycrystalline shear obtained through Voigt approach in GPa for zero and %s pressure" %self.pressure,\
            " # These are the values of polycrystalline shear obtained through Reuss approach in GPa for zero and %s pressure\n" %self.pressure,\
            " # These are the polycrystalline TOECS calculated using Voigt method at zero pressure, in the following order: C123, C144, C456",\
            " # These are the polycrystalline TOECS calculated using Reuss method at zero pressure, in the following order: C123, C144, C456\n"])
        
        self.completeoutput = os.path.join(self.outpath, "Additional Data.txt")
        f = open(self.completeoutput, 'w')
        i=0
        for something in values:            
            f.write(str(something))
            f.write(str(texts[i]))
            f.write("\n")
            i+=1
            
                    
    def process(self):
        """This method is responsible for calling the necessary methods in the correct order."""
        self.pres()
        self.young()
        self.polycrystal()
        self.store()
        self.plotdata()
        self.plot()
        

class Integration:
    
    def __init__(self, constants=[182.41807108,124.3300311,78.9430471,-1186.16805267,-712.50051294,-34.9259258,48.51582668,-598.67383185,70.35896528], pressure=1, steps=1000):
        
        pressurechange = pressure # in GPa
        # c11 c12 c44 c111 c112 c123 c144 c166 c456
        self.x=constants
        self.y0=[self.x[0] , self.x[1], self.x[2]] #y = c11 c12 c44
        self.steps = int(steps)
        self.P=np.linspace(0,pressurechange,self.steps)
    
    def f(self, y,P):
        c11 = y[0]
        c12 = y[1]
        c44 = y[2]
        dc11dP = -(2*self.x[4]+self.x[3]+2*c12+2*c11)/(2*c12+c11)
        dc12dP = -(self.x[5]+2*self.x[4]-c12-c11)/(2*c12+c11)
        dc44dP = -(2*self.x[7]+self.x[6]+c44+2*c12+c11)/(2*c12+c11)
        return [dc11dP, dc12dP, dc44dP]
        
    def solve(self):
        self.solution = odeint(self.f,self.y0, self.P)

        return self.solution
        
a = Main()
