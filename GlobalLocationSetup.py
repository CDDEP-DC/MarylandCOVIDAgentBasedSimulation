

class GlobalLocationSetup:
    def __init__(self, globalId, populationAmt, HHSizeDist, HHSizeAgeDist):
        self.globalId = globalId
        self.populationAmt = populationAmt
        self.HHSizeDist = HHSizeDist
        self.HHSizeAgeDist = HHSizeAgeDist
        
    def getGlobalId(self):
        return self.globalId

    def getPopulationAmt(self):
        return self.populationAmt

    def getHHSizeDist(self):
        return self.HHSizeDist

    def getHHSizeAgeDist(self):
        return self.HHSizeAgeDist
