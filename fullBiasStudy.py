#! /usr/bin/env python

from ROOT import gSystem

import datetime
import sys
import os
import re
import math
import cPickle
import ROOT as root
root.gSystem.Load('libRooFit')
root.gROOT.SetBatch(True)

from helpers import *
import makeCards

from numpy import mean, median, corrcoef
from numpy import std as stddev

#root.gErrorIgnoreLevel = root.kWarning
#root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.WARNING)
#root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.ERROR)
PRINTLEVEL = root.RooFit.PrintLevel(-1) #For MINUIT
#PRINTLEVEL = root.RooFit.PrintLevel(1) #For MINUIT

canvas = root.TCanvas()

class BiasStudy:
  #def __init__(self,category,dataFiles,energyStr):
  def __init__(self,category,dataFileNames,energyStr,nToys=10,pklOutFnBase="output/biasData",inputPkl=None):
    self.sigMasses = range(115,156,5)
    self.sigMasses = [125,150]
    ## Try to load data from pkl file
    if inputPkl != None:
      try:
        inputPklF = open(inputPkl)
        self.data = cPickle.load(inputPklF)
        inputPklF.close()
        self.pdfAltNameList = self.data['meta']['pdfAltNameList']
        self.pdfAltNameList = self.data['meta']['pdfAltNameList']
        self.nToys = self.data['meta']['nToys']
        self.nData = self.data['meta']['nData']
        self.catName = self.data['meta']['catName']
        self.energyStr = self.data['meta']['energyStr']
        energyStr = self.energyStr
        self.truePdfName = self.data['meta']['truePdfName']
        self.truePdfTitle = self.data['meta']['truePdfTitle']
        self.sigMasses = self.data['meta']['sigMasses']
      except Exception, err:
        print("Error loading data from pkl file: "+str(inputPkl))
        print(err)
        self.data = None
    else:
      self.catName = category[0]
      self.catCuts = category[1]
      self.energyStr = energyStr
      self.nToys = nToys
      self.pklOutFn = pklOutFnBase+"_"+self.catName+"_"+energyStr+".pkl"
      self.data = None
    catName = self.catName
    canvas = root.TCanvas()
    self.canvas = canvas
    ## Run
    if self.data==None:
      data = {'meta':{}}
      self.data = data
      data['meta']['sigMasses'] = self.sigMasses
      self.dimuonMass = root.RooRealVar("dimuonMass","m [GeV/c^{2}]",110.,170.)
      dimuonMass = self.dimuonMass
      dimuonMass.setRange("low",110,120) # Silly ranges for old fit functionality
      dimuonMass.setRange("high",130,170)
      dimuonMass.setRange("signal",120,130)
      dimuonMass.setRange("signalfit",110,140)
      self.wTrue = root.RooWorkspace("wTrue")
      self.wTrueToy = root.RooWorkspace("wTrueToy")
      wTrueImport = getattr(self.wTrue,"import")
      wTrueToyImport = getattr(self.wTrueToy,"import")

      # Hack to Make makePDFBakOld work
      self.minMassZ = 88.
      self.maxMassZ = 94.
      dimuonMassZ = root.RooRealVar("dimuonMass","dimuonMass",self.minMassZ,self.maxMassZ)
      self.dimuonMassZ = dimuonMassZ

      ### Load data
      
      self.dataTree = root.TChain()
      for i in dataFileNames:
        self.dataTree.Add(i+"/outtree"+self.catName)
      self.dataTree.SetCacheSize(10000000);
      self.dataTree.AddBranchToCache("*");

      self.realData = root.RooDataSet("realData"+catName+energyStr,
                                      "realData"+catName+energyStr,
                                          self.dataTree,root.RooArgSet(dimuonMass)
                                        )
      self.nData = self.realData.sumEntries()

      self.realDataZ = root.RooDataSet("realDataZ"+catName+energyStr,
                                      "realDataZ"+catName+energyStr,
                                          self.dataTree,root.RooArgSet(dimuonMassZ)
                                        )

      ### Make Bak Pdfs

      self.truePdfName = "true"+catName+energyStr
      self.truePdfTitle = "#frac{Exp(p_{1}m)}{(m-p_{2})^{2}}"
      data['meta']['truePdfName'] = self.truePdfName
      data['meta']['truePdfTitle'] = self.truePdfTitle
      self.truePdfFunc = makeCards.makePDFBakExpMOverSq
      #self.truePdfTitle ="Voigtian+Exp" 
      #self.truePdfFunc = makeCards.makePDFBakOld
      self.truePdfFunc(self.truePdfName,self.realData,dimuonMass,110,170,wTrueImport,dimuonMassZ,self.realDataZ)
      self.truePdf = self.wTrue.pdf("bak")
      self.truePdf.SetName(self.truePdfName)
      self.truePdf.SetTitle("True PDF "+self.truePdfTitle)

      self.trueToyPdfName = "trueToy"+catName+energyStr
      self.truePdfFunc(self.trueToyPdfName,self.realData,dimuonMass,110,170,wTrueToyImport,dimuonMassZ,self.realDataZ)
      self.trueToyPdf = self.wTrueToy.pdf("bak")
      self.trueToyPdf.SetName(self.trueToyPdfName)

      self.pdfAltList = []
      self.pdfAltwList = []
      self.pdfAltNameList = [
          "ExpLog",
          "MOverSq",
          "BakOld",
          #"BakExpMOverSq",
      ]
      self.pdfAltFuncList = [
          makeCards.makePDFBakExpLog,
          makeCards.makePDFBakMOverSq,
          makeCards.makePDFBakOld,
          #makeCards.makePDFBakExpMOverSq,
      ]
      data['meta']['pdfAltNameList'] = self.pdfAltNameList
      for pdfAltName,pdfAltFunc in zip(self.pdfAltNameList,self.pdfAltFuncList):
        pdfName = "alt"+catName+energyStr+"_"+pdfAltName
        wAlt = root.RooWorkspace("wAlt"+catName+energyStr+"_"+pdfAltName)
        pdfAltFunc(pdfName,self.realData,dimuonMass,110,170,getattr(wAlt,"import"),dimuonMassZ,self.realDataZ)
        altPdf = wAlt.pdf("bak")
        altPdf.SetName(pdfName)
        self.pdfAltList.append(altPdf)
        self.pdfAltwList.append(wAlt)

      self.nBakVar = root.RooRealVar("nBak","N_{B}",self.nData/2.,self.nData*2)

      ### Now load Signal PDFs
      
      self.sigPdfs = []
      self.wSigs = []
      for hmass in self.sigMasses:
        wSig = root.RooWorkspace("signal"+catName+energyStr+str(hmass))
        makeCards.makePDFSigNew(catName+energyStr,"sig_ggH",dimuonMass,float(hmass),
                                getattr(wSig,"import")
                               )
        sigPdf = wSig.pdf("ggH")
        sigPdf.SetName("sigPDF_"+str(hmass)+"_"+catName+energyStr)
        self.sigPdfs.append(sigPdf)
        self.wSigs.append(wSig)

      for i in self.sigPdfs:
        i.Print()

      self.nSigVar = root.RooRealVar("nSig","N_{S}",-self.nData/4.,self.nData/4)

      ### Make results data structure and begin log

      data['meta']['nToys'] = self.nToys
      data['meta']['nData'] = self.nData
      data['meta']['catName'] = self.catName
      data['meta']['energyStr'] = self.energyStr

      for hmass in self.sigMasses:
        data[hmass] = {}
        data[hmass]['zTrue'] = []
        data[hmass]['nTrue'] = []
        data[hmass]['chi2True'] = []
        data[hmass]['ndfTrue'] = []
        data[hmass]['errTrue'] = []
        data[hmass]['pullAll'] = []
        for pdfAltName in self.pdfAltNameList:
          data[hmass][pdfAltName] = {'z':[],'pull':[],'n':[],'err':[],'chi2':[],'ndf':[]}

      ### Toy Loop

      for iToy in range(self.nToys):
        toyData = self.truePdf.generate(root.RooArgSet(dimuonMass),int(self.nData))
        toyData.SetName("toyData"+catName+energyStr+str(iToy))
        toyDataHist = toyData.binnedClone("toyDataHist"+catName+energyStr+str(iToy))
        plotThisToy = (iToy % 10 == 0)
        saveThisData = (iToy % 100 == 99)
        for hmass,sigPdf in zip(self.sigMasses,self.sigPdfs):
          frame = None 
          if plotThisToy:
            frame = dimuonMass.frame()
            toyData.plotOn(frame)
  
          trueToySBPdf = root.RooAddPdf("SBTrue"+catName+energyStr+str(hmass)+"_"+str(iToy),"",
                              root.RooArgList(self.trueToyPdf,sigPdf),
                              root.RooArgList(self.nBakVar,self.nSigVar)
                          )
          trueToySBPdf.fitTo(toyData,
                             PRINTLEVEL
                           )
          chi2TrueToyVar = trueToySBPdf.createChi2(toyDataHist)
          ndfTrue = dimuonMass.getBins() - 1  # b/c roofit normalizes
          ndfTrue -= trueToySBPdf.getParameters(toyDataHist).getSize()
          if plotThisToy:
            trueToySBPdf.plotOn(frame,root.RooFit.LineColor(6))
            #trueToySBPdf.plotOn(frame,root.RooFit.Components(root.RooArgSet(self.trueToyPdf)),root.RooFit.LineColor(1),root.RooFit.LineStyle(2))
          nTrueToy = self.nSigVar.getVal()
          errTrueToy = self.nSigVar.getError()
          data[hmass]['nTrue'].append(nTrueToy)
          data[hmass]['errTrue'].append(errTrueToy)
          data[hmass]['chi2True'].append(chi2TrueToyVar.getVal())
          data[hmass]['ndfTrue'].append(ndfTrue)
          if errTrueToy != 0.:
            data[hmass]['zTrue'].append(nTrueToy/errTrueToy)
          for pdfAlt,pdfAltName,color in zip(self.pdfAltList,self.pdfAltNameList,range(2,len(self.pdfAltList)+2)):
              altSBPdf = root.RooAddPdf("SB"+pdfAltName+catName+energyStr+str(hmass)+"_"+str(iToy),"",
                              root.RooArgList(pdfAlt,sigPdf),
                              root.RooArgList(self.nBakVar,self.nSigVar)
                          )
              altSBPdf.fitTo(toyData,
                              PRINTLEVEL
                              )
              altChi2Var = altSBPdf.createChi2(toyDataHist)
              ndfAlt = dimuonMass.getBins() - 1  # b/c roofit normalizes
              ndfAlt -= altSBPdf.getParameters(toyDataHist).getSize()
              if plotThisToy:
                altSBPdf.plotOn(frame,root.RooFit.LineColor(color))
                #altSBPdf.plotOn(frame,root.RooFit.Components(root.RooArgSet(pdfAlt)),root.RooFit.LineColor(color),root.RooFit.LineStyle(2))
              nAlt = self.nSigVar.getVal()
              errAlt = self.nSigVar.getError()
              if errAlt == 0.:
                  continue
              pull = (nTrueToy-nAlt)/errAlt
              data[hmass][pdfAltName]['n'].append(nAlt)
              data[hmass][pdfAltName]['err'].append(errAlt)
              data[hmass][pdfAltName]['chi2'].append(altChi2Var.getVal())
              data[hmass][pdfAltName]['ndf'].append(ndfAlt)
              data[hmass][pdfAltName]['z'].append(nAlt/errAlt)
              data[hmass][pdfAltName]['pull'].append(pull)
              data[hmass]['pullAll'].append(pull)
          if plotThisToy:
            frame.Draw()
            canvas.SaveAs("output/debug_"+catName+"_"+energyStr+"_"+str(hmass)+"_"+str(iToy)+".png")
          if saveThisData:
            pklTmpFile = open(self.pklOutFn+"."+str(iToy),'w')
            cPickle.dump(data,pklTmpFile)
            pklTmpFile.close()
        del toyData

      pklFile = open(self.pklOutFn,'w')
      cPickle.dump(data,pklFile)
      pklFile.close()

    outStr = "#"*80+"\n"
    outStr = "#"*80+"\n"
    outStr += "\n"+self.catName +"  "+self.energyStr + "\n\n"

    outStr += "nToys: {0}\n".format(self.nToys)
    outStr += "nData Events: {0}\n".format(self.nData)
    outStr += "\n"

    data = self.data

    for hmass in self.sigMasses:
      outStr +=  "mass: "+str(hmass)+'\n'
      dataH = data[hmass]
      outStr +=  "  True Z Scores:   {0:.2f} +/- {1:.2f}  Median: {2:.2f}\n".format(mean(dataH['zTrue']),stddev(dataH['zTrue']),median(dataH['zTrue']))
      outStr +=  "  All Pulls:       {0:.2f} +/- {1:.2f}  Median: {2:.2f}\n".format(mean(dataH['pullAll']),stddev(dataH['pullAll']),median(dataH['pullAll']))
      for pdfAltName in self.pdfAltNameList:
        dataHA = dataH[pdfAltName]
        outStr +=  "  "+pdfAltName+":\n"
        outStr +=  "    Z Scores:      {0:.2f} +/- {1:.2f}  Median: {2:.2f}\n".format(mean(dataHA['z']),stddev(dataHA['z']),median(dataHA['z']))
        outStr +=  "    Pulls:         {0:.2f} +/- {1:.2f}  Median: {2:.2f}\n".format(mean(dataHA['pull']),stddev(dataHA['pull']),median(dataHA['pull']))
    print outStr
    self.outStr = outStr

  def plot(self,outputPrefix):
    self.pdfAltTitleMap = {
        "ExpLog":"Exp(p_{1}m^{2}+p_{2}m+p_{3}ln(m))",
        "MOverSq":"#frac{m}{(m-p_{1})^{2}}",
        "BakOld":"Voigtian+Exp",
        "BakExpMOverSq":"#frac{Exp(p_{1}m)}{(m-p_{2})^{2}}",
    }
    titleMap = {
      "Jets01PassPtG10BB": "0,1-Jet Tight BB",
      "Jets01PassPtG10BO": "0,1-Jet Tight BO",
      "Jets01PassPtG10BE": "0,1-Jet Tight BE",
      "Jets01PassPtG10OO": "0,1-Jet Tight OO",
      "Jets01PassPtG10OE": "0,1-Jet Tight OE",
      "Jets01PassPtG10EE": "0,1-Jet Tight EE",
      "Jets01PassCatAll" : "0,1-Jet Tight Combination",
                            
      "Jets01FailPtG10BB": "0,1-Jet Loose BB",
      "Jets01FailPtG10BO": "0,1-Jet Loose BO",
      "Jets01FailPtG10BE": "0,1-Jet Loose BE",
      "Jets01FailPtG10OO": "0,1-Jet Loose OO",
      "Jets01FailPtG10OE": "0,1-Jet Loose OE",
      "Jets01FailPtG10EE": "0,1-Jet Loose EE",
      "Jets01FailCatAll" : "0,1-Jet Loose Combination",
    
      "Jet2CutsVBFPass":"2-Jet VBF Tight",
      "Jet2CutsGFPass":"2-Jet GF Tight",
      "Jet2CutsFailVBFGF":"2-Jet Loose",
    }

    canvas = self.canvas
    tlatex = root.TLatex()
    tlatex.SetNDC()
    tlatex.SetTextFont(root.gStyle.GetLabelFont())
    tlatex.SetTextSize(0.04)
    caption = titleMap[self.catName]
    caption2 = ""
    caption3 = ""
    caption4 = ""
    iHist = 0
    for hmass in self.sigMasses:
      hist = root.TH1F("hist"+str(iHist),"",30,-3,3)
      setHistTitles(hist,"(N_{sig}(Alt)-N_{sig}(Ref))/#DeltaN_{sig}(Alt)","N_{Toys}")
      iHist += 1
      for pull in self.data[hmass]['pullAll']:
          hist.Fill(pull)
      hist.Draw()
      tlatex.SetTextAlign(12)
      tlatex.DrawLatex(gStyle.GetPadLeftMargin(),0.96,PRELIMINARYSTRING)
      tlatex.SetTextAlign(12)
      tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.85,"Reference PDF: "+self.truePdfTitle)
      tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.75,"All Alternate PDFs")
      tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.68,"m_{H} = "+str(hmass)+" GeV/c^{2}")
      tlatex.SetTextAlign(32)
      tlatex.DrawLatex(0.99-gStyle.GetPadRightMargin(),0.96,caption)
      line = self.setYMaxAndDrawVertLines(hist,median(self.data[hmass]['pullAll']))
      canvas.RedrawAxis()
      saveAs(canvas,outputPrefix+self.catName+"_"+str(hmass)+"_All")
      canvas.Clear()

      for pdfAltName in self.pdfAltNameList:
        hist = root.TH1F("hist"+str(iHist),"",30,-3,3)
        setHistTitles(hist,"(N_{sig}(Alt)-N_{sig}(Ref))/#DeltaN_{sig}(Alt)","N_{Toys}")
        iHist += 1
        for pull in self.data[hmass][pdfAltName]['pull']:
            hist.Fill(pull)
        hist.Draw()
        tlatex.SetTextAlign(12)
        tlatex.DrawLatex(gStyle.GetPadLeftMargin(),0.96,PRELIMINARYSTRING)
        tlatex.SetTextAlign(12)
        tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.85,"Reference PDF: "+self.truePdfTitle)
        tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.75,"Alternate PDF: "+self.pdfAltTitleMap[pdfAltName])
        tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.68,"m_{H} = "+str(hmass)+" GeV/c^{2}")
        tlatex.SetTextAlign(32)
        tlatex.DrawLatex(0.99-gStyle.GetPadRightMargin(),0.96,caption)
        line = self.setYMaxAndDrawVertLines(hist,median(self.data[hmass][pdfAltName]['pull']))
        canvas.RedrawAxis()
        saveAs(canvas,outputPrefix+self.catName+"_"+str(hmass)+"_"+pdfAltName)
        canvas.Clear()

    for pdfAltName in self.pdfAltNameList:
      minx = 115
      maxx = 155
      axisHist = root.TH2F("axishist"+str(iHist),"",1,minx,maxx,1,-1,1)
      setHistTitles(axisHist,"M_{H} [GeV/c^{2}]","Median[(N_{sig}(Alt)-N_{sig}(Ref))/#DeltaN_{sig}(Alt)]")
      graph = root.TGraph()
      graphBand = root.TGraphErrors()
      graphBand.SetPoint(0,minx,0.)
      graphBand.SetPointError(0,0.,0.14)
      graphBand.SetPoint(1,maxx,0.)
      graphBand.SetPointError(1,0.,0.14)
      graphBand.SetFillStyle(1)
      graphBand.SetFillColor(root.kGreen-9)
      iHist += 1
      iGraph = 0
      for hmass in self.sigMasses:
        medianPull = median(self.data[hmass][pdfAltName]['pull'])
        graph.SetPoint(iGraph,hmass,medianPull)
        iGraph += 1
      axisHist.Draw()
      graphBand.Draw("3")
      graph.Draw("LP")
      tlatex.SetTextAlign(12)
      tlatex.DrawLatex(gStyle.GetPadLeftMargin(),0.96,PRELIMINARYSTRING)
      tlatex.SetTextAlign(12)
      tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.85,"Reference PDF: "+self.truePdfTitle)
      tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.75,"Alternate PDF: "+self.pdfAltTitleMap[pdfAltName])
      tlatex.SetTextAlign(32)
      tlatex.DrawLatex(0.99-gStyle.GetPadRightMargin(),0.96,caption)
      canvas.RedrawAxis()
      saveAs(canvas,outputPrefix+self.catName+"_"+pdfAltName)
      canvas.Clear()

  def setYMaxAndDrawVertLines(self,hist,x):
    ymax = 0.
    for i in range(1,hist.GetXaxis().GetNbins()+1):
      ymax = max(ymax,hist.GetBinContent(i))
    ymax * 1.5
    hist.GetYaxis().SetRangeUser(0.,ymax*1.5)
    line = root.TLine()
    line.SetLineColor(root.kRed)
    line.SetLineWidth(3)
    line.DrawLine(x,0,x,ymax*1.05)
    return line

