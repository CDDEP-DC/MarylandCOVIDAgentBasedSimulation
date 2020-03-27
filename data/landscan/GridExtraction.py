# -----------------------------------------------------------------------------
# GridExtraction.py contains functions to convert global land data into a dict
# of spatial data
# -----------------------------------------------------------------------------

import numpy as np

def GridExtraction(landgrid,xblocklength,yblocklength):
    """
    converts a 2d array of landscan data into a dictionary of blocks

    :param landgrid: land scan data that needs to be broken down into blocks
    :type landgrid: array
    :param xblocklength: horizontal length of each local block of landscan data
    :type xblocklength: int
    :param yblocklength: vertical length of each local block of landscan data
    :type yblocklength: int
    :return: set of local blocks
    :rtype: dict
    """

    xtotsize = landgrid.shape[0]
    ytotsize = landgrid.shape[1]
    xnum = int(xtotsize / xblocklength)
    ynum = int(ytotsize / yblocklength)
    if xtotsize % xblocklength > 0:
       xnum += 1
    if ytotsize % yblocklength > 0:
       ynum += 1
    LocalPopulation = {}
    n=0
    coordDict = {}
    for i in range(0,xnum):
        for j in range(0,ynum):
            block = landgrid[i * xblocklength: (i + 1) * xblocklength,
                j * yblocklength: (j + 1) * yblocklength]
            LocalPopulation[n] = block.sum()
            if 20255 in block:
                coordDict["Market"] = (i, j)
                #print('Seafood Market is in coordinates ',(i, j))
            else:
                coordDict[n] = (i, j)
                n += 1
    Xcoord ={}
    Ycoord ={}
    for i in coordDict.keys():
        Xcoord[i] = coordDict[i][0]
        Ycoord[i] = coordDict[i][1]


    return Xcoord, Ycoord, LocalPopulation, coordDict

def GridDict(extractedGrid):
    Blocks = {}
    for i in range(0,extractedGrid.shape[0]):
        for j in range(0,extractedGrid.shape[1]):
            Blocks[(i,j)] = extractedGrid[i,j]
    
    return Blocks
    
def CreateInteractionMatrixFromLandscan(xCoord, yCoord, locPop):
    """
    Build interaction matrix based on euclidean distance and population density

    :param locationdict: spatial 2D array with population density
    :type locationdict: numpy array
    :param loc_ids: ordered list of location ids
    :type loc_ids: list of tuples
    :return: interaction matrix
    :rtype: array
    """
    numlocs = locPop.__len__()
    GravityMat = np.zeros(shape=(numlocs,numlocs))
    for i in range(0,numlocs):
        for j in range (0,numlocs):
            popi = locPop[i]
            popj = locPop[j]
            xdist = (xCoord[j] - xCoord[i])
            ydist = (yCoord[j] - yCoord[i])
            dist = (xdist**2 + ydist**2)**.5    # euclidean distance
            if i == j:
                dist = 1
            GravityMat[i,j] = popi * popj / dist**2

    InteractionMatrix = np.zeros(shape=(numlocs, numlocs))
    for i in range(0,numlocs):
        if GravityMat.sum(1)[i] > 0:
            InteractionMatrix[i, :] = GravityMat[i, :] / GravityMat[i, :].sum()
        else:
            InteractionMatrix[i, :] = np.zeros(numlocs)

    return np.array(InteractionMatrix)
