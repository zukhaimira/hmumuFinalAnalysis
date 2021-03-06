#!/usr/bin/env python

from xsec import *
from helpers import *
import ROOT as root
import os

dataDir = "input/V00-01-10/"
caption1= "110 GeV < m_{#mu#mu} < 150 GeV"
outDir = "output/"
caption2=""

CUTS="dimuonMass < 150. && dimuonMass > 110."
#CUTS+= "&& nJets>=2 && ptMiss<40. && dijetMass > 650."
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, m_{jj}>650 GeV"
#CUTS+= "&& nJets>=2 && ptMiss<40. && dijetMass > 650. && deltaEtaJets > 3.5"
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, 2-Jet Cuts"
CUTS+= "&& nJets>=2 && ptMiss<40. && dijetMass > 500."
caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, m_{jj}>500"

#CUTS+= "&& nJets>=2 && ptMiss<40. && deltaEtaJets>3.0"
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV,|#Delta#eta|>3, p_{T}(j_{1},j_{2})> 30,30 GeV"

#CUTS+= "&& nJets>=2 && ptMiss<40. && jetLead_pt>60. && jetSub_pt>50."
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, p_{T}(j_{1},j_{2})> 60,50 GeV"

#CUTS+= "&& nJets>=2 && ptMiss<40. && jetLead_pt>60. && jetSub_pt<50."
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, p_{T}(j_{1},j_{2})< 60,50 GeV"

#CUTS+= "&& nJets>=2 && ptMiss<40. && deltaEtaJets>3.5"
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, |#Delta#eta_{jj}|>3.5"

#CUTS+= "&& nJets>=2 && ptMiss<40. && deltaEtaJets<3.5"
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, |#Delta#eta_{jj}|<3.5"

#CUTS+= "&& nJets>=2 && ptMiss<40. && jetLead_pt>60. && jetSub_pt>50. && deltaEtaJets>3.5"
#caption1+= ", |#Delta#eta_{jj}|>3.5"
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, p_{T}(j_{1},j_{2})> 60,50 GeV"

#CUTS+= "&& nJets>=2 && ptMiss<40. && jetLead_pt<60. && jetSub_pt<50. && deltaEtaJets>3.5"
#caption1+= ", |#Delta#eta_{jj}|>3.5"
#caption2="#geq2 Jets, p_{T}^{Miss}<40 GeV, p_{T}(j_{1},j_{2})< 60,50 GeV"


RUNPERIOD="8TeV"
LUMI=lumiDict[RUNPERIOD]

LOGY=False
reverse=False
allHiggsTogether = False
drawString="HIST"
LEGDRAWSTRING="l"
drawString="PE"
LEGDRAWSTRING="lep"

histDirs = [""]
#histDirs = ["Jets0/","Jets1/","Jets2/"]

categoryAnotations ={}
categoryAnotations['Jets0/'] = "0 Jet"
categoryAnotations['Jets1/'] = "1 Jet"
categoryAnotations['Jets2/'] = "#geq2 Jets"

backgroundList = [
"DYJetsToLL"#,
#"ttbar"
]

signalList = [
"ggHmumu125",
"vbfHmumu125"
]

#colors["DYJetsToLL"] = root.kBlue

urLegendPos = [0.68,0.65,0.88,0.88]
lcLegendPos = [0.45,0.25,0.65,0.48]
lrLegendPos = [0.68,0.25,0.88,0.48]
ulLegendPos = [0.25,0.65,0.45,0.88]
stdLegendPos = urLegendPos

