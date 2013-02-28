#!/usr/bin/env python


import argparse
parser = argparse.ArgumentParser(description="Makes Shape Diagnostic Plots from Datacards")
parser.add_argument("--signalInject", help="Sets a caption saying that signal was injected with strength",type=float,default=0.0)
parser.add_argument("--plotSignalStrength", help="Plots a signal bump with this strength",type=float,default=10.0)
parser.add_argument("--plotSignalBottom", help="Plots a signal bump with this strength",action="store_true",default=False)
parser.add_argument("--signalInjectMass", help="Mass For Injected Signal",type=float,default=125.0)
args = parser.parse_args()

from helpers import *
from xsec import *
import math
import os.path
import glob
import random

from ROOT import gSystem
gSystem.Load('libRooFit')

root.gErrorIgnoreLevel = root.kWarning
root.gROOT.SetBatch(True)
root.gStyle.SetOptStat(0)

#root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.WARNING)
root.RooMsgService.instance().setGlobalKillBelow(root.RooFit.ERROR)
PRINTLEVEL = root.RooFit.PrintLevel(-1) #For MINUIT

def convertErrors(hist):
  nBinsX = hist.GetNbinsX()
  for i in range(0,nBinsX+2):
    x = hist.GetBinContent(i)
    hist.SetBinError(i,math.sqrt(x))

def findMaxInRange(dataHist,xName,minX,maxX):
  result = 0.0
  for i in range(dataHist.numEntries()):
    argSet = dataHist.get(i)
    xVar = argSet.find(xName)
    x = xVar.getVal()
    if x>maxX or x<minX:
        continue
    y = dataHist.weight()
    if y>result:
      result = y
  return result

def getGraphIntegral(graph):
  X = root.Double()
  Y = root.Double()
  result = 0.0
  for i in range(graph.GetN()):
    graph.GetPoint(i,X,Y)
    result += float(Y)
  return result

