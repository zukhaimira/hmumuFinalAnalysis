#! /usr/bin/env python

from ROOT import gSystem

import singleHelpers
import datetime
import sys
import os
import re
import math
import cPickle
import ROOT as root
root.gSystem.Load('libRooFit')
root.gROOT.SetBatch(True)
import scipy.stats

from multiprocessing import Pool
import itertools
from itertools import repeat as itrRepeat

from helpers import *
from makeCards import *
from xsec import *
from fitOrderChooser import makePDFBakSumExp,makePDFBakBernstein

from numpy import mean, median, corrcoef, percentile
from numpy import std as stddev

#root.gErrorIgnoreLevel = root.kWarning
#root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.WARNING)
root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.ERROR)
PRINTLEVEL = root.RooFit.PrintLevel(-1) #For MINUIT
#PRINTLEVEL = root.RooFit.PrintLevel(1) #For MINUIT


#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################
#########################################################################

class PlotBgkFits:
  def __init__(self,catName,energyStr,dataFileNames,outPrefix,pdfsToTry):
    catName = catName[0]
    randomGenerator = root.RooRandom.randomGenerator()
    randomGenerator.SetSeed(10001)
    dataTree = root.TChain()
    for i in dataFileNames:
      dataTree.Add(i+"/outtree"+catName)
    dataTree.SetCacheSize(10000000);
    dataTree.AddBranchToCache("*");

    dimuonMass = root.RooRealVar("dimuonMass","M(#mu#mu) [GeV/c^{2}]",110.,160.)
    dimuonMass.setRange("low",110,120) # Silly ranges for old fit functionality
    dimuonMass.setRange("high",130,160)
    dimuonMass.setRange("signal",120,130)
    dimuonMass.setRange("signalfit",110,140)
    dimuonMass.setBins(50)

    # Hack to Make makePDFBakOld work
    minMassZ = 88.
    maxMassZ = 94.
    dimuonMassZ = root.RooRealVar("dimuonMass","dimuonMass",minMassZ,maxMassZ)

    ### Load data
    realData = root.RooDataSet("realData"+catName+energyStr,
                                    "realData"+catName+energyStr,
                                        dataTree,root.RooArgSet(dimuonMass)
                                      )
    nData = realData.sumEntries()
    realDataHist = realData.binnedClone()

    realDataZ = root.RooDataSet("realDataZ"+catName+energyStr,
                                    "realDataZ"+catName+energyStr,
                                        dataTree,root.RooArgSet(dimuonMassZ)
                                      )


    ### Make Bak Pdfs
    pdfTitles = []
    self.rmpList = []
    self.pdfList = []
    self.frList = []
    self.wList = []
    self.frDebugDict = {}

    self.outStr = "################################################################"
    self.outStr += "\n\n"
    self.outStr += catName + energyStr
    self.outStr += "\n\n"
    self.latexStrDetail = ""
    self.outStrDetail = "##############################################################\n\n"
    self.outStrDetail += catName + energyStr + "\n\n"
    for pdfName in pdfsToTry:
      pdfOrder = None
      pdfBaseName = pdfName
      orderMatch = re.match(r"([\d]+)(.+)",pdfBaseName)
      if orderMatch:
        pdfBaseName = orderMatch.group(2)
        pdfOrder = int(orderMatch.group(1))

      w = root.RooWorkspace("w"+pdfBaseName)
      wImport = getattr(w,"import")
      pdfFunc = globals()["makePDFBak"+pdfBaseName]
      tmpParamList,tmpNormTup,tmpDebug,tmpOrder = pdfFunc(pdfName+catName+energyStr,realData,dimuonMass,110,160,wImport,dimuonMassZ,realDataZ,order=pdfOrder)
      pdf = w.pdf("bak")
      fr = pdf.fitTo(realData, 
                         root.RooFit.Hesse(True), 
                         root.RooFit.Minos(True), # Doesn't Help, just makes it run longer
                         root.RooFit.Save(True),
                         PRINTLEVEL
                       )
      self.frDebugDict[pdfName] = rooDebugFR(fr,resultDict=True)

      #rmp = RooModelPlotter(dimuonMass,pdf,realData,fr,
      #                  TITLEMAP[catName],energyStr,lumiDict[energyStr],
      #                  caption2=PDFTITLEMAP[pdfBaseName]
      #                  )
      #rmp.draw(outPrefix+"_Shape_"+energyStr+catName+"_"+pdfName)
      #rmp.drawWithParams(outPrefix+"_Shape_"+energyStr+catName+"_"+pdfName+"_params")
      floatParsFinal = fr.floatParsFinal()
      self.outStrDetail += "\n{0}\n".format(pdf.GetTitle())
      #self.outStrDetail += tmpDebug + "\n"
      for i in range(floatParsFinal.getSize()):
        parTitle = floatParsFinal.at(i).GetTitle()
        parVal = floatParsFinal.at(i).getVal()
        parErr = floatParsFinal.at(i).getError()
        self.outStrDetail += "  {0:30}: {1:10.3g} +/- {2:10.3g}\n".format(parTitle,parVal,parErr)

      pdf.SetName(pdfName)
      
      #ndfFunc = rooPdfNFreeParams(pdf,realData)

      #chi2Var = pdf.createChi2(realDataHist)
      #chi2 = chi2Var.getVal()
      #ndf = dimuonMass.getBins() - 1  # b/c roofit normalizes
      #ndf -= ndfFunc
      #nll = fr.minNll()
      ##self.outStr+= "{0:15} chi2: {1:.2f} ndf: {2:.0f} nll: {3:.3g}\n".format(pdfName,chi2,ndf,nll)

      #self.rmpList.append(rmp)
      self.pdfList.append(pdf)
      self.frList.append(fr)
      self.wList.append(w)
      pdfTitle = PDFTITLEMAP[pdfBaseName]
      if tmpOrder != None:
        pdfTitle = str(tmpOrder)+"-"+pdfTitle
      pdfTitles.append(pdfTitle)
    
    print "$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$"
    print "About to start RooCompareModels..."

    binWidth = 1
    if "Jet2" in catName or "VBF" in catName:
        binWidth *= 2.5
    elif "BO" in catName:
        binWidth *= 1
    elif "BE" in catName:
        binWidth *= 2.5
    elif "OO" in catName:
        binWidth *= 2.5
    elif "OE" in catName:
        binWidth *= 2.5
    elif "EE" in catName:
        binWidth *= 2.5
    elif "FF" in catName:
        binWidth *= 2.5
    elif "CC" in catName:
        binWidth *= 2.5
    elif "BB" in catName:
        binWidth *= 1

    binning = dimuonMass.getBinning()
    xlow = binning.lowBound()
    xhigh = binning.highBound()
    dimuonMass.setBins(int((xhigh-xlow)/binWidth))

    self.rcm = RooCompareModels(dimuonMass,realData,
                              self.pdfList,self.frList,pdfTitles,
                              TITLEMAP[catName],energyStr,lumiDict[energyStr]
                              )
    self.rcm.draw(outPrefix+"_Comb_"+energyStr+"_"+catName)
    #self.rcm.drawDiff(0,outPrefix+"_Comb_"+energyStr+"_"+catName+"Diff")
    #self.rcm.drawPullHists(outPrefix+"_Comb_"+energyStr+"_"+catName+"Pulls")
    logFile = open(outPrefix+"_GOF_"+energyStr+"_"+catName+".log",'w')
    self.rcm.printGOFTable(logFile)
    self.rcm.printDiffTable(0,logFile)
    logFile.close()
    self.gofData = self.rcm.getGOFData()

  def getGOFData(self):
    return self.gofData
  def getFRData(self):
    return self.frDebugDict