histNames = {}
if True:
    #histNames["dimuonMass"] = {"xlabel":"m_{#mu#mu} [GeV/c^{2}]","xlimits":[110.0,150.],"nbins":40}#,"ylimits":[0.1,5e5]}
    #histNames["dimuonPt"] = {"xlabel":"p_{T,#mu#mu} [GeV/c]","xlimits":[0.0,200.0],"nbins":20}#,"ylimits":[0.1,1e5]}
    #histNames["dimuonY"] = {"xlabel":"y_{#mu#mu}","xlimits":[-2.2,2.2],"nbins":10}#,"ylimits":[0.1,3e6]}
    #histNames["cosThetaStar"] = {"xlabel":"cos(#theta^{*})","xlimits":[-2.2,2.2],"nbins":10}#,"ylimits":[0.1,3e6]}
    #histNames["muonLead_pt"] = {"xlabel":"Leading Muon p_{T} [GeV/c]","xlimits":[25.,150.],"nbins":25}#,"ylimits":[0.1,3e6]}
    #histNames["muonSub_pt"] = {"xlabel":"Sub-Leading Muon p_{T} [GeV/c]","xlimits":[25.,150.],"nbins":25}#,"ylimits":[0.1,3e6]}
    #histNames["muonLead_eta"] = {"xlabel":"Leading Muon #eta","xlimits":[-2.1,2.1],"nbins":25}#,"ylimits":[0.1,3e6]}
    #histNames["muonSub_eta"] = {"xlabel":"Sub-Leading Muon #eta","xlimits":[-2.1,2.1],"nbins":10}#,"ylimits":[0.1,3e6]}

    #histNames["nJets"] = {"xlabel":"N_{jets}","xlimits":[-0.5,5.5],"nbins":6}#,"ylimits":[0.1,3e6]}
    #histNames["ptMiss"] = {"xlabel":"Missing p_{T} [GeV/c]","xlimits":[0.0,300.0],"nbins":12}#,"ylimits":[0.1,3e6]}
    histNames["deltaEtaJets"] = {"xlabel":"#Delta#eta(j_{1},j_{2})","xlimits":[0.0,7.0],"nbins":14}#,"ylimits":[0.1,3e6]}
    histNames["dijetMass"] = {"xlabel":"m_{jj} [GeV/c^{2}]","xlimits":[0.0,1000.],"nbins":20}#,"ylimits":[0.1,3e6]}
    histNames["dijetYabs"] = {"xlabel":"|Y_{jj}|","xlimits":[0,2.5],"nbins":5}#,"ylimits":[0.1,3e6]}
    histNames["dijetPt"] = {"xlabel":"p_{T,jj} [GeV/c]","xlimits":[0,500.],"nbins":25}#,"ylimits":[0.1,3e6]}

    #histNames["jetLead_pt"] = {"xlabel":"Leading Jet p_{T} [GeV/c]","xlimits":[30.,150.],"nbins":12}#,"ylimits":[0.1,3e6]}
    #histNames["jetSub_pt"] = {"xlabel":"Sub-Leading Jet p_{T} [GeV/c]","xlimits":[30.,150.],"nbins":12}#,"ylimits":[0.1,3e6]}
    #histNames["jetLead_eta"] = {"xlabel":"Leading Jet #eta","xlimits":[-5,5],"nbins":20}#,"ylimits":[0.1,3e6]}
    #histNames["jetSub_eta"] = {"xlabel":"Sub-Leading Jet #eta","xlimits":[-5,5],"nbins":20}#,"ylimits":[0.1,3e6]}
    #histNames["jetLead_PUIDDisc"] = {"xlabel":"Leading Jet PUID","xlimits":[-1,1],"nbins":20,"leg":ulLegendPos}#,"ylimits":[0.1,3e6]}
    #histNames["jetSub_PUIDDisc"] = {"xlabel":"Sub-Leading Jet PUID","xlimits":[-1,1],"nbins":20,"leg":ulLegendPos}#,"ylimits":[0.1,3e6]}
    #histNames["jetLead_PUIDDisc_Forward"] = {"xlabel":"Leading Jet PUID (|#eta|>2.4)","xlimits":[-1,1],"nbins":20,"leg":ulLegendPos}#,"ylimits":[0.1,3e6]}
    #histNames["jetSub_PUIDDisc_Forward"] = {"xlabel":"Sub-Leading Jet PUID (|#eta|>2.4)","xlimits":[-1,1],"nbins":20,"leg":urLegendPos}#,"ylimits":[0.1,3e6]}

    #histNames["jetLead_PUIDDisc_Central"] = {"xlabel":"Leading Jet PUID (|#eta|<2.4)","xlimits":[-1,1],"nbins":20,"leg":ulLegendPos}#,"ylimits":[0.1,3e6]}
    #histNames["jetSub_PUIDDisc_Central"] = {"xlabel":"Sub-Leading Jet PUID (|#eta|<2.4)","xlimits":[-1,1],"nbins":20,"leg":ulLegendPos}#,"ylimits":[0.1,3e6]}

    #histNames["KD"] = {"xlabel":"MEKD","xlimits":[0.0,1.0],"nbins":20,'leg':ulLegendPos}#,"ylimits":[0.1,3e6]}
    #histNames["KDPdf"] = {"xlabel":"MEKD","xlimits":[0.0,1.0],"nbins":20,'leg':ulLegendPos}#,"ylimits":[0.1,3e6]}
    #histNames["sigME"] = {"xlabel":"Signal |M|^2","xlimits":[0.0,1e-3],"nbins":40}#,"ylimits":[0.1,3e6]}
    #histNames["sigMEPdf"] = {"xlabel":"Signal |M|^2 (Including PDF Info)","xlimits":[0.0,120.0],"nbins":30}#,"ylimits":[0.1,3e6]}
    #histNames["bakME"] = {"xlabel":"Drell-Yan |M|^2","xlimits":[0.0,0.05],"nbins":30}#,"ylimits":[0.1,3e6]}
    #histNames["bakMEPdf"] = {"xlabel":"Drell-Yan |M|^2 (Including PDF Info)","xlimits":[0.0,120.0],"nbins":30}#,"ylimits":[0.1,3e6]}
    #histNames["sigMENorm"] = {"xlabel":"Signal |M|^2","xlimits":[0.0,1.],"nbins":20}#,"ylimits":[0.1,3e6]}
    #histNames["sigMEPdfNorm"] = {"xlabel":"Signal |M|^2 (Including PDF Info)","xlimits":[0.0,1.0],"nbins":20}#,"ylimits":[0.1,3e6]}
    #histNames["bakMENorm"] = {"xlabel":"Drell-Yan |M|^2","xlimits":[0.0,1.],"nbins":20}#,"ylimits":[0.1,3e6]}
    #histNames["bakMEPdfNorm"] = {"xlabel":"Drell-Yan |M|^2 (Including PDF Info)","xlimits":[0.0,1.0],"nbins":20}#,"ylimits":[0.1,3e6]}

