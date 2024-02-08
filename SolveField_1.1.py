# -*- coding: utf-8 -*-
"""
Created on Tue Aug 18 23:52:26 2020

@author: Fischetto, Giuliano A.
"""

from PIL import Image
import os
import tarfile
import tkinter.filedialog
import numpy as np
import Client as astro #Astrometry.net Client (A little bit modiffied by the author of this code)
import time
import ast
import cv2
import copy
import winsound

T0=time.time()


#FUNCTIONS
def standby(totTime, query='back'):  #Stand-by time between requests for status
    if totTime<4: totTime=4
    stby=15 #Amount squares to complete charging bar
    delay=totTime/stby
    ASCII_block=u'\u2588'
    print('---Stand by, %s in %d seconds...' %(query,totTime))
    print('---%02ds-----------%02ds-----------0s\n' %(totTime,totTime/2),end='---', flush=True)
    for i in range(stby):
        print(ASCII_block, end=' ', flush=True)
        time.sleep(delay)
    print('\n\n')


def solve(myAPIkey, imagePath, numberOfFiles): #Get objects pixel location from Astrometry.net
    coordinatesFound={} #Here i'll store objects found and their coordinates for each job
    allJobStatus={}
    global imageUploaded
    imageUploaded=None
    try:
        uploadArgsFile = open(imagePath[0:-4]+'-kwargs.txt')
        uploadArgs = ast.literal_eval(uploadArgsFile.read())
    except:
        uploadArgs={}
    
    usr=astro.Client()
    login = usr.login(myAPIkey)
    print('\n')
    
    if login['status'] == 'success':
        
        imageUploaded = usr.upload(imagePath,**uploadArgs)
        print('\n')
        
        if imageUploaded['status'] == 'success':
            try:
                jobs=usr.sub_status(imageUploaded['subid'])['jobs']
                while not jobs or None in jobs or len(jobs) != numberOfFiles: #Wait until submission gets jobs assigned
                    standby(20,'waiting for all jobs to get assigned. Asking')
                    jobs=usr.sub_status(imageUploaded['subid'])['jobs']
                
                currentSubJobsStatus=['solving'] #Here i'll store the status of jobs in the submission
                while 'solving' in currentSubJobsStatus:
                    standby(30, 'waiting for all jobs to get solved. Next jobs\' status report')
                    
                    currentSubJobsStatus=[] 
                    currentSub=usr.sub_status(imageUploaded['subid']) #Info of the submission
                    print('\n')
                    for job in currentSub['jobs']:
                        currentSubJobsStatus.append(usr.job_status(job)) 
                        print('\n')
    
                    
                    if 'solving' not in currentSubJobsStatus:
                        if 'success' not in currentSubJobsStatus:
                            print('---Every image failed')
                        print('---Jobs\' status: ',currentSubJobsStatus)
                        print('\n')
                        break
                    print('---Recent jobs\' status: ',currentSubJobsStatus)
                
                coordinatesFound={} #Here i'll store objects found and their coordinates for each job
                allJobStatus={}
                lastSubStatus = usr.sub_status(imageUploaded['subid'])
                for job in lastSubStatus['jobs']:
                    currentJobStatus = usr.job_status(job)
                    allJobStatus['%d'%job]=currentJobStatus
                    if currentJobStatus == 'success':
                        coordinatesFound['%d'%job]=usr.annotate_data(job)['annotations'] 
                        coordinatesFound['%d'%job].sort(key=lambda x: x.get('vmag')) #Sort by magnitude (most shiny first)
                    else:
                        coordinatesFound['%d'%job]=[]

                print('\n---Solving done')
            except:
                print('---Something failed.')
                standby(5,'trying again')
        else:
            print('---File upload status: \r',imageUploaded['status']) #Image uploading failed
            coordinatesFound = None
            allJobStatus = None
    return coordinatesFound, imageUploaded['status'], allJobStatus

