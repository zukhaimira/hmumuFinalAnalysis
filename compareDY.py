#!/usr/bin/env python

from xsec import *
from helpers import *
import ROOT as root
import os
import sys

dataDir = "input/"
outDir = "output/"

RUNPERIOD="8TeV"
LUMI=lumiDict[RUNPERIOD]

LOGY=False
integralPlot=False

backgroundList = [
#"DYToMuMu",
#"DYJetsToLL",
#"WJetsToLNu",
"ttbar",
"WW",
"WZ",
"ZZ"
#"QCD"
]

dyList = [
 "DYToMuMu", "DYJetsToLL"
]
dyLegendEntries = {"DYToMuMu":"DY Powheg","DYJetsToLL":"DY Madgraph"}

urLegendPos = [0.70,0.67,0.9,0.9]
ulLegendPos = [0.20,0.67,0.4,0.9]
ucLegendPos = [0.46,0.67,0.64,0.9]
lcLegendPos = [0.46,0.35,0.64,0.63]
ccLegendPos = [0.46,0.47,0.64,0.7]
stdLegendPos = urLegendPos

#histDirs = ["","4GeVWindow/","PtDiMu100/","VBFPresel/","IncPresel/","NotBlindWindow/"]
histDirs = [""]
histDirs = ["NotBlindWindow/"]
histDirs = ["VBFPresel/","IncPresel/"]
#histDirs = ["","PtDiMu100/","VBFPresel/","IncPresel/"]

histNames = {}
#histNames["mDiMu"] = {"xlabel":"m_{#mu#mu} [GeV]","xlimits":[110.0,150.0],"rebin":1}
histNames["mDiMu"] = {"xlabel":"m_{#mu#mu} [GeV]","xlimits":[80.0,150.0],"rebin":1}

histNames["ptDiMu"] = {"xlabel":"p_{T,#mu#mu} [GeV]","xlimits":[0.0,200.0],"rebin":5}
#histNames["ptDiJet"] = {"xlabel":"p_{T,jj} [GeV]","xlimits":[0.0,200.0],"rebin":2}

histNames["mDiJet"] = {"xlabel":"m_{jj} [GeV]","xlimits":[0.0,1200.0],"rebin":5}
histNames["mDiJet"] = {"xlabel":"m_{jj} [GeV]","xlimits":[300.0,1200.0],"rebin":5}
histNames["deltaEtaJets"] = {"xlabel":"#Delta#eta_{jj}","xlimits":[0.0,8.5]}
histNames["deltaEtaJets"] = {"xlabel":"#Delta#eta_{jj}","xlimits":[3.0,8.5]}
histNames["deltaRJets"] = {"xlabel":"#DeltaR_{jj}","xlimits":[0.0,8.5]}
histNames["deltaPhiJets"] = {"xlabel":"#Delta#phi_{jj}","xlimits":[0.0,3.2],"rebin":2,"leg":ulLegendPos}
histNames["deltaEtaMuons"] = {"xlabel":"#Delta#eta_{#mu#mu}","xlimits":[0.0,4.5]}
histNames["deltaRMuons"] = {"xlabel":"#DeltaR_{#mu#mu}","xlimits":[0.0,6.0]}
histNames["deltaPhiMuons"] = {"xlabel":"#Delta#phi_{#mu#mu}","xlimits":[0.0,3.2],"rebin":2,"leg":ulLegendPos}

histNames["ptMu1"] = {"xlabel":"Leading Muon p_{T} [GeV]","xlimits":[20.0,200.0]}
histNames["ptMu2"] = {"xlabel":"Sub-Leading Muon p_{T} [GeV]","xlimits":[20.0,200.0]}