if __name__ == "__main__":
  outDir = "output/"

  categories = []

  jet2PtCuts = " && jetLead_pt > 40. && jetSub_pt > 30. && ptMiss < 40."
  jet01PtCuts = " && !(jetLead_pt > 40. && jetSub_pt > 30. && ptMiss < 40.)"

  #categories += [["Jets01PassPtG10BB",  "dimuonPt>10." +jet01PtCuts]]
  #categories += [["Jets01PassPtG10BO",  "dimuonPt>10." +jet01PtCuts]]
  #categories += [["Jets01PassPtG10"+x,  "dimuonPt>10." +jet01PtCuts] for x in categoriesAll]
  #categories += [["Jets01FailPtG10"+x,"!(dimuonPt>10.)"+jet01PtCuts] for x in categoriesAll]
  #categories += [["Jet2CutsVBFPass","deltaEtaJets>3.5 && dijetMass>650."+jet2PtCuts]]
  categories += [["Jet2CutsGFPass","!(deltaEtaJets>3.5 && dijetMass>650.) && (dijetMass>250. && dimuonPt>50.)"+jet2PtCuts]]
  categories += [["Jet2CutsFailVBFGF","!(deltaEtaJets>3.5 && dijetMass>650.) && !(dijetMass>250. && dimuonPt>50.)"+jet2PtCuts]]

  dataDir = "/data/uftrig01b/jhugon/hmumu/analysisV00-01-10/forGPReRecoMuScleFit/"
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

  logFile = open(outDir+"biasStudy.log",'w')
  now = datetime.datetime.now().replace(microsecond=0).isoformat(' ')
  logFile.write("# {0}\n\n".format(now))
  inputPklFiles = glob.glob(outDir+"*.pkl")
  if len(inputPklFiles)>0:
    for inputPkl in inputPklFiles:
      bs = BiasStudy(None,None,None,None,inputPkl=inputPkl)
      logFile.write(bs.outStr)
      bs.plot(outDir+"bias_")
  else:
    for category in categories:
      bs = BiasStudy(category,dataFns8TeV,"8TeV",100)
      logFile.write(bs.outStr)
      bs.plot(outDir+"bias_")
    
  now = datetime.datetime.now().replace(microsecond=0).isoformat(' ')
  logFile.write("\n\n# {0}\n".format(now))
  logFile.close()
  
