#! /usr/bin/env python

from ROOT import gSystem

import sys
import os
import re
import math
from ROOT import *
gSystem.Load('libRooFit')
import ROOT as root

from helpers import *

#root.gErrorIgnoreLevel = root.kWarning
#root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.WARNING)
#root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.ERROR)
PRINTLEVEL = root.RooFit.PrintLevel(-1) #For MINUIT
#PRINTLEVEL = root.RooFit.PrintLevel(1) #For MINUIT


# ------------------------------------------------------------------------------

def Usage():
   print 'Wrong syntax: \n'
   print '   ./extractRooFitSignalDG.py [process] [mass] [benergy (7TeV,8TeV)]\n'
   print 'first is included, last IS NOT included'
   sys.exit()
    
# ------------------------------------------------------------------------------

# ====================   
# set useful variables
if (len(sys.argv) < 4):
   Usage()

# default values
process = sys.argv[1]
mass    = sys.argv[2]
benergy = sys.argv[3]

#inputfile  = "/afs/cern.ch/work/d/digiovan/HToMM/officialMC/submit%s/root/" % benergy
inputfile  = "/afs/cern.ch/work/d/digiovan/HToMM/baselinePP/submit%s/root/" % benergy
inputfile += "%sHmumu%s_%s.root" % (process,mass,benergy)

if (process == 'GluGlu'):
   process = 'gg'
if (process == 'VBF'):
   process = 'vbf'
   
outputfile = 'fitresults/fitresults_%sHmumu%s_%s' % (process,mass,benergy)
savefile   = 'fitresults/png/fitresults_%sHmumu%s_%s' % (process,mass,benergy)

print 'PROCESS: %s' % process
print 'MASS: %s' % mass
print 'BENERGY: %s' % benergy
print 'inputfile: %s' % inputfile
print 'outputfile: %s' % outputfile
print 'savefile: %s' % savefile
print '----------------------------------------------------------------------\n'
# ====================


# define the dimuon mass variable
#minMass = 110.
#maxMass = 135.
minMass = float(mass.replace("p","."))-10.0
maxMass = float(mass.replace("p","."))+10.0
mMuMu = root.RooRealVar("mMuMu","M(#mu#mu) [GeV/c^{2}]",minMass,maxMass)


#####################################################################
# define the Double Gaussian
meanG1 = root.RooRealVar("MeanG1","MeanG1", float(mass.replace("p",".")), float(mass.replace("p","."))-10, float(mass.replace("p","."))+3 )
meanG2 = root.RooRealVar("MeanG2","MeanG2", float(mass.replace("p",".")), float(mass.replace("p","."))-3,  float(mass.replace("p","."))+3 )
 
widthG1 = root.RooRealVar("WidthG1","WidthG1", 7.049779267, 0.0,50.0)
widthG2 = root.RooRealVar("WidthG2","WidthG2", 1.830513636, 0.0, 4.0)
 
#mixGG = root.RooRealVar("mixGG","mixGG", 0.1140210709, 0.0,0.5)
mixGG = root.RooRealVar("mixGG","mixGG", 0.1140210709, 0.0,1.0)

gaus1 = root.RooGaussian("gaus1","gaus1",mMuMu,meanG1,widthG1)
gaus2 = root.RooGaussian("gaus2","gaus2",mMuMu,meanG2,widthG2)
 
pdfMmumuGG = root.RooAddPdf("pdfMmumuGG","pdfMmumuGG",gaus1,gaus2,mixGG)


# define the Single Gaussian for the EE category
meanSG  = root.RooRealVar("MeanSG", "MeanSG", float(mass.replace("p",".")),110.,140.)
widthSG = root.RooRealVar("WidthSG","WidthSG", 1.839226054,0.1,20.0)
 
pdfMmumuSG = root.RooGaussian("sgaus","sgaus",mMuMu,meanSG,widthSG)

#####################################################################


def doFit(f,baseName,benergy,canvas,outputfile,saveName):
 
  widthG1.setVal(7.049779267)
  widthG2.setVal(1.830513636)
  mixGG  .setVal(0.01140210709)

  mDiMu = f.Get( baseName + "/mDiMu")

  #if ("EE" in baseName):
  #   mDiMu.Rebin(4)
  
  mMuMuRooDataHist = root.RooDataHist("template","template",root.RooArgList(mMuMu),mDiMu)

  pdfMmumu = None