histNames["ptJet1"] = {"xlabel":"Leading Jet p_{T} [GeV]","xlimits":[30.0,250.0]}
histNames["ptJet2"] = {"xlabel":"Sub-Leading Jet p_{T} [GeV]","xlimits":[0.0,250.0]}
histNames["ht"] = {"xlabel":"Jet H_{T} [GeV], for Jets p_{T}>30 GeV","xlimits":[0.0,1000.0]}
histNames["htInRapidityGap"] = {"xlabel":"Jet H_{T} in Jet Rapidity Gap [GeV], for Jets p_{T}>30 GeV","xlimits":[0.0,1000.0]}
histNames["nJets"] = {"xlabel":"N_{jets}","xlimits":[0,10]}
histNames["nJetsInRapidityGap"] = {"xlabel":"N_{jets} in Jet Rapidity Gap [GeV]","xlimits":[0,10]}

histNames["etaMu1"] = {"xlabel":"Leading Muon #eta","xlimits":[-2.4,2.4],"rebin":2,"leg":ccLegendPos}
histNames["etaMu2"] = {"xlabel":"Sub-Leading Muon #eta","xlimits":[-2.4,2.4],"rebin":2,"leg":ccLegendPos}

histNames["etaJet1"] = {"xlabel":"Leading Jet #eta","xlimits":[-5.0,5.0],"rebin":2}
histNames["etaJet2"] = {"xlabel":"Sub-Leading Jet #eta","xlimits":[-5.0,5.0],"rebin":2}

histNames["yDiMu"] = {"xlabel":"y_{#mu#mu} [GeV]","xlimits":[-2.2,2.2],"rebin":2,"leg":lcLegendPos}

histNames["cosThetaStar"] = {"xlabel":"cos(#theta^{*})","xlimits":[-1.0,1.0],"rebin":2,"leg":lcLegendPos}
histNames["cosThetaStarCS"] = {"xlabel":"cos(#theta^{*}_{CS})","xlimits":[-1.0,1.0],"rebin":2,"leg":lcLegendPos}

histNames["relIsoMu1"] = {"xlabel":"Leading Muon Relative PF Isolation","xlimits":[0,0.3],"rebin":2}
histNames["relIsoMu2"] = {"xlabel":"Sub-Leading Muon Relative PF Isolation","xlimits":[0,0.3],"rebin":2}

#histNames["likelihoodHistMuonOnly"] = {"xlabel":"Likelihood (Non-VBF Category)","xlimits":[-0.5,0.5],"rebin":2}
histNames["BDTHistMuonOnly"] = {"xlabel":"BDT (Non-VBF Category)","xlimits":[-1,0],"rebin":2}

#histNames["likelihoodHistVBF"] = {"xlabel":"Likelihood (VBF Category)","xlimits":[-0.5,0.5],"rebin":2}
histNames["BDTHistVBF"] = {"xlabel":"BDT (VBF Category)","xlimits":[-0.5,0.5],"rebin":2}

histNames["puJetIDSimpleDiscJet1"] = {"xlabel":"PU Jet ID Simple Discriminator--Leading Jet","xlimits":[-1,1],"rebin":1}
histNames["puJetIDSimpleDiscJet2"] = {"xlabel":"PU Jet ID Simple Discriminator--Sub-Leading Jet","xlimits":[-1,1],"rebin":1}
histNames["puJetIDSimpleDiscJet3"] = {"xlabel":"PU Jet ID Simple Discriminator--3rd Leading Jet","xlimits":[-1,1],"rebin":1}

histNames["puJetIDSimpleJet1"] = {"xlabel":"PU Jet Simple Loose ID--Leading Jet","xlimits":[],"rebin":1}
histNames["puJetIDSimpleJet2"] = {"xlabel":"PU Jet Simple Loose ID--Sub-Leading Jet","xlimits":[],"rebin":1}
histNames["puJetIDSimpleJet3"] = {"xlabel":"PU Jet Simple Loose ID--3rd Leading Jet","xlimits":[],"rebin":1}

histNames["nVtx"] = {"xlabel":"N_{vtx}","xlimits":[0,40],"leg":stdLegendPos}
histNames["met"] = {"xlabel":"E_{T}^{Miss}","xlimits":[0,300],"leg":stdLegendPos}

tlatex = root.TLatex()
tlatex.SetNDC()
tlatex.SetTextSize(0.07)
tlatex.SetTextAlign(12)