#######################################
root.gROOT.SetBatch(True)
setStyle()
#######################################

GLOBALCOUNTER=0
scaleFactors = {}
#print "scale factors:"
for i in nEventsMap:
  if nEventsMap[i] ==0.0:
    scaleFactors[i] = 0.0
  else:
    scaleFactors[i] = xsec[i]*1000.0*LUMI/nEventsMap[i]
  #print "%s = %.2e" %(i,scaleFactors[i])

#######################################

class Dataset:
  def __init__(self,filename,legendEntry,color,scaleFactor):
    self.filename = filename
    self.legendEntry = legendEntry
    self.color = color
    self.scaleFactor = scaleFactor

    if filename != "":
      self.rootFile = root.TFile(filename)
      self.tree = self.rootFile.Get("outtree")
      self.tree.SetCacheSize(10000000);
      self.tree.AddBranchToCache("*");
    self.hists = {}
    self.datasetName = os.path.basename(filename)
    self.datasetName = self.datasetName.replace(".root","")

  def isZombie(self):
    return self.rootFile.IsZombie()

  def loadHistos(self,names,prefix=""):
    global GLOBALCOUNTER
    for name in names:
      #print("In datasetName: {0}, loading histogram: {1}".format(self.datasetName,name))
      tmpHistInfo = histNames[name]
      xlimits = tmpHistInfo["xlimits"]
      nbins = tmpHistInfo["nbins"]
      tmpHistName = name+str(GLOBALCOUNTER)
      GLOBALCOUNTER += 1
      varToDraw = name
      tmpCUTS = CUTS
      if "Norm" in name:
        varToDraw = varToDraw.replace("Norm","")
        varToDraw += " * "+str(MENormDict[RUNPERIOD][varToDraw])
      if "_Forward" in name:
        varToDraw = varToDraw.replace("_Forward","")
        if "jetLead" in varToDraw:
          tmpCUTS += " && abs(jetLead_eta) > 2.4"
        elif "jetSub" in varToDraw:
          tmpCUTS += " && abs(jetSub_eta) > 2.4"
      if "_Central" in name:
        varToDraw = varToDraw.replace("_Central","")
        if "jetLead" in varToDraw:
          tmpCUTS += " && abs(jetLead_eta) < 2.4"
        elif "jetSub" in varToDraw:
          tmpCUTS += " && abs(jetSub_eta) < 2.4"
      if name == "KD":
        sigNorm = MENormDict[RUNPERIOD]["sigME"]
        bakNorm = MENormDict[RUNPERIOD]["bakME"]
        varToDraw = "sigME*%f/(bakME*%f+sigME*%f)" % (sigNorm,bakNorm,sigNorm)
      if name == "KDPdf":
        sigNorm = MENormDict[RUNPERIOD]["sigMEPdf"]
        bakNorm = MENormDict[RUNPERIOD]["bakMEPdf"]
        varToDraw = "sigMEPdf*%f/(bakMEPdf*%f+sigMEPdf*%f)" %(sigNorm,bakNorm,sigNorm)
      if "abs" in name:
        varToDraw = varToDraw.replace("abs","")
        varToDraw = "abs("+varToDraw+")"
      drawStr = varToDraw+" >> "+tmpHistName+"("+str(nbins)+","+str(xlimits[0])+","+str(xlimits[1])+")"
      #print drawStr
      cutStr = treeCut(prefix,tmpCUTS)
      #print cutStr
      self.tree.Draw(drawStr,cutStr)
      tmp = root.gDirectory.Get(tmpHistName)
      if type(tmp) != root.TH1F:
        print("Warning: In datasetName: %s, loading histogram: %s: Object type is not TH1F!!" % (self.datasetName,prefix+name))
        continue
      tmp.UseCurrentStyle()
      if histNames[name].has_key("rebin"):
        tmp.Rebin(histNames[name]["rebin"])
      tmp.SetFillColor(self.color)
      tmp.SetFillStyle(1)
      tmp.SetLineColor(self.color)
      tmp.SetMarkerColor(self.color)
      tmp.Sumw2()
      tmp.Scale(self.scaleFactor)
      self.hists[prefix+name] = tmp
  def eatOtherDatasets(self,listOfOthers):
    first = True
    for ds in listOfOthers:
      if first:
        first = False
        self.hists = ds.hists
        for key in self.hists:
          tmp = self.hists[key]
          tmp.SetFillColor(self.color)
          tmp.SetFillStyle(1)
          tmp.SetMarkerColor(self.color)
          tmp.SetLineColor(self.color)
      else:
        for key in self.hists:
          self.hists[key].Add(ds.hists[key])