def filterCoordinates(Coordinates, maxvar=7): #Filter images by varianze and get average pixel position
    allCoords={} #Store every object and coordinates in original image
    filteredCoords={} #Final coordinates which, if found multiple times, are below a certain varianze
    
    maxvarx=maxvary=maxvar #Varianze of multiple time found objects
    
    for job, objs in Coordinates.items(): #Unpack jobs (usually 1) and objects (stars, etc) found in them
        for obj in objs: #For every object
            existed=False
            for names, _ in allCoords.items(): #Add object to allCoords, if already existed it apends the current pixel coordinates 
                if '%s'%(obj['names']) == names:
                    existed=True
                    allCoords[names]['pixelx'].append(copy.deepcopy(obj['pixelx']))
                    allCoords[names]['pixely'].append(copy.deepcopy(obj['pixely']))
                    allCoords[names]['vmag']=copy.deepcopy(obj['vmag'])
            if existed==False:
                allCoords['%s'%obj['names']]={'pixelx':[copy.deepcopy(obj['pixelx'])],'pixely':[copy.deepcopy(obj['pixely'])],'vmag':copy.deepcopy(obj['vmag'])}
                        
    for names, _ in allCoords.items(): #Calculate average coordinates and varianze
        allCoords[names]['averagex']=np.average(allCoords[names]['pixelx'])
        allCoords[names]['varx']=np.var(allCoords[names]['pixelx'])
        allCoords[names]['averagey']=np.average(allCoords[names]['pixely'])
        allCoords[names]['vary']=np.var(allCoords[names]['pixely'])
    
    for names, _ in allCoords.items():  #Filter by varianze condition
        if allCoords[names]['varx'] < maxvarx and allCoords[names]['vary'] < maxvary:
            filteredCoords[names]=copy.deepcopy(allCoords[names])
            
    return filteredCoords

def createTar(path, tar_name, imExt): #Create .tar file only with region images files
    numberOfFiles=0
    with tarfile.open(tar_name, 'w') as tar_handle:
        for file in os.listdir(path):
            if file[-4:]==imExt:
                tar_handle.add(path+file, arcname=file)
                numberOfFiles+=1
    tar_handle.close()
    return numberOfFiles

def createTxt(path,var): #Create .txt with data
    f = open(path, 'w+',encoding='utf-8')     
    f.write(str(var))
    f.close()  

def createNewDirectory(path):
    try: #Create new directory where to save future files
        os.makedirs(path)
    except FileExistsError:
        print('---Directory already existed')
        dirExists=True
    except OSError:
        print('---Creation of the directory %s failed.' %path)
    else:
        print('---New directory created succesfully: %s' %path)
        dirExists=True
    return dirExists

def tifToPng(Query): #Convert from .tif to .png
    def convertion():
        if (file[2].lower()=='tif' or file[2].lower()=='tiff') and file[1]=='.':
            if os.path.isfile(outfile):
                print ('---A png file already exists for %s' % file[0])
            else:
                try:
                    currentImage = Image.open(tiffsPath+'/'+tiffile)
                    print('---Generating png for %s' % file[0])
                    currentImage.thumbnail(currentImage.size)
                    currentImage.save(outfile, 'PNG')
                except:
                    print('---Failed to generate png for %s' % file[0])
    
    dirExists = None
    pngDir='/PNG-files/'
   
    if Query == '2':
        print('---Select .tif file')
        tiffsPath = tkinter.filedialog.askopenfilename(title='Select .tiff file')
        dirExists = createNewDirectory(tiffsPath.rpartition('/')[0]+pngDir)
        
    if Query == '4':
        print('---Select file directory where .tif files are. CAUTION: every tif will be solved')
        tiffsPath = tkinter.filedialog.askdirectory(title='Select directory where .tiff files are')
        dirExists = createNewDirectory(tiffsPath+pngDir)   
    
    if dirExists:
        if Query == '2':
            tiffile = tiffsPath.rpartition('/')[2]
            file = tiffile.rpartition('.')
            outfile = tiffsPath.rpartition('/')[0]+pngDir+file[0]+'.png'
            tiffsPath = tiffsPath.rpartition('/')[0]
            convertion()
            convertedPath = outfile
            
        if Query == '4':
            for tiffile in os.listdir(tiffsPath):
                file=tiffile.rpartition('.')
                outfile = tiffsPath+pngDir+file[0]+'.png'
                convertion()
            convertedPath = tiffsPath+pngDir
        
    return convertedPath