#######################################
root.gROOT.SetBatch(True)
setStyle()
#######################################

scaleFactors = {}
#print "scale factors:"
for i in nEventsMap:
  if nEventsMap[i] ==0.0:
    scaleFactors[i] = 0.0
  else:
    p = getPeriod(i)
    scaleFactors[i] = xsec[i]*1000.0*LUMI/nEventsMap[i]*efficiencyMap[p]*mcPlotScaleFactorMap[p]
  #print "%s = %.2e" %(i,scaleFactors[i])

#######################################

class Dataset:
  def __init__(self,filename,legendEntry,color,scaleFactor,isData=False,isSignal=False):
    self.filename = filename
    self.legendEntry = legendEntry
    self.color = color
    self.scaleFactor = scaleFactor

    self.rootFile = root.TFile(filename)
    self.hists = {}
    self.datasetName = os.path.basename(filename)
    self.datasetName = self.datasetName.replace(".root","")
    self.isData=isData
    self.isSignal=isSignal

  def isZombie(self):
    return self.rootFile.IsZombie()

  def loadHistos(self,names,prefix=""):
    for name in names:
      #print("In datasetName: {0}, loading histogram: {1}".format(self.datasetName,name))
      tmpHistInfo = histNames[name]
      xlimits = tmpHistInfo["xlimits"]
      tmp = self.rootFile.Get(prefix+name)
      if type(tmp) != root.TH1F:
        print("Warning: In datasetName: {0}, loading histogram: {1}: Object type is not TH1F!!".format(self.datasetName,prefix+name))
        continue
      tmp.UseCurrentStyle()
      if histNames[name].has_key("rebin"):
        tmp.Rebin(histNames[name]["rebin"])
      if self.isSignal:
        tmp.SetLineColor(self.color)
      elif self.isData:
        tmp.SetMarkerColor(self.color)
        tmp.SetLineColor(self.color)
      else:
        tmp.SetFillColor(self.color)
      tmp.Scale(self.scaleFactor)
      self.hists[prefix+name] = tmp

#######################################

dyDatasetList = []
for i in dyList:
  i += "_"+RUNPERIOD
  if i in scaleFactors:
    if scaleFactors[i]>0.0:
      filename = dataDir+i+".root"
      if not os.path.exists(filename):
          continue
      tmp = Dataset(filename,dyLegendEntries[re.sub(r"_.*","",i)],getColor(i),scaleFactors[i])
      if tmp.isZombie():
        print ("Warning: file for dataset {0} is Zombie!!".format(i))
        continue
      print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      dyDatasetList.append(tmp)

bkgDatasetList = []
for i in backgroundList:
  i += "_"+RUNPERIOD
  if i in scaleFactors:
    if scaleFactors[i]>0.0:
      filename = dataDir+i+".root"
      if not os.path.exists(filename):
          continue
      tmp = Dataset(filename,getLegendEntry(i),getColor(i),scaleFactors[i])
      if tmp.isZombie():
        print ("Warning: file for dataset {0} is Zombie!!".format(i))
        continue
      print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      bkgDatasetList.append(tmp)

sigDatasetList = []
for i in signalList:
  i += "_"+RUNPERIOD
  if i in scaleFactors:
    if scaleFactors[i]>0.0:
      filename = dataDir+i+".root"
      if not os.path.exists(filename):
          continue
      tmp = Dataset(filename,getLegendEntry(i),getColor(i),scaleFactors[i],isSignal=True)
      if tmp.isZombie():
        print ("Warning: file for dataset {0} is Zombie!!".format(i))
        continue
      print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      sigDatasetList.append(tmp)

realDatasetList = []
for i in dataDict[RUNPERIOD]:
      filename = dataDir+i+".root"
      if not os.path.exists(filename):
        print("Error: Data file not found {}, exiting".format(filename))
        sys.exit(1)
      tmp = Dataset(filename,getLegendEntry(RUNPERIOD),1,1.0,isData=True)
      if tmp.isZombie():
        print ("Error: file for dataset {0} is Zombie!!".format(i))
        sys.exit(1)
      print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      realDatasetList.append(tmp)

