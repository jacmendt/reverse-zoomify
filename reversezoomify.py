"""
This python scripts helps to reverse zoomify tiles.

:Date: 2015-04-23
:Authors: jacmendt
:Version: 1.0.0
:Copyright: 
"""
import math
import tempfile
import urllib2
import os
import shutil
import argparse
import xml.etree.ElementTree as ET
from PIL import Image

def calculateTierSize(imageWidth, imageHeight, tileSize=256):
    """ The function calculate the number of tiles per tier
    
    :type imageWidth: float
    :type imageHeight: float
    :type tileSize: int (default=256)
    :return: Array.<Array.<float>> """
    tierSizeInTiles = []
    while (imageWidth > tileSize or imageHeight > tileSize):
        tileWidth = float(imageWidth) / tileSize
        tileHeight = float(imageHeight) / tileSize
        tierSizeInTiles.append([math.ceil(tileWidth), math.ceil(tileHeight)])
        tileSize += tileSize
    tierSizeInTiles.append([1.0, 1.0]) 
    tierSizeInTiles.reverse()     
    return tierSizeInTiles

def calculateTileCountUpToTier(tierSizeInTiles):
    """ The function caclulate the tileCount up to the top tier
    
    :type tileSizeInTiles: Array.<float>
    :return: Array.<float> """
    tileCountUpToTier = [0]
    for i in range(1, len(tierSizeInTiles)):
        value = tierSizeInTiles[i - 1][0] * tierSizeInTiles[i - 1][1] + tileCountUpToTier[i - 1]
        tileCountUpToTier.append(int(value))
    return tileCountUpToTier

def calculateTileUrl(tierSizeInTiles, tileCountUpToTier, zoom, baseUrl, tileSize):
    """ Calculate the tile urls for given parameter set.
    
    :type tierSizeInTiles: Array.<Array.<float>>
    :type tileCountUpToTier: Array.<float>
    :type zoom: int
    :type baseUrl: int
    :type tileSize: int
    :return: Array<str> """   
    tileUrls = []
    for tileCoordX in range(0, int(tierSizeInTiles[zoom][0])):
        for tileCoordY in range(0, int(tierSizeInTiles[zoom][1])):
            tileIndex = tileCoordX + tileCoordY * tierSizeInTiles[zoom][0] + tileCountUpToTier[zoom]
            tileGroup = int(math.floor(float(tileIndex) / tileSize)) # int(tileIndex / tileSize) | 0
            tileUrls.append(baseUrl + "TileGroup%(tileGroup)s/%(zoom)s-%(tileCoordX)s-%(tileCoordY)s.jpg"%{
                "tileGroup": tileGroup,
                "zoom": zoom,
                "tileCoordX": tileCoordX,
                "tileCoordY": tileCoordY
            })
    return tileUrls
    
def fetchTilesFromServer(tileUrls, targetDir):
    """ Fetch all image files from the server and save them in a targetdir.
    
    :type tileUrls: Array.<str>
    :type targetDir: str """
    print "Fetch image tiles from server ..."
    for url in tileUrls:        
        # print url
        imageFile = urllib2.urlopen(url)
        
        # write image to file
        outputStream = open(os.path.join(targetDir, url.split('/')[-1]), 'wb')
        outputStream.write(imageFile.read())
        outputStream.close()
    print "Finish fetching image files."

        
def getProperties(baseUrl):
    """ Fetch and parse the properties xml file.
    
    :type baseUrl: str
    :return: dict """
    propertiesResponse = urllib2.urlopen(baseUrl + "ImageProperties.xml")
    xmlResponse = ET.fromstring(propertiesResponse.read())
    return xmlResponse.attrib
    
def mergeTiles(tileDir, targetPath, tierSizeInTiles, zoom, width, height, tileSize):
    """ Function merges all tiles into a single image.
    
    :type tileDir: str
    :type targetPath: str
    :type tierSizeInTiles: Array.<Array.<float>>
    :type zoom: int
    :type width: int
    :type height: int
    :type tileSize: int
    :return: str """
    print "Merge image tiles ..."
    mergeImage = Image.new("RGB", (width, height))
    for tileCoordX in range(0, int(tierSizeInTiles[zoom][0])):
        for tileCoordY in range(0, int(tierSizeInTiles[zoom][1])):
            filename = "%(zoom)s-%(tileCoordX)s-%(tileCoordY)s.jpg"%{
                "zoom": zoom,
                "tileCoordX": tileCoordX,
                "tileCoordY": tileCoordY
            }
            file = os.path.join(tileDir, filename)
            mergeImage.paste(Image.open(file), (tileCoordX * tileSize, tileCoordY * 256))
    mergeImage.save(targetPath)
    return targetPath

def reverseEngineerZoomifyTiles(baseUrl, targetDir, targetName):
    """ Base function for doing a reverse engineering of zoomify tiles in the max resolution.
    
    :type url: str 
    :type targetDir: str """
    print "Reverse zoomify tiles for url - %s"%baseUrl
    
    # get properties
    properties = getProperties(baseUrl)
    
    # calculate basic tile pyramid values
    tierSizeInTiles = calculateTierSize(int(properties['WIDTH']), int(properties['HEIGHT']), int(properties['TILESIZE']))
    tileCountUpToTier = calculateTileCountUpToTier(tierSizeInTiles)
    
    # get tiles    
    tileUrls = calculateTileUrl(tierSizeInTiles, tileCountUpToTier, len(tierSizeInTiles) - 1, baseUrl, int(properties['TILESIZE']))
    tileDir = tempfile.mkdtemp("", "tmp_", targetDir)  # create dir
    fetchTilesFromServer(tileUrls, tileDir)
    
    # create response
    targetPath = os.path.join(targetDir, "%s.jpg"%targetName)
    mergeTiles(tileDir, targetPath, tierSizeInTiles, len(tierSizeInTiles) - 1,
               int(properties['WIDTH']), int(properties['HEIGHT']), int(properties['TILESIZE']))
    
    shutil.rmtree(tileDir)
    
    print "Create file: %s"%targetPath
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This scripts allows the reverse engineering of zoomify tiles.', prog='ReverseZoomify')
    parser.add_argument('baseUrl', metavar='BASE_URL', type=str, help='Url to the zoomify directory.')
    parser.add_argument('targetDir', metavar='TARGET_DIR', type=str, help='Working and target directory for fetching and merging the image tiles.')
    parser.add_argument('outputName', metavar='OUTPUT_NAME', type=str, help='Name of the target image.')
    args = parser.parse_args()    
    
    reverseEngineerZoomifyTiles(args.baseUrl, args.targetDir, args.outputName)
    