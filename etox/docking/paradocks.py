# -*- coding: utf-8 -*-

"""
This file contains all the PARADOCKS methods for etoxsys.
"""

import os
import textwrap
import shutil
import glob

from eTOX_ALLIES.etox.core.molHandler import mols2single
from .. import settings

PARADOCKS = settings.get('PARADOCKS')
CMD = [PARADOCKS, 'paradocks.conf']
INPUTFMT='mol2'

def prepareDocking(liglist,proteinf,settings):
    '''This function sets up docking with PLANTS so that CMD can be executed by the script.
       Requires the protein for docking as separate input. The other arguments should be named and are passed to Conf().'''
    outFile=mols2single(liglist,output='molecule',format='mol2')
    settings['customset']['ligand']=os.path.basename(outFile)
    settings['customset']['radius']=int(settings['customset']['radius'])
    settings['customset']['lleft']=[x+4-settings['customset']['radius'] for x in settings['customset']['pocket']]
    settings['customset']['uright']=[x-4+settings['customset']['radius'] for x in settings['customset']['pocket']]
    inputf = open('paradocks.conf','w')
    conf = Conf(**settings)
    inputf.write(conf.mode('custom'))
    inputf.close()
    shutil.copy(proteinf,  '.')
    return


def solveDocking():
    '''This function handles the docking solutions generated by the script.
     It should return a list of the filenames that will be analyzed, filtered and clustered'''
    solutions=glob.glob('*paradocks_prot1_*.mol2')  #all plants solutions are retrieved in a list
    return solutions

class Conf:
    '''Defines a PARADOCKS configuration file
     Its possible to initialize with a custom dictionary, 
     or modify elements later with setCustom()'''
    def __init__(self,customset=None):
        '''Sets up a paradocks configuration file as a string. Sets up dicts with presets'''
        self.text=textwrap.dedent('''
        <?xml version="1.0" encoding="utf-8"?>
        <ParaDockS application="DOCKING">
        	<OptimizerConfiguration type="PSO">
        		<Iterations>100</Iterations>
        		<Particles>20</Particles>
        		<InertiaStart>1</InertiaStart>
        		<InertiaEnd>0.2</InertiaEnd>
        		<CognitiveWeight>1</CognitiveWeight>
        		<SocialWeight>3.4</SocialWeight>
        		<RandomSeed>0</RandomSeed>
        	</OptimizerConfiguration>
        	<ScoringFunction>
        		<FitnessFunctionConfiguration type="pScore">
        			<Group id="0" type="pScore"/>
        			<FitnessTermConfiguration type="pScore_HBond" scale="0.1" group="0">
        				<HBFactor>-14.5847</HBFactor>
        				<HBDistance>0.910731</HBDistance>
        				<HBAngle>3.1</HBAngle>
        				<HBCutoff>4.7</HBCutoff>
        			</FitnessTermConfiguration>
        			<FitnessTermConfiguration type="pScore_vdw" scale="0.1" group="0">
        				<Cutoff>8</Cutoff>
        				<DefaultGridSpacing>0.2</DefaultGridSpacing>
        				<UpperScoreLimit>15</UpperScoreLimit>
        				<LowerScoreLimit>-2e+20</LowerScoreLimit>
        			</FitnessTermConfiguration>
        			<FitnessTermConfiguration type="pScore_ivdw" scale="0.1" group="0">
        				<NumberOfBondsBetween>4</NumberOfBondsBetween>
        				<VDWCutoff>4</VDWCutoff>
        				<PenaltyCutoff>15</PenaltyCutoff>
        			</FitnessTermConfiguration>
        		</FitnessFunctionConfiguration>
        	</ScoringFunction>
        	<RescoringFunction/>
        	<DockingDataSet>
        		<ProteinDefinition>
        			<Name>protein</Name>
        			<File>{0[proteinDock]}</File>
        			<ActiveSiteDefinition>
        				<Center x="{0[pocket][0]}" y="{0[pocket][1]}" z="{0[pocket][2]}"/>
        				<Radius>{0[radius]}</Radius>
        				<LowerLeftCorner x="{0[lleft][0]}" y="{0[lleft][1]}" z="{0[lleft][2]}"/>
        				<UpperRightCorner x="{0[uright][0]}" y="{0[uright][1]}" z="{0[uright][2]}"/>
        			</ActiveSiteDefinition>
        		</ProteinDefinition>
        		<LigandDefinition>
        			<Name>Ligand</Name>
        			<File>{0[ligand]}</File>
        			<Range startIdx="0" endIdx="5"/>
        			<DockingRuns>50</DockingRuns>
        		</LigandDefinition>
        	</DockingDataSet>
        	<OutputConfiguration>
        		<VerbosityLevel>debug</VerbosityLevel>
        		<OutputPath>.</OutputPath>
        		<Prefix>./paradocks</Prefix>
        		<Suffix/>
        		<FileType>MOL2</FileType>
        		<NumSolutions>0</NumSolutions>
        	</OutputConfiguration>
        </ParaDockS>''').strip('\n')
    
        #Set default dictionary
        self.defaults=dict(proteinDock='protein.mol2',
        ligand='molecule.mol2',
        pocket=[0.0,0.0,0.0],
        lleft=[0.0,0.0,0.0],
        uright=[0.0,0.0,0.0],
        radius=12
        )
        #custom is a copy of the defaults unless modified by user
        self.customset=self.defaults.copy()
        if customset is not None:
            self.customset.update(customset)
    
        self.presets = {'default':  self.defaults,
              'custom'  :  self.customset
              }

    def setText(self,txt):
        '''Allows user to change the default configuration string'''
        self.text=str(txt)
    
    def getText(self):
        '''Allows user to retrieve current configuration string'''
        return self.text
   
    def setCustom(self,**kwargs):
        '''User can set the individual values in the custom preset to whatever is desired
             use key= and value= to change one value.
             Its also possible to change the entire list to one predefined preset with preset='''
        if 'preset' in kwargs and len(kwargs) == 1:
            if kwargs['preset'] in self.presets:
                self.customset.update(self.presets.get(kwargs['preset']))
            else:
                raise Exception, 'Use preset=, or key= and val= as arguments!'
        elif 'key' in kwargs and 'val' in kwargs and len(kwargs) == 2:            
            self.customset[kwargs['key']]=kwargs['val']
        else:            
            raise Exception, 'Use preset=, or key= and val= as arguments!'
   
    def mode(self,preset):
        '''Returns formatted Gold configuration file with values set to preset requested.'''
        if preset in self.presets:
            return self.text.format(self.presets[preset])
        else:
            raise Exception, 'Unknown preset!'