#######################################

canvas = root.TCanvas("canvas")
leg = root.TLegend(*stdLegendPos)
leg.SetLineColor(0)
leg.SetFillColor(0)
uniqueLegendEntries = set()
dyColors = [root.kRed,root.kBlue]
for ds,col in zip(dyDatasetList,dyColors):
  for hname in ds.hists:
    if ds.legendEntry not in uniqueLegendEntries:
      ds.hists[hname].SetLineColor(col)
      leg.AddEntry(ds.hists[hname],ds.legendEntry,"l")
      uniqueLegendEntries.add(ds.legendEntry)
    break
#for ds in sigDatasetList:
#  for hname in ds.hists:
#    if ds.legendEntry not in uniqueLegendEntries:
#      leg.AddEntry(ds.hists[hname],ds.legendEntry,"l")
#      uniqueLegendEntries.add(ds.legendEntry)
#    break
for ds in realDatasetList:
  for hname in ds.hists:
    if ds.legendEntry not in uniqueLegendEntries:
      leg.AddEntry(ds.hists[hname],ds.legendEntry,"pe")
      uniqueLegendEntries.add(ds.legendEntry)
    break
  break

#######################################

for histName in bkgDatasetList[0].hists:
  print("Making Histo: %s" % histName)
  canvas.Clear()
  bkgHist = None
  sigHist = None
  dyHistList = []
  for ds in bkgDatasetList:
    tmpHist = ds.hists[histName]
    if bkgHist == None:
        bkgHist = tmpHist.Clone(histName+"_BakSum")
    else:
        bkgHist.Add(tmpHist)
  for ds in sigDatasetList:
    tmpHist = ds.hists[histName]
    if sigHist == None:
        sigHist = tmpHist.Clone(histName+"_SigSum")
    else:
        sigHist.Add(tmpHist)
  for ds in dyDatasetList:
    tmpHist = ds.hists[histName]
    dyHistList.append(tmpHist)

  assert(len(dyHistList) == 2)
  dy0Hist = bkgHist.Clone("dy0BakSum")
  dy0Hist.Add(dyHistList[0])
  dy0Hist.SetLineColor(root.kRed+1)
  dy1Hist = bkgHist.Clone("dy1BakSum")
  dy1Hist.Add(dyHistList[1])
  dy1Hist.SetLineColor(root.kBlue+1)

  #dataHist = bkgDatasetList[0].hists[histName].Clone()
  #dataHist.Reset()
  dataHist = realDatasetList[0].hists[histName].Clone()
  dataHist.Reset()
  for realDS in realDatasetList:
    dataHist.Add(realDS.hists[histName])

  histBaseName = re.sub(r".*/","",histName)
  xtitle = histNames[histBaseName]["xlabel"]
  stack = CompareTwoHistsAndData(dy0Hist,dy1Hist, dataHist, canvas, xtitle,lumi=LUMI,logy=LOGY,xlimits=histNames[histBaseName]["xlimits"],integralPlot=integralPlot,energyStr=RUNPERIOD)

  legLeftPos = stdLegendPos[0]
  if histNames[histBaseName].has_key("leg"):
    setLegPos(leg,(histNames[histBaseName]["leg"]))
    legLeftPos = histNames[histBaseName]["leg"][0]
  else:
    setLegPos(leg,stdLegendPos)
  leg.Draw("same")

#  tlatex.SetTextSize(0.03)
#  tlatex.SetTextAlign(33)
#  anotateText = "80 GeV < m_{#mu#mu} < 160 GeV"
#  tlatex.DrawLatex(legLeftPos-0.02,1.0-gStyle.GetPadTopMargin()-0.02,anotateText)

  saveName = histName.replace("(","")
  saveName = saveName.replace(")","")
  saveName = saveName.replace("[","")
  saveName = saveName.replace("]","")
  saveName = saveName.replace("/","_")
  saveAs(canvas,outDir+saveName+"_"+RUNPERIOD)