def cropAndSolve(originalImagePath, APIkey="notAPIkey"): #Crop current image into regions and sole with Astrometry.net Client
    tempPath = originalImagePath.rpartition('/')
    tempName = tempPath[2].rpartition('.')[0]
    newDirectory = tempPath[0]+'/'+tempName+'/'
    dirExists0 = createNewDirectory(newDirectory)
    if dirExists0:
        tempIm = Image.open(originalImagePath)
        tempIm.save(newDirectory+tempPath[2])
        imagePath = newDirectory+tempPath[2]
        print(imagePath)
        
    
    Ti=time.time()
    if imagePath != '':
        imageCoordinates=[]
        NameDotExt=(imagePath.rpartition('/')[2]).rpartition('.')
        imageName=NameDotExt[0]
        imageExtention=NameDotExt[1]+NameDotExt[2]
        Dir = imagePath.rpartition('/')[0]
        newDir ='/croppedRegionsToUpload-%s/'%imageName
        regionsDir ='/regionsOverlay-%s/'%imageName
        tarPath = Dir+newDir+'%s-regions.tar'%imageName
        regionNames=[]
        
        pixelDispersion = 5 #Max pixel varianze allowed
        
        # ***Ver como generalizar esto***
        #Grid proposed to dissect image for a more efficient job for Astrometry.net
        cropMesh =  [[4,4,4,4,0,(255,255,255)],[3,3,4,4,0,(0,0,255)],[7,1,8,2,0,(0,255,0)],[7,1,8,2,1,(0,255,255)],\
                     [1,6,2,8,0,(255,255,0)],[1,6,2,8,1,(255,0,255)]] #[NumXregions,NumYregions,fractionOfImageWith,fractionOfImageHeight,NumberOfSimilarLevel]

        dirExists1 = createNewDirectory(Dir+newDir)
        dirExists2 = createNewDirectory(Dir+regionsDir)
    
         
        if dirExists1 and dirExists2:
            im=Image.open(imagePath)
            allRectanglesImage = cv2.imread(imagePath)
            imW, imH = im.size
            
            for level in cropMesh: #Dissect image into regions (easier for Astrometry.net to solve)
                #Region dimension relative to image size
                boxW = imW/level[2]-1
                boxH = imH/level[3]-1
                
                # ***Ver como generalizar esto***
                #Coordinate origin shifts 
                if level == cropMesh[0]: #Grid 0
                    xSh = 0
                    ySh = 0
                    
                if level == cropMesh[1]: #Grid 1
                    xSh = boxW/2
                    ySh = boxH/2
                
                if level == cropMesh[2]:
                    xSh = boxW/2
                    ySh = boxH/8
                
                if level == cropMesh[3]:
                    xSh = boxW/2
                    ySh = boxH*(7/8)
                    
                if level == cropMesh[4]:
                    xSh = boxW/4
                    ySh = boxH
                
                if level == cropMesh[5]:
                    xSh = boxW*(3/4)
                    ySh = boxH
                    
                rectanglesImage = cv2.imread(imagePath)
                for x in range(level[0]):   #Cropping and saving region images
                    for y in range(level[1]):
                        box=np.array([xSh+x*boxW,ySh+y*boxH,xSh+(x+1)*boxW-1,ySh+(y+1)*boxH-1], dtype='int32')
                        boxTuple=tuple(box)
                        region=im.crop(boxTuple)
                        imSaveName=Dir+newDir+imageName+'---crop-lvl'+str(level)+'-reg'+str([x,y])+'-xo%05d-yo%05d-xf%05d-yf%05d'%boxTuple+imageExtention
                        region.save(imSaveName)
                        regionNames.append(imSaveName)
                        cv2.rectangle(rectanglesImage,(box[0],box[1]),(box[2],box[3]),level[5])
                        cv2.imwrite(Dir+regionsDir+'%s-rectangles-region'%imageName+str(level[0:-1])+'.png',rectanglesImage)
                        cv2.rectangle(allRectanglesImage,(box[0],box[1]),(box[2],box[3]),level[5])
                        
            cv2.imwrite(Dir+regionsDir+'%s-allRectangles.png'%imageName,allRectanglesImage)
            regionNames.sort() #Useful to map jobIDs with regions
            numberOfFiles = createTar(Dir+newDir, tarPath, imageExtention) #Create .tar file with region images
            try:
                regionCoordinates, uploadStatus, jobsStatus = solve(APIkey, tarPath, numberOfFiles) #Solve regions with Astrometry.net
            except:
                input('---Something Failed when calling Astrometry.net, probably inputed wrong API key. App will close now...')
                
            if uploadStatus == 'success' and 'success' in jobsStatus.values():
                try:
                    createTxt(Dir+newDir+'regionCoordinates-%s.txt'%imageName, regionCoordinates) #Save region coordinates found for .tar file
                    print('---Succeded to create regionCoordinates-%s.txt'%imageName)
                except:
                    print('---Failed to create regionCoordinates.txt')
                    
                jobIDs=[] #Will map these with var: regionNames
                for jobid, _ in regionCoordinates.items():
                    jobIDs.append(jobid)
                jobIDs.sort()
                
                imageCoordinates={}
                if len(regionNames) == len(jobIDs): #Mapping region to image pixelValues
                    for i in range(len(jobIDs)):
                        imageCoordinates['%s'%jobIDs[i]]=copy.deepcopy(regionCoordinates['%s'%jobIDs[i]])
                        
                        #Getting origins index for each region
                        indexXoStart=regionNames[i].index('xo', len(imageName))+2
                        indexXoEnd=regionNames[i].index('-yo', len(imageName))
                        indexYoStart=regionNames[i].index('yo', len(imageName))+2
                        indexYoEnd=regionNames[i].index('-xf', len(imageName))
                        
                        #Getting origin coordinates for each region
                        xo=int(regionNames[i][indexXoStart:indexXoEnd])
                        yo=int(regionNames[i][indexYoStart:indexYoEnd])
        
                        for obj in imageCoordinates['%s'%jobIDs[i]]: #Adding (xo,yo) to pixel values
                            obj['pixelx']+=xo
                            obj['pixely']+=yo
                
                #If objects were found multiple times, check for a minimun coordinate dispersion 
                filteredImageCoordinates = filterCoordinates(imageCoordinates, pixelDispersion) 
                
                try:
                    createTxt(Dir+newDir+'filteredImageCoordinates-%s.txt'%imageName, filteredImageCoordinates)
                    print('---Succeded to create filteredImageCoordinates-%s.txt'%imageName)
                except:
                    print('---Failed to save txt with coordinates')
                
                try: #Sorting objects by brightness magnitude
                    sortedFilteredImageCoordinates=[]
                    for obj, data in filteredImageCoordinates.items():
                        currentObj={'name':obj, **data}
                        sortedFilteredImageCoordinates.append(currentObj)
                        
                    sortedFilteredImageCoordinates.sort(key=lambda x: x.get('vmag'))
                    print('---Succeded to sort coordinates by vmag')
                except:
                    print('---Failed to sort coordinates by vmag')
                
                try:
                    createTxt(Dir+'/sortedFilteredImageCoordinates-%s.txt'%imageName, sortedFilteredImageCoordinates)
                    print('---Succeded to create sortedfilteredImageCoordinates-%s.txt'%imageName)
                except:
                    print('---Failed to save txt with sorted by vmag coordinates')
                    
                try:    #Drawing objects found over original image
                    objImage = cv2.imread(imagePath)
                    index=-1
                    for obj in sortedFilteredImageCoordinates:
                        index+=1
                        xShift=int(len(str(index))*3)
                        xO=int(obj['averagex'])
                        yO=int(obj['averagey'])
                        objImage[yO,xO]=[0,255,0] #Center dot
                        cv2.circle(objImage,(xO,yO),5,(0,255,0),1) #Circle
                        cv2.putText(objImage,str(index),(xO-xShift,yO+15),cv2.FONT_HERSHEY_SIMPLEX,0.3,(0,255,0)) #Number id (sorted by brightness magnitude)
                    cv2.imwrite(imagePath[0:-4]+'-objects.png',objImage)
                    print('---Succeded to create image overlay: %s-objects.png'%imageName)
                except:
                    print('---Failed to create image overlay')
                        
            else:
                if uploadStatus != 'success':
                    print('---Error: upload status = %s'%uploadStatus)
                elif 'success' not in jobsStatus:
                    print('---Astrometry.net failed to solve any region')
                else:
                    print('---Something failed (Unknown Error)')
                    
        else:
            print('---Failed to create new directories: ')
            if dirExists1:
                print('---Failed to create rectangles overlay directory.')
            if dirExists2:
                print('---Fialed to create regions directory.')
        
        duration = 300  # milliseconds
        freq = 190  # Hz
        winsound.Beep(freq, duration) #SoundAlarm
        print('---This solving took %d '%(time.time()-Ti)+'seconds to run')
        
        