def makeGOFDataTable(gofData,pdfList,energyStr):
  categories = sortCatNames(gofData.keys())
  result = "%% GOF Table for "+energyStr+"\n"
  result += r"\begin{tabular}{|l|"+"c|"*len(pdfList)+r"} \hline"+"\n"
  line = "Category"
  for pdfName in pdfList:
    pdfTitle = PDFTITLEMAP[pdfName]
    if "#" in pdfTitle or "_" in pdfTitle or "^" in pdfTitle:
      pdfTitle = pdfTitle.replace("#","\\")
      pdfTitle = "$\mathrm{"+pdfTitle+"}$"
    line += " & "+pdfTitle
  result += line + r" \\ \hline \hline"+"\n"
  for cat in categories:
    line = "{0:18}".format(TITLEMAP[cat])
    for pdfName in pdfList:
      #line += " & {0:6.1f}/{1}, $\mathrm{{p_{{\chi^2}}}}={2:.3g}$".format(*gofData[cat][pdfName])
      line += " & {0:6.1f}/{1}".format(*gofData[cat][pdfName])
    result += line + r" \\ \hline"+"\n"
  result += r"\end{tabular}"+"\n\n"

  result += "%% GOF Prob Table for "+energyStr+"\n"
  result += r"\begin{tabular}{|l|"+"c|"*len(pdfList)+r"} \hline"+"\n"
  line = "Category"
  for pdfName in pdfList:
    pdfTitle = PDFTITLEMAP[pdfName]
    if "#" in pdfTitle or "_" in pdfTitle or "^" in pdfTitle:
      pdfTitle = pdfTitle.replace("#","\\")
      pdfTitle = "$\mathrm{"+pdfTitle+"}$"
    line += " & "+pdfTitle
  result += line + r" \\ \hline \hline"+"\n"
  for cat in categories:
    line = "{0:18}".format(TITLEMAP[cat])
    for pdfName in pdfList:
      line += " & {2:7.3g}".format(*gofData[cat][pdfName])
    result += line + r" \\ \hline"+"\n"
  result += r"\end{tabular}"+"\n\n"

  return result