#######################################

dataDatasetList = []
for i in dataDict[RUNPERIOD]:
      print("looking at data: " + i)
      filename = dataDir+i+".root"
      if not os.path.exists(filename):
          continue
      tmp = Dataset(filename,i,1,1.0)
      if tmp.isZombie():
        print ("Warning: file for dataset {0} is Zombie!!".format(i))
        continue
      #print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      dataDatasetList.append(tmp)

bkgDatasetList = []
for i in backgroundList:
  print("looking at bkg: " + i)
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
      #print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      bkgDatasetList.append(tmp)

sigDatasetList = []
for i in signalList:
  i += "_"+RUNPERIOD
  print i
  if i in scaleFactors:
    if scaleFactors[i]>0.0:
      filename = dataDir+i+".root"
      if not os.path.exists(filename):
          continue
      tmp = Dataset(filename,getLegendEntry(i),getColor(i),scaleFactors[i])
      if tmp.isZombie():
        print ("Warning: file for dataset {0} is Zombie!!".format(i))
        continue
      #print("Loading Dataset: {0}".format(i))
      for hDir in histDirs:
        tmp.loadHistos(histNames,prefix=hDir)
      sigDatasetList.append(tmp)
oldSigDatasetList = sigDatasetList
if allHiggsTogether:
  allHiggsDataset = Dataset("","H #rightarrow #mu#mu",root.kRed,1.0)
  allHiggsDataset.eatOtherDatasets(sigDatasetList)
  sigDatasetList = [allHiggsDataset]

oldDataDatasetList = dataDatasetList
allDataDataset = Dataset("","Data",root.kBlack,1.0)
allDataDataset.eatOtherDatasets(dataDatasetList)
bkgDatasetList = [allDataDataset]

bkgDatasetList += sigDatasetList

if reverse:
  bkgDatasetList.reverse()

#######################################

canvas = root.TCanvas("canvas")
leg = root.TLegend(*stdLegendPos)
#leg = root.TLegend(*lcLegendPos)
leg.SetLineColor(0)
leg.SetFillColor(0)
uniqueLegendEntries = set()
for ds in bkgDatasetList:
  for hname in ds.hists:
    if ds.legendEntry not in uniqueLegendEntries:
      leg.AddEntry(ds.hists[hname],ds.legendEntry,LEGDRAWSTRING)
      uniqueLegendEntries.add(ds.legendEntry)
    break

#######################################

