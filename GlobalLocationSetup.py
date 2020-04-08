

class GlobalLocationSetup:
    def __init__(self, globalId, populationAmt, HHSizeDist, HHSizeAgeDist, PopulationDensity, LocalIdentification, RegionalIdentification):
        self.globalId = globalId
        self.populationAmt = populationAmt
        self.HHSizeDist = HHSizeDist
        self.HHSizeAgeDist = HHSizeAgeDist
        self.PopulationDensity = PopulationDensity
        self.LocalIdentification = LocalIdentification
        self.RegionalIdentification = RegionalIdentification
        
        
        
    def getGlobalId(self):
        return self.globalId

    def getPopulationAmt(self):
        return self.populationAmt

    def getHHSizeDist(self):
        return self.HHSizeDist

    def getHHSizeAgeDist(self):
        return self.HHSizeAgeDist

    def getPopulationDensity(self):
        return self.PopulationDensity
        
    def getLocalIdentification(self):
        return self.LocalIdentification
        
    def getRegionalIdentification(self):
        return self.RegionalIdentification
        