class ShapePlotter:
  def __init__(self,filename,outDir,titleMap,rebin=1,doSignalScaling=True,xlimits=[],normRange=[],signalInject=0.0,plotSignalStrength=8.0,plotSignalBottom=False):
    self.plotSignalBottom=plotSignalBottom
    self.signalInject=signalInject
    self.plotSignalStrength=plotSignalStrength
    self.histList = []
    self.padList = []
    self.pullsList = []
    self.legList = []
    self.modelLines = []
    self.signalNormParamList = []
    self.signalPlusBakGraphList = []
    self.titleMap = titleMap
    self.filename = filename
    self.xlimits = xlimits
    self.normRange = normRange
    self.textFileName = os.path.splitext(filename)[0]+".txt"
    self.processNameMap, self.params, self.normErrMap = getattr(self,"readCard")(self.textFileName)
    self.colors = [root.kRed-9, root.kGreen-9, root.kBlue-9, root.kMagenta-9, root.kCyan-9]
    self.fillStyles = [3004,3005,3003,3006,3007]
    self.pullType = "adrian1"
    #self.pullType = "ratio"
    self.pullType = "pullMC"

    self.canvas = root.TCanvas()

    self.lumi = -1
    self.lumiStr = ""
    self.energyStr = ""
    tmpMatch = re.search(r"([\w]*)_(.+)_([.0-9]+)\.root",filename)
    if tmpMatch:
      self.lumi = float(tmpMatch.group(3))
      self.lumiStr = "L = {0:.1f} fb^{{-1}}".format(self.lumi)
      self.energyStr = tmpMatch.group(2)

    self.data = {}
    self.f = root.TFile(filename)
    for channelKey in self.f.GetListOfKeys():
      if channelKey.GetClassName() != "RooWorkspace":
        continue
      channelNameOrig = channelKey.GetName()
      channelName = re.sub("[\d]+TeV","",channelNameOrig)
      channelWS = channelKey.ReadObj()
      mMuMu = channelWS.var("mMuMu")
      mMuMu.setRange("makeShapePlotRange",self.xlimits[0],self.xlimits[1])
      mMuMu.setRange("makeShapeNormRange",self.normRange[0],self.normRange[3])
      mMuMu.setRange("makeShapeNormRange1",self.normRange[0],self.normRange[1])
      mMuMu.setRange("makeShapeNormRange2",self.normRange[2],self.normRange[3])
      mMuMu.setRange("makeShapeSignalRange",110.,140.)
      bakPDF = channelWS.pdf("bak")
      data_obs = channelWS.data("data_obs")
      rooDataTitle = data_obs.GetTitle()
      tmpRebin = rebin
      if "VBF" in channelName:
        if "BDT" in channelName:
          if self.energyStr == "7TeV":
            tmpRebin *= 5
          else:
            tmpRebin *= 5
        else:
          tmpRebin *= 5
      elif "BO" in channelName:
          tmpRebin *= 4
      elif "BE" in channelName:
          tmpRebin *= 5
      elif "OO" in channelName:
          tmpRebin *= 5
      elif "OE" in channelName:
          tmpRebin *= 5
      elif "EE" in channelName:
          tmpRebin *= 5
      elif "BB" in channelName:
        if self.energyStr == "7TeV":
          tmpRebin *= 4
        else:
          tmpRebin *= 2
      else:
          tmpRebin *= 2
      if tmpRebin != 1:
        realName = data_obs.GetName()
        data_obs.SetName(realName+str(random.randint(0,1000)))
        tmpHist = data_obs.createHistogram("mMuMu")
        tmpHist.Rebin(tmpRebin)
        data_obs =  root.RooDataHist(realName,data_obs.GetTitle(),
                                                            root.RooArgList(mMuMu),tmpHist)
      #Data Time

      sigGraph = None
      dataGraph, bakPDFGraph, sigPlusBakPDFGraph, sigPDFGraph, pullsGraph,chi2,sigCount = getattr(self,"makeMainTGraphs")(bakPDF,data_obs,mMuMu,
                                        channelWS,
                                        self.processNameMap[channelNameOrig],
                                        channelName
                                                    )
      if plotSignalStrength>0.:
        sigGraph, bestFitSigStr = getattr(self,"scaleSigPDFGraph")(sigPDFGraph,sigCount,self.processNameMap[channelNameOrig],plotSignalStrength)
      sigGraph = sigPlusBakPDFGraph
      pullsDistribution = getattr(self,"draw")(channelName,dataGraph,bakPDFGraph,pullsGraph,chi2,rooDataTitle,sigGraph)
      saveName = outDir+os.path.splitext(os.path.split(self.filename)[1])[0]+'_'+channelName
      saveName = re.sub(r"([\d]+)\.[\d]+",r"\1",saveName)
      saveAs(self.canvas,saveName)

      getattr(self,"drawPulls")(channelName,pullsDistribution,rooDataTitle)
      saveName = outDir+"pulls_"+os.path.splitext(os.path.split(self.filename)[1])[0]+'_'+channelName
      saveName = re.sub(r"([\d]+)\.[\d]+",r"\1",saveName)
      saveAs(self.canvas,saveName)
      """

      #Templates Time
      for processName in self.processNameMap[channelNameOrig]:
        template = channelWS.data(processName+"_Template")
        rooDataTitle = template.GetTitle()
        if tmpRebin != 1:
            realName = template.GetName()
            template.SetName(realName+str(random.randint(0,1000)))
            tmpHist = template.createHistogram("mMuMu")
            tmpHist.Rebin(tmpRebin)
            template =  root.RooDataHist(realName,template.GetTitle(),
                                                            root.RooArgList(mMuMu),tmpHist)
        pdf = channelWS.pdf(processName)
        dataGraph, pdfGraph, pullsGraph,chi2 = getattr(self,"makeTGraphs")(pdf,template,mMuMu)
        pullsDistribution = getattr(self,"draw")(channelName,dataGraph,pdfGraph,pullsGraph,chi2,rooDataTitle)
        saveName=outDir+os.path.splitext(os.path.split(self.filename)[1])[0]+'_'+channelName+"_"+processName
        saveName = re.sub(r"([\d]+)\.[\d]+",r"\1",saveName)
        saveAs(self.canvas,saveName)
      """

  def readCard(self,fn):
    f = open(fn)
    foundBin = False
    binList = []
    processList = []
    rateList = []
    paramMap = {}
    normErrMap = {}
    for line in f:
      if re.search("^bin",line):
        if foundBin:
          m =  re.findall("[\s]+[\w]+",line)
          binList.extend([i for i in m])
        else:
          foundBin = True
      if re.search("^process[\s]+[a-zA-Z]+",line):
          m =  re.findall("[\s]+[\w]+",line)
          processList.extend([i for i in m])
      if re.search("^rate[\s]+[-+eE.0-9]+",line):
          m =  re.findall("[\s]+[-+eE.0-9]+",line)
          rateList.extend([float(i) for i in m])
      paramMatch = re.search(r"([a-zA-Z0-9_]+)[\s]+param[\s]+([-.+eE0-9]+)[\s]+([-.+eE0-9]+)",line)
      if paramMatch:
        gs = paramMatch.groups()
        paramMap[gs[0]] = [gs[1],gs[2]]
      normMatch = re.search(r"bkN([a-zA-Z0-9_]+)[\s]+gmN[\s]+([-.+eE0-9]+)[\s-]+([.0-9]+)[\s-]+",line)
      if normMatch:
        gs = normMatch.groups()
        normErrMap[gs[0]] = 1.0/sqrt(float(gs[1]))
    binList = [x.replace(r" ","") for x in binList]
    processList = [x.replace(r" ","") for x in processList]
    result = {}
    for i in binList:
      if not result.has_key(i):
        result[i] = {}
    for b,p,r in zip(binList,processList,rateList):
      result[b][p] = r
    return result, paramMap, normErrMap

  def getRatioGraph(self,hist,curve):
    def findI(graph,x):
      xList = []
      X = root.Double()
      Y = root.Double()
      for i in range(graph.GetN()):
        graph.GetPoint(i,X,Y)
        xList.append(abs(float(X)-float(x)))
      bestI = min(range(len(xList)), key=lambda i: xList[i])
      if xList[bestI]>1.0:
        return -1
      return bestI
    ratioPlot = root.TGraphAsymmErrors()
    histX = root.Double()
    histY = root.Double()
    curveX = root.Double()
    curveY = root.Double()
    for i in range(hist.GetN()):
      hist.GetPoint(i,histX,histY)
      curveI = findI(curve,histX)
      if curveI < 0:
        continue
      curve.GetPoint(curveI,curveX,curveY)
      ratio = 0.0
      ratioErrUp = 0.0
      ratioErrDown = 0.0
      if curveY != 0.0 and histY != 0.0:
        histYErrUp = hist.GetErrorYhigh(i)
        histYErrDown = hist.GetErrorYlow(i)
        ratio = histY/curveY
        ratioErrUp = histYErrUp/curveY
        ratioErrDown = histYErrDown/curveY
        #if "bak" in curve.GetName():
          #print("hx: {:<10.1f} cx: {:<10.1f} hy: {:<10.1f} cy: {:<10.1f} ratio: {:<10.3f} hyErrUp: {:<10.1f}".format(histX,curveX,histY,curveY,ratio,hist.GetErrorYhigh(i)))
          #print("{:<5.1f}: hx: {:<10.1f} cx: {:<10.1f} ratio: {:<10.3f}".format(histX,histX,curveX,ratio))
          #print("{:<5.1f}: h: {:<10.1f} c: {:<10.1f} ratio: {:<10.3f}".format(histX,histY,curveY,ratio))
      else:
        continue
      ratioPlot.SetPoint(i,histX,ratio)
      ratioPlot.SetPointError(i,0.,0.,ratioErrDown,ratioErrUp)
    return ratioPlot

  def getAdrian1Errors(self,hist,curve):
    def findI(graph,x):
      xList = []
      X = root.Double()
      Y = root.Double()
      for i in range(graph.GetN()):
        graph.GetPoint(i,X,Y)
        xList.append(abs(float(X)-float(x)))
      bestI = min(range(len(xList)), key=lambda i: xList[i])
      if xList[bestI]>1.0:
        return -1
      return bestI
    ratioPlot = root.TGraph()
    histX = root.Double()
    histY = root.Double()
    curveX = root.Double()
    curveY = root.Double()
    for i in range(hist.GetN()):
      hist.GetPoint(i,histX,histY)
      curveI = findI(curve,histX)
      if curveI < 0:
        continue
      curve.GetPoint(curveI,curveX,curveY)
      ratio = 0.0
      if  histY != 0.0:
        ratio = (histY-curveY)/histY
      ratioPlot.SetPoint(i,histX,ratio)
    return ratioPlot

  def getPullErrors(self,hist,curve,doMCErr=False):
    def findI(graph,x):
      xList = []
      X = root.Double()
      Y = root.Double()
      for i in range(graph.GetN()):
        graph.GetPoint(i,X,Y)
        xList.append(abs(float(X)-float(x)))
      bestI = min(range(len(xList)), key=lambda i: xList[i])
      if xList[bestI]>1.0:
        return -1
      return bestI
    ratioPlot = root.TGraph()
    histX = root.Double()
    histY = root.Double()
    curveX = root.Double()
    curveY = root.Double()
    for i in range(hist.GetN()):
      hist.GetPoint(i,histX,histY)
      curveI = findI(curve,histX)
      if curveI < 0:
        continue
      curve.GetPoint(curveI,curveX,curveY)
      ratio = 0.0
      err = sqrt(histY)
      errMC = sqrt(curveY)
      if doMCErr:
        if  errMC == 0.0:
          continue
        ratio = (histY-curveY)/errMC
      else:
        if  err == 0.0:
          continue
        ratio = (histY-curveY)/err
      ratioPlot.SetPoint(i,histX,ratio)
    return ratioPlot

  def makePullDistribution(self,hist,curve):
    def findI(graph,x):
      xList = []
      X = root.Double()
      Y = root.Double()
      for i in range(graph.GetN()):
        graph.GetPoint(i,X,Y)
        xList.append(abs(float(X)-float(x)))
      bestI = min(range(len(xList)), key=lambda i: xList[i])
      if xList[bestI]>1.0:
        return -1
      return bestI
    ratioPlot = root.TH1F(hist.GetName()+"_pullDist","",20,-5.0,5.0)
    ratioPlot.Sumw2()
    ratioPlot.SetLineColor(1)
    ratioPlot.SetMarkerColor(1)
    histX = root.Double()
    histY = root.Double()
    curveX = root.Double()
    curveY = root.Double()
    for i in range(hist.GetN()):
      histYErrUp = hist.GetErrorYhigh(i)
      histYErrDown = hist.GetErrorYlow(i)
      assert(histYErrDown==histYErrUp)
      hist.GetPoint(i,histX,histY)
      curveI = findI(curve,histX)
      curve.GetPoint(curveI,curveX,curveY)
      ratio = 0.0
      if  histY != 0.0:
        ratio = (histY-curveY)/histYErrUp
      ratioPlot.Fill(ratio)
    return ratioPlot

  def makeTGraphs(self,pdf,data,observable):
    avgWeight = 1.0
    isRealData = (data.GetTitle() == "Real Observed Data")
    if (not isRealData) and (data.GetName() == "data_obs" or "bak" in data.GetName()):
      for i in backgroundList:
        if "DY" in i:
          datasetName = i + "_" + self.energyStr
          avgWeight = self.lumi*1000.0*xsec[datasetName]/nEventsMap[datasetName]
    frame = None
    if len(self.xlimits) == 2:
      frame = observable.frame(root.RooFit.Range(*self.xlimits))
    else:
      frame = observable.frame()
    pdfParams = pdf.getParameters(data)
    itr = pdfParams.createIterator()
    curveNomName = pdf.GetName()+"_CurveNom"
    curveDataName = data.GetName()+"_Curve"
    rng = root.RooFit.Range("makeShapePlotRange")
    normRange = root.RooFit.NormRange("makeShapeNormRange")
    if "Hmumu125" in data.GetName():
      rng = root.RooFit.Range("makeShapeSignalRange")
    data.plotOn(frame,root.RooFit.Name(curveDataName))
    pdf.plotOn(frame,root.RooFit.Name(curveNomName),rng,normRange)
    pulls = frame.pullHist(curveDataName,curveNomName)
    nparams = pdf.getParameters(data).getSize()
    #nparams = 0
    chi2 = frame.chiSquare(nparams)
    curveNames = []
    for iParam in range(pdfParams.getSize()):
      param = itr.Next()
      paramName = param.GetName()
      if self.params.has_key(paramName):
        nominal,err = self.params[paramName]
        nominal = float(nominal)
        err = float(err)
        tmpName = pdf.GetName()+"_Curve{0}p".format(iParam)
        param.setVal(nominal+err)
        pdf.plotOn(frame,root.RooFit.Name(tmpName),rng,normRange)
        curveNames.append(tmpName)
        tmpName = pdf.GetName()+"_Curve{0}m".format(iParam)
        param.setVal(nominal-err)
        pdf.plotOn(frame,root.RooFit.Name(tmpName),rng,normRange)
        curveNames.append(tmpName)
    # Norm uncertainty
    normErr = None
    if data.GetName() == "data_obs" or "bak" in data.GetName():
      pdfParams = pdf.getParameters(data)
      itr = pdfParams.createIterator()
      param = itr.Next()
      paramName = param.GetName()
      match = re.match(r"([a-zA-Z0-9]+)_.*",paramName)
      if match:
        channelName = match.group(1)
        normErr = self.normErrMap[channelName]
      else:
        print "Warning: norm uncertainty string match failed"
    varUp = []
    varDown = []
    for curveName in curveNames:
      curve = frame.findObject(curveName)
      if curveName[len(curveName)-1]=='p':
        varUp.append(curve)
      else:
        varDown.append(curve)
    curveNom = frame.findObject(curveNomName)
    curveData = frame.findObject(curveDataName)
    modelGraph = root.TGraphAsymmErrors()
    dataGraph = root.TGraphAsymmErrors()
    pullsGraph = root.TGraphAsymmErrors()
    iPoint = 0
    xNom = root.Double()
    yNom = root.Double()
    xErr = root.Double()
    yErr = root.Double()
    for i in range(curveNom.GetN()):
      curveNom.GetPoint(i,xNom,yNom)
      errUp = 0.0
      errDown = 0.0
      badPoint = False
      for errCurve in varUp:
        iErr = errCurve.findPoint(xNom,1.0)
        if iErr < 0:
          badPoint = True
        errCurve.GetPoint(iErr,xErr,yErr)
        errUp += (yErr-float(yNom))**2
      for errCurve in varDown:
        iErr = errCurve.findPoint(xNom,1.0)
        if iErr < 0:
          badPoint = True
        errCurve.GetPoint(iErr,xErr,yErr)
        errDown += (yErr-float(yNom))**2
      if badPoint:
        continue
      errUp = sqrt(errUp)
      errDown = sqrt(errDown)
      modelGraph.SetPoint(iPoint,xNom,yNom)
      modelGraph.SetPointError(iPoint,0.,0.,errDown,errUp)
      iPoint+=1
    iPoint = 0
    for i in range(curveData.GetN()):
      curveData.GetPoint(i,xNom,yNom)
      if yNom <=0.0:
        continue
      dataGraph.SetPoint(iPoint,xNom,yNom)
      errUp = sqrt(yNom)*sqrt(avgWeight)
      errDown = sqrt(yNom)*sqrt(avgWeight)
      dataGraph.SetPointError(iPoint,0.,0.,errDown,errUp)
      iPoint+=1
    iPoint = 0
    for i in range(pulls.GetN()):
      pulls.GetPoint(i,xNom,yNom)
      pullsGraph.SetPoint(iPoint,xNom,yNom)
      errUp = pulls.GetErrorXhigh(i)
      errDown = pulls.GetErrorXlow(i)
      pullsGraph.SetPointError(iPoint,0.,0.,errDown,errUp)
      iPoint+=1
    dataGraph.SetName(curveData.GetName()+"_TGraph")
    modelGraph.SetName(curveNom.GetName()+"_TGraph")
    pullsGraph.SetName(curveData.GetName()+"_pullsTGraph")
    dataGraph.SetMarkerColor(1)
    modelGraph.SetLineColor(root.kBlue+1)
    modelGraph.SetFillColor(root.kCyan)
    modelGraph.SetFillStyle(1)
    return dataGraph, modelGraph, pullsGraph, chi2

  def drawPulls(self,channelName,pulls,rooDataTitle):
    self.canvas.Clear()
    self.canvas.cd()

    binWidth = getBinWidthStr(pulls)

    dataLabel = "FullSim MC"
    if rooDataTitle == "Toy Data":
      dataLabel = "Toy MC"
    elif rooDataTitle == "Real Observed Data":
      dataLabel = "Data"

    xtitle = "({0}-Fit)/#sigma_{{{0}}}".format(dataLabel)
    ytitle = "Events/{0}".format(binWidth)
    pulls.GetXaxis().SetTitle(xtitle)
    pulls.GetYaxis().SetTitle(ytitle)
    pulls.Draw()

    fitFunc = root.TF1(pulls.GetName()+"_fitFunc","gaus",
                                pulls.GetXaxis().GetXmin(),pulls.GetXaxis().GetXmax())
    fitFunc.SetLineColor(root.kBlue)
    fitResult = pulls.Fit(fitFunc,"LEMSQ")
    chi2 = fitFunc.GetChisquare()
    ndf = fitFunc.GetNDF()
    #print("chi2: {0:.2g}/{1}".format(chi2,ndf))
    #nParams =  fitFunc.GetNumberFreeParameters()
    #for i in range(nParams):
    #    parName = fitFunc.GetParName(i)
    #    val = fitFunc.GetParameter(i)
    #    err = fitFunc.GetParError(i)
    #    print("name: {}, value: {}, error: {}".format(parName,val,err))

    mean = fitFunc.GetParameter(1)
    meanErr = fitFunc.GetParError(1)
    sigma = fitFunc.GetParameter(2)
    sigmaErr = fitFunc.GetParError(2)

    tlatex = root.TLatex()
    tlatex.SetNDC()
    tlatex.SetTextFont(root.gStyle.GetLabelFont())
    tlatex.SetTextSize(root.gStyle.GetLabelSize())
    tlatex.SetTextAlign(12)
    tlatex.DrawLatex(gStyle.GetPadLeftMargin(),0.96,PRELIMINARYSTRING)
    tlatex.SetTextAlign(32)
    tlatex.DrawLatex(1.0-gStyle.GetPadRightMargin(),0.96,self.titleMap[channelName])
    tlatex.DrawLatex(0.98-gStyle.GetPadRightMargin(),0.875,"#sqrt{s}="+self.energyStr)
    tlatex.DrawLatex(0.98-gStyle.GetPadRightMargin(),0.825,self.lumiStr)
    tlatex.SetTextAlign(12)
    tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.875,"#chi^{{2}}/NDF = {0:.2g}".format(float(chi2)/ndf))
    tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.825,"#mu = {0:.2f} #pm {1:.2f}".format(mean,meanErr))
    tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.775,"#sigma = {0:.2f} #pm {1:.2f}".format(sigma,sigmaErr))

  def draw(self,channelName,data,model,pulls,chi2,rooDataTitle,sigPlusBakPDF=None):
      drawXLimits = self.xlimits
      isSignalMC = False
      pullType = self.pullType
      if "Hmumu125" in data.GetName():
        drawXLimits = [110.,140.]
      if "Hmumu" in data.GetName():
        isSignalMC=True
      def getMaxYVal(self,graph):
        l = []
        x = root.Double()
        y = root.Double()
        for i in range(graph.GetN()):
          graph.GetPoint(i,x,y)
          if x < drawXLimits[0]:
                continue
          if x > drawXLimits[1]:
                continue
          l.append(float(y))
        if len(l) == 0:
            return -1.0
        return max(l)
      def copyGraphNoErrs(graph,outGraph):
        x = root.Double()
        y = root.Double()
        for i in range(graph.GetN()):
          graph.GetPoint(i,x,y)
          outGraph.SetPoint(i,x,y)
        outGraph.SetLineColor(graph.GetLineColor())
        outGraph.SetLineStyle(graph.GetLineStyle())
        outGraph.SetLineWidth(graph.GetLineWidth())
        outGraph.SetMarkerColor(graph.GetMarkerColor())
        outGraph.SetMarkerStyle(graph.GetMarkerStyle())
        outGraph.SetMarkerSize(graph.GetMarkerSize())
        self.modelLines.append(outGraph)
      def makeRatioModelPlots(graph,outRatio,outOne):
        for i in range(graph.GetN()):
          x = root.Double()
          y = root.Double()
          graph.GetPoint(i,x,y)
          outOne.SetPoint(i,x,1.0)
          outRatio.SetPoint(i,x,1.0)
          if y == 0.0:
            continue
          errUp = graph.GetErrorYhigh(i)
          errDown = graph.GetErrorYlow(i)
          outRatio.SetPointError(i,0.,0.,errDown/float(y),errUp/float(y))
        outOne.SetLineColor(graph.GetLineColor())
        outOne.SetLineStyle(graph.GetLineStyle())
        outOne.SetLineWidth(graph.GetLineWidth())
        outRatio.SetFillColor(graph.GetFillColor())
        outRatio.SetFillStyle(graph.GetFillStyle())
        self.modelLines.append(outOne)
        self.modelLines.append(outRatio)
      def makePullPlots(graph,outRatio,outOne):
        for i in range(graph.GetN()):
          x = root.Double()
          y = root.Double()
          graph.GetPoint(i,x,y)
          outOne.SetPoint(i,x,1.0)
          outRatio.SetPoint(i,x,1.0)
          if y == 0.0:
            continue
          errUp = graph.GetErrorYhigh(i)
          errDown = graph.GetErrorYlow(i)
          outRatio.SetPointError(i,0.,0.,errDown/float(y),errUp/float(y))
        outOne.SetLineColor(graph.GetLineColor())
        outOne.SetLineStyle(graph.GetLineStyle())
        outOne.SetLineWidth(graph.GetLineWidth())
        outRatio.SetFillColor(graph.GetFillColor())
        outRatio.SetFillStyle(graph.GetFillStyle())
        self.modelLines.append(outOne)
        self.modelLines.append(outRatio)
      def getHistArgsFromGraph(graph,drawXLimits):
        if graph.GetN() < 2:
          return graph.GetName(),graph.GetTitle(),100,drawXLimits[0],drawXLimits[1]
        diffs = []
        x = root.Double()
        y = root.Double()
        for i in range(graph.GetN()-1):
          graph.GetPoint(i,x,y)
          x1 = float(x)
          graph.GetPoint(i+1,x,y)
          x2 = float(x)
          diffs.append(x2-x1)
        #return max(set(diffs), key=diffs.count)
        nBins = int((drawXLimits[1]-drawXLimits[0])/min(diffs))
        return graph.GetName()+str(random.randint(0,10000)),graph.GetTitle(),nBins,drawXLimits[0],drawXLimits[1]
      def getHistFromGraph(graph,hist):
        x = root.Double()
        y = root.Double()
        for i in range(graph.GetN()-1):
          graph.GetPoint(i,x,y)
          yErr = graph.GetErrorYhigh(i)
          iBin = hist.GetXaxis().FindBin(x)
          hist.SetBinContent(iBin,y)
          hist.SetBinError(iBin,yErr)
        hist.SetMarkerColor(1)
        hist.SetLineColor(1)

      dataHist = root.TH1F(*getHistArgsFromGraph(data,drawXLimits))
      self.histList.append(dataHist)
      pullHist = root.TH1F(*getHistArgsFromGraph(data,drawXLimits))
      self.histList.append(pullHist)

      getHistFromGraph(data,dataHist)
      binWidth = getBinWidthStr(dataHist)

      maxVal = getMaxYVal(self,data)
      maxVal = max(getMaxYVal(self,model),maxVal)
      dataLabel = "FullSim MC"
      if rooDataTitle == "Toy Data":
        dataLabel = "Toy MC"
      elif rooDataTitle == "Real Observed Data":
        dataLabel = "Data"

      #Setup Canvas
      self.canvas.cd()
      self.canvas.Clear()
      self.canvas.SetLogy(0)
      pad1 = root.TPad("pad1"+data.GetName(),"",0.02,0.30,0.98,0.98,0)
      pad2 = root.TPad("pad2"+data.GetName(),"",0.02,0.01,0.98,0.29,0)
    
      pad1.SetBottomMargin(0.005);
      pad2.SetTopMargin   (0.005);
      pad2.SetBottomMargin(0.33);
      pad2.SetLogy(0)
      pad1.SetLogy(0)
    
      pad1.Draw() # Projections pad
      pad2.Draw() # Residuals   pad
  
      pad1Width = pad1.XtoPixel(pad1.GetX2())
      pad1Height = pad1.YtoPixel(pad1.GetY1())
      pad2Height = pad2.YtoPixel(pad2.GetY1())
      pad1ToPad2FontScalingFactor = float(pad1Height)/pad2Height
      canvasToPad1FontScalingFactor = float(self.canvas.YtoPixel(self.canvas.GetY1()))/pad1.YtoPixel(pad1.GetY1())
      canvasToPad2FontScalingFactor = float(self.canvas.YtoPixel(self.canvas.GetY1()))/pad2.YtoPixel(pad2.GetY1())
    
      # Main Pad
      pad1.cd();
      dataHist.Draw("")
      dataHist.GetYaxis().SetTitle(("Events/{0} GeV/c^{{2}}").format(binWidth))
      dataHist.GetYaxis().SetTitleSize(gStyle.GetTitleSize("Y")*canvasToPad1FontScalingFactor)
      dataHist.GetYaxis().SetLabelSize(gStyle.GetLabelSize("Y")*canvasToPad1FontScalingFactor)
      dataHist.GetYaxis().SetTitleOffset(0.8*gStyle.GetTitleOffset("Y"))
      dataHist.GetXaxis().SetLabelOffset(0.70)
      dataHist.GetXaxis().SetTitle("m_{#mu#mu} [GeV/c^{2}]")
      #dataHist.GetXaxis().SetRangeUser(*drawXLimits)
      if maxVal != None:
        dataHist.GetYaxis().SetRangeUser(0.0,maxVal*1.05)
      modelLine = root.TGraph()
      copyGraphNoErrs(model,modelLine)
      model.Draw("3")
      model.SetFillStyle(1001)
      if sigPlusBakPDF != None:
        sigPlusBakPDF.Draw("l")
      modelLine.Draw("l")
      dataHist.Draw("same")
      pad1.Update()
      pad1.RedrawAxis() # Updates Axis Lines

      # Pulls Pad
      pad2.cd()

      ratioGraph = None
      if pullType == "adrian1":
        ratioGraph = self.getAdrian1Errors(data,model)
      elif pullType == "pullMC":
        ratioGraph = self.getPullErrors(data,model,True)
      elif pullType == "ratio":
        ratioGraph = self.getRatioGraph(data,model)
      else :
        ratioGraph = self.getPullErrors(data,model)
      self.pullsList.append(ratioGraph)
      pulls =  ratioGraph
      getHistFromGraph(pulls,pullHist)
      pullDistribution = self.makePullDistribution(data,model)
      if pullType != "ratio":
        pullHist.SetLineColor(root.kBlue)
        pullHist.SetLineStyle(1)
        pullHist.SetLineWidth(2)
        pullHist.SetFillColor(856)
        pullHist.SetFillStyle(1001)
      else:
        pullHist.SetLineStyle(1)
        pullHist.SetLineColor(1)
        pullHist.SetMarkerColor(1)
      if pullType == "adrian1":
        pullHist.GetYaxis().SetTitle("#frac{"+dataLabel+"-Fit}{"+dataLabel+"}")
        pullHist.GetYaxis().SetRangeUser(-1.5,1.5)
      else:
        pullHist.GetYaxis().SetTitle("#frac{"+dataLabel+"-Fit}{#sigma_{"+dataLabel+"}}")
        pullHist.GetYaxis().SetRangeUser(-5,5)
        if pullType=="ratio":
          pullHist.GetYaxis().SetTitle("#frac{"+dataLabel+"}{Fit}")
          pullHist.GetYaxis().SetRangeUser(0,2)
        elif pullType == "pullMC":
          pullHist.GetYaxis().SetTitle("#frac{"+dataLabel+"-Fit}{#sqrt{Fit}}")
      pullHist.SetTitle("")
      pullHist.GetXaxis().SetRangeUser(*drawXLimits)
      pullHist.GetXaxis().SetTitle("m_{#mu#mu} [GeV/c^{2}]")
      pullHist.GetXaxis().CenterTitle(1)
      pullHist.GetYaxis().SetNdivisions(5)
      pullHist.GetXaxis().SetTitleSize(0.055*pad1ToPad2FontScalingFactor)
      pullHist.GetXaxis().SetLabelSize(0.050*pad1ToPad2FontScalingFactor)
      pullHist.GetYaxis().SetTitleSize(0.045*pad1ToPad2FontScalingFactor)
      pullHist.GetYaxis().SetLabelSize(0.045*pad1ToPad2FontScalingFactor)
      pullHist.GetYaxis().CenterTitle(1)
      pullHist.GetXaxis().SetTitleOffset(0.75*pullHist.GetXaxis().GetTitleOffset())
      pullHist.GetYaxis().SetTitleOffset(0.65)

      pullHist.GetXaxis().SetLabelSize(gStyle.GetLabelSize("X")*canvasToPad2FontScalingFactor)

      if pullType=="ratio":
        pullHist.Draw("")
        modelRatio = root.TGraphAsymmErrors()
        modelOne = root.TGraphAsymmErrors()
        makeRatioModelPlots(model,modelRatio,modelOne)
        modelRatio.Draw("3")
        modelOne.Draw("l")
        pullHist.Draw("same")
      else:
        pullHist.Draw("hist")


      ## Pretty Stuff
  
      normchi2 = chi2
      problatex = root.TLatex()
      problatex.SetNDC()
      problatex.SetTextFont(dataHist.GetXaxis().GetLabelFont())
      problatex.SetTextSize(pullHist.GetYaxis().GetLabelSize())
      problatex.SetTextAlign(12)
      problatex.DrawLatex(0.18,0.41,"#chi^{{2}}/NDF: {0:.3g}".format(normchi2))
  
      pad2.Update()
      pad2.RedrawAxis() # Updates Axis Lines
    
      pad1.cd()

      legPos = [0.65,0.65,1.0-gStyle.GetPadRightMargin()-0.01,1.0-gStyle.GetPadTopMargin()-0.01]
      leg = root.TLegend(*legPos)
      leg.SetFillColor(0)
      leg.SetLineColor(0)
      leg.AddEntry(dataHist,dataLabel,"pe")
      leg.AddEntry(model,"Fit","lf")
      if self.plotSignalStrength>0.0 and sigPlusBakPDF != None:
        leg.AddEntry(sigPlusBakPDF,"SM Higgs #times {0:.1f}".format(self.plotSignalStrength),"l")
      leg.Draw()

      tlatex = root.TLatex()
      tlatex.SetNDC()
      tlatex.SetTextFont(root.gStyle.GetLabelFont())
      #tlatex.SetTextSize(0.05)
      tlatex.SetTextSize(0.04*canvasToPad1FontScalingFactor)
      tlatex.SetTextAlign(12)
      tlatex.DrawLatex(gStyle.GetPadLeftMargin(),0.96,PRELIMINARYSTRING)
      tlatex.SetTextAlign(32)
      tlatex.DrawLatex(1.0-gStyle.GetPadRightMargin(),0.96,self.titleMap[channelName])
      if isSignalMC:
        tlatex.SetTextAlign(12)
        #tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.80,self.lumiStr)
        tlatex.DrawLatex(0.02+gStyle.GetPadLeftMargin(),0.875,"#sqrt{s}="+self.energyStr)
      else:
        tlatex.SetTextAlign(32)
        tlatex.DrawLatex(legPos[0]-0.01,0.820,self.lumiStr)
        tlatex.DrawLatex(legPos[0]-0.01,0.875,"#sqrt{s}="+self.energyStr)
        if self.signalInject>0.0:
          tlatex.SetTextColor(root.kRed)
          tlatex.DrawLatex(legPos[0]-0.01,0.760,"{0:.0f} #times SM Signal Injection ".format(self.signalInject))

      self.padList.extend([pad1,pad2])
      self.pullsList.append(pulls)
      self.legList.append(leg)

      return pullDistribution 

  def makeSigPlusBakPDF(self,workspace,mMuMu,data_obs,rateMap,r,rebin):
    if self.plotSignalBottom:
      multiplyFactor = 1000
      r = float(r)
      sigNames = []
      for i in rateMap:
        if i != "bak":
          sigNames.append(i)
      sigNames.sort()
      signalPDFs = [workspace.pdf(i) for i in sigNames]
      signalNs = [rateMap[i]*r for i in sigNames]
      signalNTotal = sum(signalNs)
      signalNormParams = []
      print signalNTotal
      for sigName, sigN in zip(sigNames,signalNs):
        signalNormParams.append(root.RooRealVar("normParam_"+sigName,"normParam_"+sigName,
                                              sigN
                                              )
                                  )
      addPDFList = []
      for name, norm, pdf in zip(sigNames, signalNormParams, signalPDFs):
        addPDFList.append(
                    root.RooExtendPdf(name+"ExtPDF",name+"ExtPDF",pdf,norm)
            )
      sigPlusBakPDF = root.RooAddPdf("sigPlusBakPDF","sigPlusBakPDF",
                                              root.RooArgList(*addPDFList)
                                            )
      data = sigPlusBakPDF.generate(root.RooArgSet(mMuMu),int(signalNTotal*multiplyFactor))
      print data.sumEntries()
      boundaries = getRooVarRange(mMuMu,"makeShapePlotRange")
      binningName = "sillyBinning"+str(random.randint(0,10000))
      binning = root.RooBinning(int(boundaries[1]-boundaries[0]),boundaries[0],boundaries[1],
                                            binningName)
      mMuMu.setBinning(binning)
      binWidth = 1.0
      
      print "bin widht", binWidth
      
      self.signalNormParamList += signalNormParams
  
      frame = None
      if len(self.xlimits) == 2:
        frame = mMuMu.frame(root.RooFit.Range(*self.xlimits))
      else:
        frame = mMuMu.frame()
      curveNomName = sigPlusBakPDF.GetName()+"_CurveNomSigPBak"
      curveDataName = data.GetName()+"_CurveSigPBak"
      rng = root.RooFit.Range("makeShapePlotRange")
      data.plotOn(frame,root.RooFit.Name(curveDataName),root.RooFit.Binning(binningName))
      sigPlusBakPDF.plotOn(frame,root.RooFit.Name(curveNomName),rng)
  
      for i, pdf in zip(range(6,10),signalPDFs):
        sigPlusBakPDF.plotOn(frame,root.RooFit.Components(pdf.GetName()),root.RooFit.LineColor(i))
      self.canvas.cd()
      frame.Draw()
      self.canvas.SaveAs("debug_SigPlusBakPDFs"+str(random.randint(0,100))+".png")
      frame.Print()
  
      curveNom = frame.findObject(curveNomName)
      modelGraph = root.TGraph()
      iPoint = 0
      xNom = root.Double()
      yNom = root.Double()
      for i in range(curveNom.GetN()):
        curveNom.GetPoint(i,xNom,yNom)
        yNom = root.Double(yNom/multiplyFactor*rebin/2.0)
        modelGraph.SetPoint(iPoint,xNom,yNom)
        iPoint+=1
      modelGraph.SetName(curveNom.GetName()+"_TGraph")
      modelGraph.SetLineColor(root.kRed)
      self.signalPlusBakGraphList.append(modelGraph)
  
      return modelGraph
    else:
      r = float(r)
      bakPDF = workspace.pdf("bak")
      bakN = rateMap['bak']
      sigNames = []
      for i in rateMap:
        if i != "bak":
          sigNames.append(i)
      sigNames.sort()
      signalPDFs = [workspace.pdf(i) for i in sigNames]
      signalNs = [rateMap[i]*r for i in sigNames]
      signalNTotal = sum(signalNs)
      allNTotal = bakN+signalNTotal
      signalNormParams = []
      for sigName, sigN in zip(sigNames,signalNs):
        signalNormParams.append(root.RooRealVar("normParam_"+sigName,"normParam_"+sigName,
                                              float(sigN)/allNTotal
                                              )
                                  )
      addPDFList = signalPDFs+[bakPDF]
      sigPlusBakPDF = root.RooAddPdf("sigPlusBakPDF","sigPlusBakPDF",
                                              root.RooArgList(*addPDFList),
                                              root.RooArgList(*signalNormParams))
      self.signalNormParamList += signalNormParams
  
      frame = None
      if len(self.xlimits) == 2:
        frame = mMuMu.frame(root.RooFit.Range(*self.xlimits))
      else:
        frame = mMuMu.frame()
      curveNomName = sigPlusBakPDF.GetName()+"_CurveNomSigPBak"
      curveDataName = data_obs.GetName()+"_CurveSigPBak"
      rng = root.RooFit.Range("makeShapePlotRange")
      normRange = root.RooFit.NormRange("makeShapeNormRange1,makeShapeNormRange2")
      data_obs.plotOn(frame,root.RooFit.Name(curveDataName))
      sigPlusBakPDF.plotOn(frame,root.RooFit.Name(curveNomName),rng,normRange)
  
  #    sigPlusBakPDF.plotOn(frame,root.RooFit.Components(bakPDF.GetName()),root.RooFit.LineColor(2))
  #    for i, pdf in zip(range(6,10),signalPDFs):
  #      sigPlusBakPDF.plotOn(frame,root.RooFit.Components(pdf.GetName()),root.RooFit.LineColor(i))
  #    self.canvas.cd()
  #    frame.Draw()
  #    self.canvas.SaveAs("debug_SigPlusBakPDFs"+str(random.randint(0,100))+".png")
  #    frame.Print()
  
      curveNom = frame.findObject(curveNomName)
      modelGraph = root.TGraph()
      iPoint = 0
      xNom = root.Double()
      yNom = root.Double()
      for i in range(curveNom.GetN()):
        curveNom.GetPoint(i,xNom,yNom)
        modelGraph.SetPoint(iPoint,xNom,yNom)
        iPoint+=1
      modelGraph.SetName(curveNom.GetName()+"_TGraph")
      modelGraph.SetLineColor(root.kRed)
      self.signalPlusBakGraphList.append(modelGraph)
  
      return modelGraph

  def makeMainTGraphs(self,bakPDF,data,observable,workspace,rateMap,channelName):
    nparamsForChi2 = bakPDF.getParameters(data).getSize()
    avgWeight = 1.0
    isRealData = (data.GetTitle() == "Real Observed Data")
    if (not isRealData) and (data.GetName() == "data_obs" or "bak" in data.GetName()):
      for i in backgroundList:
        if "DY" in i:
          datasetName = i + "_" + self.energyStr
          avgWeight = self.lumi*1000.0*xsec[datasetName]/nEventsMap[datasetName]

    plotRangeList = getRooVarRange(observable,"makeShapePlotRange")
    getPlotRangeString = "mMuMu > {0} && mMuMu < {1}".format(*plotRangeList)
    nData =  data.sumEntries(getPlotRangeString)
    wImport = getattr(workspace,"import")
    sigName = None
    vbfChannel = "VBF" in channelName
    for i in rateMap:
      if i != "bak":
        if vbfChannel and "vbf" in i:
          sigName = i
          break
        elif not vbfChannel and "gg" in i:
          sigName = i
          break
    sigPDF = workspace.pdf(sigName)

    bakStrength = root.RooRealVar("bakStrength","bakStrength",1.0,1e6)
    sigStrength = root.RooRealVar("sigStrength","sigStrength",0.0,1e6)
    epdfSig = root.RooExtendPdf("epdfSig","epdfSig",sigPDF,sigStrength)
    epdfBak = root.RooExtendPdf("epdfBak","epdfBak",bakPDF,bakStrength)
    pdfSB = root.RooAddPdf("pdfSB","Signal + Background",root.RooArgList(epdfBak,epdfSig))
    wImport(pdfSB)
  
    constraintPDFList = []
    constraintParamList = []
    pdfParams = bakPDF.getParameters(data)
    itr = pdfParams.createIterator()
    for iParam in range(pdfParams.getSize()):
      param = itr.Next()
      paramName = param.GetName()
      if self.params.has_key(paramName):
        nominal,err = self.params[paramName]
        nominal = float(nominal)
        err = float(err)
        meanVar = root.RooRealVar("ConstrainMean_"+paramName,"ConstrainMean_"+paramName,nominal)
        sigmaVar = root.RooRealVar("ConstrainSigma_"+paramName,"ConstrainSigma_"+paramName,err)
        constraintPDF = root.RooGaussian("ConstrainPDF_"+paramName,"ConstrainPDF_"+paramName,param,meanVar,sigmaVar)
        constraintParamList.append(meanVar)
        constraintParamList.append(sigmaVar)
        constraintPDFList.append(constraintPDF)
        wImport(meanVar)
        wImport(sigmaVar)
        wImport(constraintPDF)
        #print paramName,nominal,err
    pdfFinal = None
    if len(constraintPDFList)>0:
      constraintPDFList.append(pdfSB)
      pdfFinal = root.RooProdPdf("pdfSBConstraint",
              "Signal+Background * Constraints",
              root.RooArgList(*constraintPDFList)
              )
      wImport(pdfFinal)
    else:
      pdfFinal = pdfSB
  
    #frSB = pdfSB.fitTo(data,root.RooFit.SumW2Error(False),PRINTLEVEL,root.RooFit.Save(True))
    fr = pdfFinal.fitTo(data,root.RooFit.SumW2Error(False),PRINTLEVEL,root.RooFit.Save(True))

    rng = root.RooFit.Range("makeShapePlotRange")
    normRange = root.RooFit.NormRange("makeShapeNormRange")
    frame = None
    if len(self.xlimits) == 2:
      frame = observable.frame(root.RooFit.Range(*self.xlimits))
    else:
      frame = observable.frame()
    curveUpNames = []
    curveDownNames = []

    curveDataName = pdfFinal.GetName()+"_CurveData"
    data.plotOn(frame,root.RooFit.Name(curveDataName),rng)
    curveNomName = pdfFinal.GetName()+"_CurveNominal"
    pdfFinal.plotOn(frame,root.RooFit.Name(curveNomName),rng,normRange,root.RooFit.Components("epdfBak"))
    #nparamsForChi2 = pdfFinal.getParameters(data).getSize()
    #nparamsForChi2 -= len(constraintParamList)
    #nparamsForChi2 = epdfBak.getParameters(data).getSize()
    chi2 = frame.chiSquare(nparamsForChi2)
    pulls = frame.pullHist(curveDataName,curveNomName)

    curveNomPlusSigName = pdfFinal.GetName()+"_CurveNominalPlusSig"
    pdfFinal.plotOn(frame,root.RooFit.Name(curveNomPlusSigName),rng,normRange)
    curveSigName = pdfFinal.GetName()+"_CurveSig"
    pdfFinal.plotOn(frame,root.RooFit.Name(curveSigName),rng,normRange,root.RooFit.Components("epdfSig"))

    nParams = fr.floatParsFinal().getSize()
    for i in range(nParams):
      varyParamName = fr.floatParsFinal().at(i).GetName()
      for sign in [1.0,-1.0]:
        for j in range(nParams):
          param = fr.floatParsFinal().at(j)
          val = param.getVal()
          if i == j:
            val += sign*param.getError()
          workspace.var(param.GetName()).setVal(val)
        tmpName = pdfFinal.GetName()+"_Curve{0}p{1}_{2}".format(i,sign,varyParamName)
        pdfFinal.plotOn(frame,root.RooFit.Name(tmpName),rng,normRange,root.RooFit.Components("epdfBak"))
        if sign > 0.0:
          curveUpNames.append(tmpName)
        else:
          curveDownNames.append(tmpName)

    varUp = []
    varDown = []
    for nameUp,nameDown in zip(curveUpNames,curveDownNames):
      curveUp = frame.findObject(nameUp)
      curveDown = frame.findObject(nameDown)
      varUp.append(curveUp)
      varDown.append(curveDown)

    curveNom = frame.findObject(curveNomName)
    curveData = frame.findObject(curveDataName)
    modelGraph = root.TGraphAsymmErrors()
    dataGraph = root.TGraphAsymmErrors()
    pullsGraph = root.TGraphAsymmErrors()

    curveNomPlusSig = frame.findObject(curveNomPlusSigName)
    curveSig = frame.findObject(curveSigName)
    modelPlusSigGraph = root.TGraphAsymmErrors()
    sigGraph = root.TGraphAsymmErrors()

    iPoint = 0
    xNom = root.Double()
    yNom = root.Double()
    xErrUp = root.Double()
    yErrUp = root.Double()
    xErrDown = root.Double()
    yErrDown = root.Double()
    for i in range(curveNom.GetN()):
      curveNom.GetPoint(i,xNom,yNom)
      errUp = float(yNom)**2/nData
      errDown = float(yNom)**2/nData
      badPoint = False
      for errCurveUp,errCurveDown in zip(varUp,varDown):
        iErrUp = errCurveUp.findPoint(xNom,1.0)
        iErrDown = errCurveDown.findPoint(xNom,1.0)
        if iErrUp < 0 or iErrDown < 0:
          badPoint = True
        errCurveUp.GetPoint(iErrUp,xErrUp,yErrUp)
        errCurveDown.GetPoint(iErrDown,xErrDown,yErrDown)
        if yErrUp >= yErrDown and yErrUp > yNom:
          errUp += (float(yErrUp)-float(yNom))**2
        elif yErrDown > yNom:
          errUp += (float(yErrDown)-float(yNom))**2
        if yErrUp <= yErrDown and yErrUp < yNom:
          errDown += (float(yErrUp)-float(yNom))**2
        elif yErrDown < yNom:
          errDown += (float(yErrDown)-float(yNom))**2
      if badPoint:
        continue
      errUp = sqrt(errUp)
      errDown = sqrt(errDown)
      modelGraph.SetPoint(iPoint,xNom,yNom)
      modelGraph.SetPointError(iPoint,0.,0.,errDown,errUp)
      iPoint+=1
    iPoint = 0
    for i in range(curveData.GetN()):
      curveData.GetPoint(i,xNom,yNom)
      if yNom <=0.0:
        continue
      dataGraph.SetPoint(iPoint,xNom,yNom)
      errUp = sqrt(yNom)*sqrt(avgWeight)
      errDown = sqrt(yNom)*sqrt(avgWeight)
      dataGraph.SetPointError(iPoint,0.,0.,errDown,errUp)
      iPoint+=1
    iPoint = 0
    for i in range(curveNomPlusSig.GetN()):
      curveNomPlusSig.GetPoint(i,xNom,yNom)
      if yNom <=0.0:
        continue
      modelPlusSigGraph.SetPoint(iPoint,xNom,yNom)
      iPoint+=1
    iPoint = 0
    for i in range(curveSig.GetN()):
      curveSig.GetPoint(i,xNom,yNom)
      if yNom <=0.0:
        continue
      sigGraph.SetPoint(iPoint,xNom,yNom)
      iPoint+=1
    iPoint = 0
    for i in range(pulls.GetN()):
      pulls.GetPoint(i,xNom,yNom)
      pullsGraph.SetPoint(iPoint,xNom,yNom)
      errUp = pulls.GetErrorXhigh(i)
      errDown = pulls.GetErrorXlow(i)
      pullsGraph.SetPointError(iPoint,0.,0.,errDown,errUp)
      iPoint+=1
    dataGraph.SetName(curveData.GetName()+"_TGraph")
    modelGraph.SetName(curveNom.GetName()+"_TGraph")
    pullsGraph.SetName(curveData.GetName()+"_pullsTGraph")
    modelPlusSigGraph.SetName(curveNom.GetName()+"_modelPlusSigTGraph")
    sigGraph.SetName(curveNom.GetName()+"_sigTGraph")
    dataGraph.SetMarkerColor(1)
    modelGraph.SetLineColor(root.kBlue+1)
    modelGraph.SetFillColor(root.kCyan)
    modelGraph.SetFillStyle(1)
    modelPlusSigGraph.SetLineColor(root.kRed)
    sigGraph.SetLineColor(root.kRed)

    return dataGraph, modelGraph, modelPlusSigGraph, sigGraph, pullsGraph, chi2, fr.floatParsFinal().find("sigStrength")

  def scaleSigPDFGraph(self,ingraph,sigCountVar,rateMap,sigStrength):
    originalCount = sigCountVar.getVal()
    oneSigCount = 0.0
    for i in rateMap:
        if i != "bak":
          oneSigCount += rateMap[i] 
    bestFitSigStrength = originalCount/oneSigCount
    scaleFactor = sigStrength/bestFitSigStrength

    #print("originalCount: {:.2f} oneSigCount: {:.2f}  best fit mu: {:.2f}".format(originalCount,oneSigCount, bestFitSigStrength))
    #print("desired mu: {:.2f} desired count: {:.2f} scale factor: {:.2f}".format(sigStrength,sigStrength*oneSigCount,scaleFactor))

    result = root.TGraph()
    result.SetName("signalGraph")
    result.SetLineColor(root.kRed)
    iPoint = 0
    x = root.Double()
    y = root.Double()
    for i in range(ingraph.GetN()):
      ingraph.GetPoint(i,x,y)
      #if yNom <=0.0:
      #  continue
      result.SetPoint(iPoint,x,y*scaleFactor)
      iPoint+=1
    return result, bestFitSigStrength
    