for histName in bkgDatasetList[0].hists:
  canvas.Clear()
  histBaseName = re.sub(r".*/","",histName)
  histCategoryName = re.sub(r"/.*","",histName)+'/'
  print("Making Histo: %s" % histName)
  bkgHistList = []
  for ds in bkgDatasetList:
    tmpHist = ds.hists[histName]
    if histNames[histBaseName].has_key("xlimits"):
      if histNames[histBaseName]["xlimits"] != []:
        tmpHist.GetXaxis().SetRangeUser(*histNames[histBaseName]["xlimits"])
    if histNames[histBaseName].has_key("rebin"):
        tmpHist.Rebin(histNames[histBaseName]["rebin"])
    if tmpHist.Integral() != 0.0:
      tmpHist.Scale(1.0/tmpHist.Integral())
    bkgHistList.append(tmpHist)
  bkgHistList.reverse()

  xtitle = histNames[histBaseName]["xlabel"]
  if LOGY:
    canvas.SetLogy(1)
  else:
    canvas.SetLogy(0)
  firstHist = True
  ymin = 9999999.0
  ymax = -9999999.0
  for hist in bkgHistList:
    hist.SetTitle("")
    hist.GetYaxis().SetTitle("Normalized Events")
    hist.GetXaxis().SetTitle(xtitle)
    if histNames[histBaseName].has_key("xlimits"):
      if histNames[histBaseName]["xlimits"] != []:
        hist.GetXaxis().SetRangeUser(*histNames[histBaseName]["xlimits"])
    hist.SetFillStyle(0)
    hist.SetLineStyle(1)
    hist.SetLineWidth(2)
    hist.SetLineColor(hist.GetFillColor())
    if ymax < hist.GetMaximum():
      ymax = hist.GetMaximum()
    if ymin < hist.GetMinimum():
      ymin = hist.GetMinimum()
    if firstHist:
      hist.Draw(drawString)
      firstHist = False
    else:
      hist.Draw(drawString+" same")
  firstHist = True
  print ymax
  for hist in bkgHistList:
    hist.SetTitle("")
    hist.GetYaxis().SetRangeUser(ymin*0.95,ymax*0.6)
    #hist.GetYaxis().SetRangeUser(ymin*0.95,ymax*0.8)
    if firstHist:
      hist.Draw(drawString)
      firstHist = False
    else:
      hist.Draw(drawString+" same")
  canvas.RedrawAxis()
  if histNames[histBaseName].has_key("leg"):
    setLegPos(leg,(histNames[histBaseName]["leg"]))
  else:
    setLegPos(leg,(stdLegendPos))
  leg.Draw()

  caption2ToDraw = caption2
  if categoryAnotations.has_key(histCategoryName):
    caption2ToDraw += categoryAnotations[histCategoryName]

  tlatex = root.TLatex()
  tlatex.SetNDC()
  tlatex.SetTextFont(root.gStyle.GetLabelFont())
  tlatex.SetTextSize(0.04)
  tlatex.SetTextAlign(12)
  tlatex.DrawLatex(gStyle.GetPadLeftMargin(),0.96,PRELIMINARYSTRING)
  tlatex.SetTextAlign(32)
  tlatex.DrawLatex(1.0-gStyle.GetPadRightMargin(),0.96,"#sqrt{s}=%s" % (RUNPERIOD))
  if histNames[histBaseName].has_key("leg") and histNames[histBaseName]["leg"] == ulLegendPos:
    tlatex.SetTextAlign(33)
    tlatex.DrawLatex(1.0-gStyle.GetPadRightMargin()-0.03,1.0-gStyle.GetPadTopMargin()-0.04,caption1)
    tlatex.DrawLatex(1.0-gStyle.GetPadRightMargin()-0.03,1.0-gStyle.GetPadTopMargin()-0.09,caption2ToDraw)
  else:
    tlatex.SetTextAlign(13)
    tlatex.DrawLatex(gStyle.GetPadLeftMargin()+0.03,1.0-gStyle.GetPadTopMargin()-0.04,caption1)
    tlatex.DrawLatex(gStyle.GetPadLeftMargin()+0.03,1.0-gStyle.GetPadTopMargin()-0.09,caption2ToDraw)

  saveName = histName.replace("(","")
  saveName = saveName.replace(")","")
  saveName = saveName.replace("[","")
  saveName = saveName.replace("]","")
  saveName = saveName.replace("/","_")
  saveAs(canvas,outDir+"dist_"+saveName+"_"+RUNPERIOD)
