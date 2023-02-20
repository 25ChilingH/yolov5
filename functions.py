import easyocr
import cv2
from geopy.geocoders import ArcGIS

skip = ['bike', 'hwy', 'highway', 'to', 'exit'] # substrings of skipped words
reader = easyocr.Reader(['en'])
def giveText(imgpred, image):
    conf_thresh = 0.2
    minHeight = 20
    minWidth = 70
    streets = []
    for pred in imgpred:
        left = pred[0] # centery-height + h_padding
        top = pred[1] # centerx-width + w_padding
        right = pred[2] # centery+height - h_padding
        bottom = pred[3] # centerx+width - w_padding
        
        # padding
        widthPadding = (right - left) * 0.1
        heightPadding = (bottom - top) * 0.01
        left -= widthPadding
        right += widthPadding
        bottom += heightPadding
        top -= heightPadding

        # making sure there is readable text
        height = bottom - top
        width = right - left
        print("Height: %d, Width: %d"%(height, width))

        # ocr
        if height >= minHeight and width >= minWidth:
            cropped_image = image[round(top):round(bottom), round(left):round(right)]
            # grayscale region within bounding box
            gray = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2GRAY)
            # threshold the image using Otsus method to preprocess for tesseract
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
            # perform a median blur to smooth image slightly
            blur = cv2.medianBlur(thresh, 3)
            # resize image to double the original size as tesseract does better with certain text size
            blur = cv2.resize(blur, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
            # cv2.imshow('', blur)
            # cv2.waitKey(0)
            result = reader.readtext(blur)
            street = ""
            for detection in result: 
                if detection[2] > conf_thresh:
                    text = detection[1]
                    textList = []
                    for x in text.split():
                        textList.append(''.join(filter(str.isalnum, x)))
                    text = ' '.join(textList)
                    street += text + " "
            street = street[:-1].lower()
            if not any(s in street for s in skip):
                streets.append(street)
    # cv2.destroyAllWindows()
    return streets

def geocodeIntersection(streets, state="California", country="USA"):
    geolocator = ArcGIS()
    param = "{} and {}, {}, {}".format(streets[0], streets[1], state, country)
    location = geolocator.geocode(param)
    return (location.latitude, location.longitude)