#  if (baseName == "IncPreselPtG10EE"):
#    pdfMmumu = pdfMmumuSG
#  else:
  pdfMmumu = pdfMmumuGG
    

    
  pdfMmumu.fitTo(mMuMuRooDataHist,root.RooFit.SumW2Error(False),PRINTLEVEL)
  
  canvas.cd()
  #canvas.SetLogy()
  
  plotMmumu = mMuMu.frame(minMass,maxMass)
  
  mMuMuRooDataHist.plotOn(plotMmumu)
  
  pdfMmumu .plotOn(plotMmumu,root.RooFit.LineColor(root.kAzure+2))

  title = ''
  if (baseName == "Jets01PassPtG10BB"):
     title = "Non-VBF Presel. Tight, Barrel - Barrel (%s)" % benergy
  if (baseName == "Jets01PassPtG10BO"):
     title = "Non-VBF Presel. Tight, Barrel - Overlap (%s)" % benergy
  if (baseName == "Jets01PassPtG10BE"):
     title = "Non-VBF Presel. Tight, Barrel - Endcap (%s)" % benergy
  if (baseName == "Jets01PassPtG10OO"):
     title = "Non-VBF Presel. Tight, Overlap - Overlap (%s)" % benergy
  if (baseName == "Jets01PassPtG10OE"):
     title = "Non-VBF Presel. Tight, Overlap - Endcap (%s)" % benergy
  if (baseName == "Jets01PassPtG10EE"):
     title = "Non-VBF Presel. Tight, Endcap - Endcap (%s)" % benergy
      
  if (baseName == "Jets01FailPtG10BB"):
     title = "Non-VBF Presel. Loose, Barrel - Barrel (%s)" % benergy
  if (baseName == "Jets01FailPtG10BO"):
     title = "Non-VBF Presel. Loose, Barrel - Overlap (%s)" % benergy
  if (baseName == "Jets01FailPtG10BE"):
     title = "Non-VBF Presel. Loose, Barrel - Endcap (%s)" % benergy
  if (baseName == "Jets01FailPtG10OO"):
     title = "Non-VBF Presel. Loose, Overlap - Overlap (%s)" % benergy
  if (baseName == "Jets01FailPtG10OE"):
     title = "Non-VBF Presel. Loose, Overlap - Endcap (%s)" % benergy
  if (baseName == "Jets01FailPtG10EE"):
     title = "Non-VBF Presel. Loose, Endcap - Endcap (%s)" % benergy
  if (baseName == "Jets01FailPtG10CC"):
     title = "Non-VBF Presel. Loose, BE+OO (%s)" % benergy
  if (baseName == "Jets01FailPtG10FF"):
     title = "Non-VBF Presel. Loose, OE+EE (%s)" % benergy
  
  if (baseName == "Jet2CutsVBFPass"):
     title = "VBF Presel, VBF Tight (%s)" % benergy
  if (baseName == "Jet2CutsGFPass"):
     title = "VBF Presel, GF Tight (%s)" % benergy
  if (baseName == "Jet2CutsFailVBFGF"):
     title = "VBF Presel, Loose (%s)" % benergy

  plotMmumu.SetTitle(title)

  #plotMmumu.SetTitle(baseName)
  #if ('hists' in baseName):
  #   plotMmumu.SetTitle(baseName[5:])
     
  plotMmumu.Draw()

##  chi2ondf =  plotMmumu.chiSquare()
##  tlatex = root.TLatex()
##  tlatex.SetNDC()
##  tlatex.SetTextFont(root.gStyle.GetLabelFont())
##  tlatex.SetTextSize(0.05)
##  tlatex.SetTextAlign(22)
##  tlatex.DrawLatex(0.75,0.85,"#chi^{{2}}/NDF = {0:.2f}".format(chi2ondf))

  canvas.Update()
  if saveName != "":
     canvas.SaveAs(saveName+'.png')
     canvas.SaveAs(saveName+'.pdf')
     canvas.SaveAs(saveName+'.root')
 
  outfile = open(outputfile+'_DG','w')
          
  print ''
  print ''
