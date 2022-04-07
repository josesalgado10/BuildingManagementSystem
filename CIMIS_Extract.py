"""
    CIMIS class
    Pulls JSON data from CIMIS server.
    Retrieves average temperature, average humidity and average ET0 for the day.
"""

import requests
import json
import datetime
import time

class CIMIS():
        def __init__(self):
            #intial values so LCD doesnt try to print null
            self.temperature = 0
            self.ET0 = 0
            self.humidity = 0

        def update_values(self):
            date = str(datetime.date.today())
            #getting the date for data extraction 
            request=None
            
            try:
                request = requests.get('http://et.water.ca.gov/api/data?appKey=3688b999-e9e6-4b3e-9c8b-8070a92335f8&targets=75&startDate=' + date + '&endDate=' + date +'&dataItems=hly-eto,hly-rel-hum,hly-air-tmp',timeout = 30)
                request.json()
            except:
                request=None
                print("CIMIS Data Extraction Failed, retrying.....")
            if(request == None):
                    return False
                
            #resetting values here
            json_string = request.json()
            temperature = 0
            humidity = 0
            ET0 = 0
            records = json_string['Data']['Providers'][0]['Records']
            count = 0
            Valid_Tmp = False
            Valid_Et0 = False
            Valid_RelHum = False
            temp_count = eto_count= humid_count = 0
            
            for i in records:
                if i['HlyAirTmp']['Value'] != None:
                    temperature += float(i['HlyAirTmp']['Value'])
                    temp_count +=1
                    Valid_Tmp   = True
                    
                if i['HlyEto']['Value'] != None:
                    ET0         += float(i['HlyEto']['Value'])
                    eto_count += 1
                    Valid_Et0   = True
                if i['HlyRelHum']['Value'] != None:
                    humidity    += float(i['HlyRelHum']['Value'])
                    humid_count += 1
                    Valid_RelHum = True
                    
                if (Valid_Tmp == True):
                        self.temperature = temperature / temp_count
                        self.temperature = (float(self.temperature) - 32) * (5.0/9.0)
                        self.temperature = round(self.temperature, 2)                       
                        
                if (Valid_Et0 == True):
                        self.ET0         = round(ET0 / eto_count , 4)
                if (Valid_RelHum == True):
                        self.humidity    = round(humidity / humid_count , 2)

            print("CIMIS Temp.: " + str(self.temperature) + "C")
            print("CIMIS Hum.: " + str(self.humidity) + "%")
            print("ET0: " + str(self.ET0))
            

#To get Values for testing purposes
if __name__ == '__main__':
        cimis = CIMIS()
        while True:
            print("Pulling values.")
            cimis.update_values()
            print("ET0= ", cimis.ET0)
            print("humidity= ", cimis.humidity)
            print("temperature= ", cimis.temperature)
            time.sleep(5)
        