def makeFRDataTable(frData,pdfList,energyStr):
  #result[name] = [nuis_s.getVal(),nuis_s.getError(),nuis_s.getErrorLo(),nuis_s.getErrorHi(),nuis_s.getMin(),nuis_s.getMax()]
  #result[name] = const_par.getVal()
  categories = sortCatNames(frData.keys())
  result = ""
  for cat in categories:
    catTitle = TITLEMAP[cat]
    for  pdfName in pdfList:
      pdfTitle = PDFTITLEMAP[pdfName]
      if "#" in pdfTitle or "_" in pdfTitle or "^" in pdfTitle:
        pdfTitle = r"$\mathrm{\mathbf{"+pdfTitle.replace("#","\\")+"}}$"
      result += "%% Fit Parameter Table for "+energyStr+" "+cat+" "+pdfName+"\n"
      result += r"\begin{tabular}{|l|"+"c|"*4+r"} \hline"+"\n"
      result += r"\multicolumn{5}{|c|}{\textbf{"+energyStr.replace("TeV"," TeV ")+catTitle+" "+pdfTitle+r"}} \\ \hline"+"\n"
      result += r"%\multicolumn{5}{|c|}{\textbf{"+energyStr.replace("TeV"," TeV ")+catTitle+" "+pdfName+r"}} \\ \hline"+"\n"
      line = r"& & Symmetric & Asymmetric & "
      result += line + r" \\"+"\n"
      line = r"Parameter & Best Fit & Error & Error & Limits"
      result += line + r" \\ \hline \hline"+"\n"
      varNames = frData[cat][pdfName].keys()
      for varName in varNames:
        line = "{0:18}".format(varName)
        if type(frData[cat][pdfName][varName]) == list:
          line += " & {0:10.3g} & {1:10.3g} & $^{{+{3:.3g}}}_{{{2:.3g}}}$ & [{4},{5}] ".format(*frData[cat][pdfName][varName])
        else:
          line += " & {0:10.3g} & const. & & ".format(frData[cat][pdfName][varName])
        result += line + r" \\ \hline"+"\n"
      result += r"\end{tabular}"+"\n\n"

  return result
        
        