#  if (baseName == "IncPreselPtG10EE"):
#    print 'Single Gaussian'
#    for i in [meanSG,widthSG]:
#      print("{0}: {1:.10g}".format(i.GetName(),i.getVal()))
#      
#    outfile.write('#process mass meanSG err widthSG err\n')
#    outfile.write('%s %s %s %s %s %s\n' % (process,mass,
#                                           meanSG.getVal() , meanSG.getError(), 
#                                           widthSG.getVal(), widthSG.getError()
#                                           )
#                  )
#  else:
  print 'Double Gaussian'
  for i in [meanG1,meanG2,widthG1,widthG2,mixGG]:
     print("{0}: {1:.10g}".format(i.GetName(),i.getVal()))

  mean_narrow      = meanG2.getVal()
  err_mean_narrow  = meanG2.getError()
  width_narrow     = widthG2.getVal()
  err_width_narrow = widthG2.getError()

  mean_wide        = meanG1.getVal()
  err_mean_wide    = meanG1.getError()
  width_wide       = widthG1.getVal()
  err_width_wide   = widthG1.getError()

  mixing           = mixGG.getVal()
  err_mixing       = mixGG.getError()

  if (widthG1.getVal()<widthG2.getVal()):

     mean_narrow      = meanG1.getVal()
     err_mean_narrow  = meanG1.getError()
     width_narrow     = widthG1.getVal()
     err_width_narrow = widthG1.getError()

     mean_wide        = meanG2.getVal()
     err_mean_wide    = meanG2.getError()
     width_wide       = widthG2.getVal()
     err_width_wide   = widthG2.getError()

     mixing           = (1-mixGG.getVal())
     err_mixing       = mixGG.getError()
     
     
  outfile.write('#process mass meanG1 err widthG1 err meanG2 err widthG2 err mixGG err\n')  
  outfile.write('%s %s %s %s %s %s %s %s %s %s %s %s\n'
                % (process,mass.replace("p","."),
                   mean_narrow,  err_mean_narrow,
                   width_narrow, err_width_narrow,
                   mean_wide,    err_mean_wide,
                   width_wide,   err_width_wide,
                   mixing,       err_mixing
                   )
                ) 

  # calculate the FWHM
  #bin1 = mDiMu.FindFirstBinAbove(mDiMu.GetMaximum()/2)
  #bin2 = mDiMu.FindLastBinAbove (mDiMu.GetMaximum()/2)
  #print mDiMu.GetBinCenter(bin2), mDiMu.GetBinCenter(bin1)
  #fwhm = float (mDiMu.GetBinCenter(bin2) - mDiMu.GetBinCenter(bin1));
  #print fwhm
  #
  #print width_narrow
  #print 2.35482*width_narrow

  print "latex %s & %s & %s & %s \\\\" % (title, width_narrow, 2.35482*width_narrow, calcFWHM(pdfMmumu,mMuMu,115,135,0.01))
  print "latex \\\\hline" 

   
  #outfile.write('%s %s %s %s %s %s %s %s %s %s %s %s\n'
  #              % (process,mass.replace("p","."),
  #                 meanG1.getVal(),  meanG1.getError(), 
  #                 widthG1.getVal(), widthG1.getError(),
  #                 meanG2.getVal(),  meanG2.getError(),
  #                 widthG2.getVal(), widthG2.getError(),
  #                 mixGG.getVal(),   mixGG.getError()
  #                 )
  #              ) 

  
#####################################################################

f = root.TFile(inputfile)

# baseline
#baseNamesGG = ["IncPreselPtG10BB",
#               "IncPreselPtG10BO",
#               "IncPreselPtG10BE",
#               "IncPreselPtG10OO",
#               "IncPreselPtG10OE",
#               "IncPreselPtG10EE"
#               ]
#
#baseNamesVBF = ["VBFBDTCut",
#                "histsVBFDeJJG3p5MJJG550pTmissL100",
#                "histsVBFDeJJG3p4MJJG500pTmissL25"
#                ]
            
# baseline++

baseNamesGG = ["Jets01PassPtG10BB",
               "Jets01PassPtG10BO",
               "Jets01PassPtG10BE",
               "Jets01PassPtG10OO",
               "Jets01PassPtG10OE",
               "Jets01PassPtG10EE",
               
               "Jets01FailPtG10BB",
               "Jets01FailPtG10BO",
               "Jets01FailPtG10BE",
               "Jets01FailPtG10OO",
               "Jets01FailPtG10OE",
               "Jets01FailPtG10EE",               
               ]

baseNamesVBF = ["Jet2CutsVBFPass",  
                "Jet2CutsGFPass",   
                "Jet2CutsFailVBFGF"
                ]

baseNames = None
if ("GluGluHmumu" in f.GetName()):
  baseNames = baseNamesGG
if ("VBFHmumu" in f.GetName()):
  baseNames = baseNamesVBF

if (baseNames == None):
  print "ERROR: The input file is not ggH or vbfH"
  sys.exit()

  
canvases = []

iStep = 0
for baseName in baseNames:
  canvas = root.TCanvas("canvas_%s" % baseName,"",iStep,iStep,800,600)
  canvases.append( canvas )
  iStep += 100
  
for id in range(0,len(baseNames)):
   if ('hists' in baseNames[id]):
      doFit(f,baseNames[id],benergy,canvases[id],outputfile+'_'+baseNames[id][5:],savefile+'_'+baseNames[id][5:])
   else:
      doFit(f,baseNames[id],benergy,canvases[id],outputfile+'_'+baseNames[id],savefile+'_'+baseNames[id])
