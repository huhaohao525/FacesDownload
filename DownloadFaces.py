import cv2
import numpy as np
import urllib2
import os
import os.path
import ConfigParser
import thread
import time
import csv
import Queue

class DownloadFaces:
    def __init__(self):
        self.stopDownloadFlag = False
        self.CONFIG_PATH = './DF_Config/'
        self.CONFIG_FILE = 'config.conf'
        self.SAVE_PATH = './FacesDownloaded/'
        self.FACE_DATASET_PATH = './face_dataset/files/'
        self.LOG_FILE = 'faces_err.log'
        self.LOG_PATH = './DF_Log/'
        self.imgQueue = Queue.Queue()
        #self.LIST_FILE = 'list_to_download.list'

        if not os.path.exists(self.CONFIG_PATH):
            print 'config path does not exist!'
            os.makedirs(self.CONFIG_PATH)

        if not os.path.exists(self.CONFIG_PATH + self.CONFIG_FILE):
            cf = ConfigParser.ConfigParser()
            cf.read(self.CONFIG_PATH + self.CONFIG_FILE)
            cf.add_section('progress')
            cf.set('progress','person_file','None')
            cf.set('progress','pic_ID','0')
            cf.set('progress','volume_used','0')
            cf.write(open(self.CONFIG_PATH + self.CONFIG_FILE,'w'))

        if not os.path.exists(self.FACE_DATASET_PATH):
            print './face_dataset/files/  does not exist..'

        if not os.path.exists(self.SAVE_PATH):
            os.makedirs(self.SAVE_PATH)

        if not os.path.exists(self.LOG_PATH):
            os.makedirs(self.LOG_PATH)
            csvfile = file(self.LOG_PATH + self.LOG_FILE,'wb')
            csvfile.close()

        self.logFile = file(self.LOG_PATH + self.LOG_FILE,'a+')
        self.log = csv.writer(self.logFile)

    def logARow(self,list):
        self.log.writerow(list)
        self.logFile.close()
        self.logFile = file(self.LOG_PATH + self.LOG_FILE,'a+')
        self.log = csv.writer(self.logFile)


    def url_to_image(self, url):
      # download the image, convert it to a NumPy array, and then read
      # it into OpenCV format
      resp = urllib2.urlopen(url,timeout = 8)
      image = np.asarray(bytearray(resp.read()), dtype="uint8")
      image = cv2.imdecode(image, cv2.IMREAD_COLOR)
      return image

    def getDonwloadInfo(self):
        cf = ConfigParser.ConfigParser()
        cf.read(self.CONFIG_PATH+'/'+self.CONFIG_FILE)
        person = cf.get('progress','person_file')
        picID = cf.get('progress','pic_ID')
        volume_used = cf.get('progress','volume_used')
        return person,picID,volume_used

    def downloadTread(self, person, picID, volume_used):
        ps = person
        pID = int(picID)
        vu = int(volume_used)
        personsList = os.listdir(self.FACE_DATASET_PATH)
        isFinding = True
        if ps == 'None':
            isFinding = False

        for p in personsList:
            if isFinding:
                if p == ps:
                    deltaVu = self.download(p, pID, vu)
                    vu += deltaVu
                    isFinding = False
            else :
                deltaVu = self.download(p, 1, vu)
                vu += deltaVu


    def download(self, person, picID, volume_used):
        deltaVu = 0
        isFinding = True
        if picID == 1:
            isFinding = False
        personfile = file(self.FACE_DATASET_PATH + person, 'rb')
        if not personfile:
            print 'file of ' + person + 'does not exist..'
            return 0
        csvReader = csv.reader(personfile)
        for line in csvReader:
            lineParams = line[0].split(' ')
            lineNumStr = lineParams[0]
            
            if isFinding:
                if int(lineNumStr) == int(picID):
                    if len(line) > 1:
                        #================================problem happens=========================
                        print 'this line can not be used,loging to file:' + self.LOG_FILE
                        splited = line[0].split(' ')
                        toLog = []
                        toLog.append(person)
                        toLog.append(splited)
                        self.logARow(toLog)
                        deltaVu += 0
                    elif len(line) == 1:
                        print 'Downloading :' + person + ',pic ID :' + str(int(lineNumStr)) + ',volume used: ' + str(volume_used)
                        lineInfo = line[0].split(' ')# 0 == picID, 1 == url, 2,3,4,5 == left,top,right,bottom
                        print lineInfo
                        result = self.processImage(lineNumStr, person, lineInfo[0], lineInfo[1], lineInfo[2], lineInfo[3], lineInfo[4], lineInfo[5])
                        if result == -1:
                            splited = line[0].split(' ')
                            toLog = []
                            toLog.append(person)
                            toLog.append(splited)
                            self.logARow(toLog)
                            deltaVu += 0
                        else:
                            deltaVu += result
                    isFinding = False
            else :
                if len(line) > 1:
                        #================================problem happens=========================
                    print 'this line can not be used,loging to file:' + self.LOG_FILE
                    splited = line[0].split(' ')
                    toLog = []
                    toLog.append(person)
                    toLog.append(splited)
                    self.logARow(toLog)
                    deltaVu += 0
                elif len(line) == 1:
                    print 'Downloading :' + person + ',pic ID :' + str(int(lineNumStr)) + ',volume used: ' + str(volume_used)
                    lineInfo = line[0].split(' ')# 0 == picID, 1 == url, 2,3,4,5 == left,top,right,bottom
                    result = self.processImage(lineNumStr, person, lineInfo[0], lineInfo[1], lineInfo[2], lineInfo[3], lineInfo[4], lineInfo[5])
                    if result == -1:
                        splited = line[0].split(' ')
                        toLog = []
                        toLog.append(person)
                        toLog.append(splited)
                        self.logARow(toLog)
                        deltaVu += 0
                    else:
                        deltaVu += result

                        

            if self.stopDownloadFlag == True:
                personfile.close()
                thread.exit()

        personfile.close()
        return deltaVu

    def processImage(self, lineNumStr, person, picID, url, left, top, right, bottom):
        personName = person.split('.')[0]
        imgType = url.split('.')[-1]
        if not os.path.exists(self.SAVE_PATH + personName):
            os.makedirs(self.SAVE_PATH + personName)

        try:
            img = self.url_to_image(url)
        except StandardError, e:
            print 'caught an error..'
            return -1
        except httplib.BadStatusLine, e:
            print 'caught an httplib error'
            return -1 

        self.imgQueue.put((img, lineNumStr, personName, imgType, person, picID, url, left, top, right, bottom))

         
        if img == None:
            return 0
        return img.size     

    def saveImage(self):
        while True:          
            if not self.imgQueue.empty():
                print 'getting item..'
                item = self.imgQueue.get()
                img, lineNumStr, personName, imgType, person, picID, url, left, top, right, bottom = item

                if img == None:
                #    self.imgQueue.task_done()
                    toLog = []
                    toLog.append(person)
                    toLog.append(picID)
                    toLog.append(url)
                    self.logARow(toLog)
                    continue

                subImg = img[int(float(top)):int(float(bottom)), int(float(left)):int(float(right))]

                try:
                    cv2.imwrite(self.SAVE_PATH + personName + '/' + str(int(picID)) + '.' + imgType, subImg)
                except cv2.error, e:
                    print 'caught an image write error..'
                #    self.imgQueue.task_done()
                    toLog = []
                    toLog.append(person)
                    toLog.append(picID)
                    toLog.append(url)
                    self.logARow(toLog) 
                    continue

                print 'save success~'
                cf = ConfigParser.ConfigParser()
                cf.read(self.CONFIG_PATH + self.CONFIG_FILE)
                cf.set('progress','person_file',person)
                cf.set('progress','pic_ID',int(lineNumStr) + 1)
                cf.set('progress','volume_used',0)
                cf.write(open(self.CONFIG_PATH + self.CONFIG_FILE,'w'))

                if self.stopDownloadFlag == True:
                    thread.exit()
                
                #self.imgQueue.task_done()
                #return img.size

    def processCommand(self):
        print 'input exit to stop downloading, input end to quit this program.'
        while True:
            command = raw_input()
            if command == 'exit':
                self.stopDownloadFlag = True
            if command == 'end':
                self.stopDownloadFlag = True
                break

def main():
    print 'MainFunc starts~'
    df = DownloadFaces()

    person, picID, volume_used = df.getDonwloadInfo()
    print 'download info: ' + 'person:' + person + ','+ 'picID:' + picID + ',' + 'volume_used:' + volume_used

    thread.start_new_thread(df.downloadTread,(person, picID, volume_used))
    thread.start_new_thread(df.saveImage,())

    
    df.processCommand()

    #img = url_to_image('http://www.contactmusic.com/pics/ld/active_for_life_arrivals_090110/a.j_buckley_2706152.jpg')
    #print img.size

if __name__ == '__main__':
    main()