titleMap = {
  "AllCat":"All Categories Comb.",
  "IncCat":"Non-VBF Categories Comb.",
  "VBFCat":"VBF Categories Comb.",

  "IncPresel":"Non-VBF Preselection",
  "VBFPresel":"VBF Preselection",

  "Pt0to30":"p_{T}^{#mu#mu} #in [0,30]",
  "Pt30to50":"p_{T}^{#mu#mu} #in [30,50]",
  "Pt50to125":"p_{T}^{#mu#mu} #in [50,125]",
  "Pt125to250":"p_{T}^{#mu#mu} #in [125,250]",
  "Pt250":"p_{T}^{#mu#mu}>250",

  "VBFLoose":"VBFL",
  "VBFMedium":"VBFM",
  "VBFTight":"VBFT",
  "VBFVeryTight":"VBFVT",

  "BDTCut":"BDT Cut Combination",
  "IncBDTCut":"Non-VBF BDT Cut",
  "VBFBDTCut":"VBF BDT Cut",

  "BDTCutCat":"BDT Cut Cat. Combination",
  "IncBDTCutCat":"Non-VBF BDT Cut",
  "VBFBDTCutCat":"VBF BDT Cut",

  "IncPreselCat":"Non-VBF Cat. Preselection",
  "VBFPreselCat":"VBF Cat. Preselection",

  "IncBDTCutBB":"Non-VBF BDT Cut BB",
  "IncBDTCutBO":"Non-VBF BDT Cut BO",
  "IncBDTCutBE":"Non-VBF BDT Cut BE",
  "IncBDTCutOO":"Non-VBF BDT Cut OO",
  "IncBDTCutOE":"Non-VBF BDT Cut OE",
  "IncBDTCutEE":"Non-VBF BDT Cut EE",
  "IncBDTCutNotBB":"Non-VBF BDT Cut !BB",
  "VBFBDTCutBB":"VBF BDT Cut BB",
  "VBFBDTCutNotBB":"VBF BDT Cut !BB",
  "IncPreselBB":"Non-VBF Preselection BB",
  "IncPreselBO":"Non-VBF Preselection BO",
  "IncPreselBE":"Non-VBF Preselection BE",
  "IncPreselOO":"Non-VBF Preselection OO",
  "IncPreselOE":"Non-VBF Preselection OE",
  "IncPreselEE":"Non-VBF Preselection EE",
  "IncPreselNotBB":"Non-VBF Preselection !BB",
  "VBFPreselBB":"VBF Preselection BB",
  "VBFPreselNotBB":"VBF Preselection !BB",

  "IncPreselPtG10BB":"Non-VBF BB",
  "IncPreselPtG10BO":"Non-VBF BO",
  "IncPreselPtG10BE":"Non-VBF BE",
  "IncPreselPtG10OO":"Non-VBF OO",
  "IncPreselPtG10OE":"Non-VBF OE",
  "IncPreselPtG10EE":"Non-VBF EE",
  "IncPreselPtG10NotBB":"Non-VBF !BB",

  "IncPreselPtG":"Non-VBF Not Combined"
}
        
if __name__ == "__main__":
  dataDir = "statsCards/"
  outDir = "shapes/"

  plotRange= [110.,160]
  #plotRange= []
  normRange = [110.,120.,130.,160]

  rebin=1

  shapePlotterList = []
  #for fn in glob.glob(dataDir+"*20.root")+glob.glob(dataDir+"*5.05.root"):
  for fn in glob.glob(dataDir+"*.root"):
  #for fn in glob.glob(dataDir+"BDTCutCat*.root"):
    if re.search("P[\d.]+TeV",fn):
        continue
    s = ShapePlotter(fn,outDir,titleMap,rebin,xlimits=plotRange,normRange=normRange,signalInject=args.signalInject,plotSignalStrength=args.plotSignalStrength,plotSignalBottom=args.plotSignalBottom)
    shapePlotterList.append(s)