if __name__ == "__main__":
  canvas = root.TCanvas()
  outDir = "output/"

  pdfsToTry = ["MSSM","Bernstein","ExpMOverSq","VoigtPMm2","VoigtPExpMm2","Old","SumExp"]

  categories = []

  jet2PtCuts = " && jetLead_pt > 40. && jetSub_pt > 30. && ptMiss < 40."
  jet01PtCuts = " && !(jetLead_pt > 40. && jetSub_pt > 30. && ptMiss < 40.)"

  categoriesAll = ["BB","BO","BE","OO","OE","EE"]
  #categories += [["Jets01PassPtG10BB",  "dimuonPt>10." +jet01PtCuts]]
  #categories += [["Jets01PassPtG10BO",  "dimuonPt>10." +jet01PtCuts]]
  #categories += [["Jets01PassPtG10BE",  "dimuonPt>10." +jet01PtCuts]]
  #categories += [["Jets01PassPtG10OE",  "dimuonPt>10." +jet01PtCuts]]
  categories += [["Jets01PassPtG10"+x,  "dimuonPt>10." +jet01PtCuts] for x in categoriesAll]
  categories += [["Jets01FailPtG10"+x,"!(dimuonPt>10.)"+jet01PtCuts] for x in categoriesAll]
  categories += [["Jet2CutsVBFPass","deltaEtaJets>3.5 && dijetMass>650."+jet2PtCuts]]
  categories += [["Jet2CutsGFPass","!(deltaEtaJets>3.5 && dijetMass>650.) && (dijetMass>250. && dimuonPt>50.)"+jet2PtCuts]]
  categories += [["Jet2CutsFailVBFGF","!(deltaEtaJets>3.5 && dijetMass>650.) && !(dijetMass>250. && dimuonPt>50.)"+jet2PtCuts]]

  dataDir = getDataStage2Directory()
  #dataDir = "/data/uftrig01b/jhugon/hmumu/analysisV00-01-10/forGPReRecoMuScleFit/"
  #dataDir = "/cms/data/store/user/jhugon/hmumu/stage2/"

  dataFns8TeV = [
    "SingleMuRun2012Av1-22Jan2013",
    "SingleMuRun2012Bv1-22Jan2013",
    "SingleMuRun2012Cv1-22Jan2013",
    "SingleMuRun2012Dv1-22Jan2013",
    ]

  dataFns7TeV = [
    "SingleMuRun2011Av1",
    "SingleMuRun2011Bv1"
    ]
  dataFns7TeV = [dataDir+i+".root" for i in dataFns7TeV]
  dataFns8TeV = [dataDir+i+".root" for i in dataFns8TeV]

  gofLog = open(outDir+"bkgGOF.tex",'w')
  paramLog = open(outDir+"bkgParams.tex",'w')

  bkgFitList = []
  for energy,dataFns in zip(["7TeV","8TeV"],[dataFns7TeV,dataFns8TeV]):
    gofDataCats = {}
    frDataCats = {}
    for category in categories:
      bkgFits = PlotBgkFits(category,energy,dataFns,outDir+"bkgFits",pdfsToTry)
      bkgFitList.append(bkgFits)
      gofDataCats[category[0]] = bkgFits.getGOFData()
      frDataCats[category[0]] = bkgFits.getFRData()
    gofLog.write(makeGOFDataTable(gofDataCats,pdfsToTry,energy))
    paramLog.write(makeFRDataTable(frDataCats,pdfsToTry,energy))
  gofLog.close()
  paramLog.close()
