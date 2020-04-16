import pandas as pd
import numpy as np

def CalculateDistance(lat1, lon1, lat2, lon2):
    """
    Uses the haversine function to calculate distance between two coordinates
    in longitude/latitudes

    :param lat1: origin latitude
    :type lat1: float
    :param lon1: origin longitude
    :type lon1: float
    :param lat2: destination latitude
    :type lat2: float
    :param lon2: destination longitude
    :type lon2: float
    :return: distance
    :rtype: float
    """
    p = np.pi/180 # convert to degrees
    a = 0.5 - np.cos((lat2 - lat1) * p) / 2 + np.cos(lat1 * p) * np.cos(lat2 * p) * \
        (1 - np.cos((lon2 - lon1) * p)) / 2
    return 12742 * np.arcsin(np.sqrt(a)) #2*R*asin...


def CreateInteractionMatrix(longData,latData,popData):
    """
    Calculates interaction matrix

    :param longData: centroid longitude data
    :type longData: array
    :param latData: centroid latitude data
    :type latData: array
    :param popData: population data
    :type popData: array
    :return: interaction matrix
    :rtype: array
    """

    nzip = popData.__len__()
    DistMatrix = np.empty(shape=(nzip,nzip))
    PopDistMatrix = np.empty(shape=(nzip,nzip))
    for i in range(0,nzip):
        DistMatrix[i,:] = CalculateDistance(latData[i],longData[i],latData,longData)
        DistMatrix[i,i] = 1
        PopDistMatrix[i,:] = popData[i] * popData
        
        
    InteractionMatrix = PopDistMatrix / DistMatrix
    NormalizedInteraction = np.empty(shape=(nzip,nzip))
    
    for i in range(0,nzip):
        rowsum = InteractionMatrix[i,:].sum()
        NormalizedInteraction[i,:] = InteractionMatrix[i,:] / rowsum

    return NormalizedInteraction

