import easyocr
import cv2
from geopy.geocoders import ArcGIS
import time
import math
import pynmea2
import serial
from datetime import datetime

reader = easyocr.Reader(['en'])
geolocator = ArcGIS()
streets = []
skip = ['bike', 'hwy', 'highway', 'to', 'exit']
def giveText(imgpred, image):
    minHeight = len(image) * 0.02
    minWidth = len(image[0]) * 0.03
    for pred in imgpred:
        left = pred[0] # centery-height + h_padding
        top = pred[1] # centerx-width + w_padding
        right = pred[2] # centery+height - h_padding
        bottom = pred[3] # centerx+width - w_padding
        
        # padding
        widthPadding = (right - left) * 0.1
        heightPadding = (bottom - top) * 0.05
        left -= widthPadding
        right += widthPadding
        bottom += heightPadding
        top -= heightPadding

        # making sure there is readable text
        height = bottom - top
        width = right - left
        # cv2.imshow('', image)
        # cv2.waitKey(0)
        print("Height: %d, Width: %d"%(height, width))
        try:
            # ocr
            if height >= minHeight and width >= minWidth:
                cropped_image = image[round(top):round(bottom), round(left):round(right)]
                # grayscale region within bounding box
                gray = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2GRAY)
                # threshold the image using Otsus method to preprocess for tesseract
                thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
                # perform a median blur to smooth image slightly
                blur = cv2.medianBlur(thresh, 3)
                # resize image to double the original size as tesseract does better with certain text size
                blur = cv2.resize(blur, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
                # cv2.imshow('', blur)
                # cv2.waitKey(0)
                result = reader.readtext(blur, allowlist="abcdefghijklmnopqrstuvwxyz0123456789", detail=0, paragraph=True)
                if result:
                    result = result[0].lower()
                    if not any(s in result for s in skip):
                        streets.append([result, time.time()])
        except:
            return "Unable to detect text"
    # cv2.destroyAllWindows()
    return streets

def geocodeIntersection(streets, state="California", country="USA", threshold=5):
    if streets[1][1] - streets[0][1] <= threshold:
        param = "{} and {}, {}, {}".format(streets[0][0], streets[1][0], state, country)
        location = geolocator.geocode(param)
        return (location.latitude, location.longitude)        
    return "No intersection found"

def readGPS(latitude, longitude, path):
    COM_PORT = "/dev/ttyTHS1"
    BAUDRATE = 9600

    print("Running get_lat_lon function")
    f = open(path, "a")

    serial_port = serial.Serial(COM_PORT, BAUDRATE, timeout = None)

    # Wait until GPS is released
    pipe = True
    while pipe:
        pipe = serial_port.inWaiting()
        serial_port.read(pipe)

    try:
        while True:
            line = serial_port.readline()
            line2 = line.decode('latin-1')

            if line2.startswith("$GNGGA"):
                msg = pynmea2.parse(line2.strip())
                
                latitude.value, longitude.value = msg.latitude, msg.longitude
                if latitude.value != 0 or longitude.value != 0:
                    f.write(f"{datetime.now().strftime('%Y:%m:%d:%H:%M:%S')} {msg.timestamp} {str(latitude.value)} {str(longitude.value)} \n")
                    serial_port.close()
                    f.flush()
                    break
            else:
                pass
    except:
        print("GPS not available")
        
# focal length in mm
f = 3.04
# real height of a street sign in mm = 6 inches
real_height = 152.4
# image height in pixels
image_height = 416
# camera/sensor height in mm
sensor_height = 23
def distance(pred):
    # object height in pixels
    object_height = pred[3]-pred[1]
    return (f * real_height * image_height)/(object_height * sensor_height)

def translate_latlong(lat,long,lat_translation_meters,long_translation_meters):
    ''' method to move any lat,long point by provided meters in lat and long direction.
    params :
        lat,long: lattitude and longitude in degrees as decimal values, e.g. 37.43609517497065, -122.17226450150885
        lat_translation_meters: movement of point in meters in latitude direction.
                                positive value: up move, negative value: down move
        long_translation_meters: movement of point in meters in longitude direction.
                                positive value: left move, negative value: right move
        '''
    earth_radius = 6378.137

    #Calculate top, which is lat_translation_meters above
    m_lat = (1 / ((2 * math.pi / 360) * earth_radius)) / 1000;  
    lat_new = lat + (lat_translation_meters * m_lat)

    #Calculate right, which is long_translation_meters right
    m_long = (1 / ((2 * math.pi / 360) * earth_radius)) / 1000;  # 1 meter in degree
    long_new = long + (long_translation_meters * m_long) / math.cos(lat * (math.pi / 180))
    
    return lat_new,long_new