#------------------------------------------------------------------------------------------------
        
        
AstrometryDotNetAPIkey=input('Enter Astrometry.net API key:')  # (***or press enter tou use default***):')

#Ask user to select an image to solve with Astrometry.net
Query = input('What do you want to solve?\n\n\
1: single PNG, JPEG, GIF, FITS image \n\
2: single TIF, TIFF image \n\
3: set of PNG, JPEG, GIF, FITS images \n\
4: set of TIF, TIFF images \n\
ENTER: None\n\n\
Type your entry: ')

if Query == '1':
    path = tkinter.filedialog.askopenfilename(title='Select image file', filetypes=(('PNG files','*.png'),('JPEG files','*.jpg'),('FITS files','*.fits')))
    if AstrometryDotNetAPIkey == '': cropAndSolve(path)
    else: cropAndSolve(path, AstrometryDotNetAPIkey)
    
if Query == '2': 
    path = tifToPng(Query)
    if AstrometryDotNetAPIkey == '': cropAndSolve(path)
    else: cropAndSolve(path, AstrometryDotNetAPIkey)

if Query == '3':
    path = tkinter.filedialog.askdirectory(title='Select directory where image files are')
    for imFile in os.listdir(path):
        duration = 1000  # milliseconds
        freq = 440  # Hz
        winsound.Beep(freq, duration) #SoundAlarm
        nextIm = input('---Next image to solve:\n\n'+path+imFile+'\n\nPress Enter to continue or any caracter to stop: ')
        if nextIm == '':
            if AstrometryDotNetAPIkey == '': cropAndSolve(path+imFile)
            else: cropAndSolve(path+imFile, AstrometryDotNetAPIkey)
        else:
            print('Exiting program')
            print('---The code took %d '%(time.time()-T0)+'seconds to run')

if Query == '4':
    path = tifToPng(Query)
    for tiffile in os.listdir(path):
        duration = 1000  # milliseconds
        freq = 440  # Hz
        winsound.Beep(freq, duration) #SoundAlarm
        nextIm = input('---Next image to solve:\n\n'+path+tiffile+'\n\nPress Enter to continue or any caracter to stop: ')
        if nextIm == '':
            if AstrometryDotNetAPIkey == '': cropAndSolve(path+tiffile)
            else: cropAndSolve(path+tiffile, AstrometryDotNetAPIkey)
        else:
            print('Exiting program')
            print('---The code took %d '%(time.time()-T0)+'seconds to run')
        
print('---The code took %d '%(time.time()-T0)+'seconds to run')

input('Press Enter to close program: ')
            