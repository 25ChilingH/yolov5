import easyocr
import cv2
from geopy.geocoders import ArcGIS
import time

reader = easyocr.Reader(['en'])
geolocator = ArcGIS()
streets = []
def giveText(imgpred, image):
    minHeight = 20
    minWidth = 70
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
        print("Height: %d, Width: %d"%(height, width))
        try:
            # ocr
            if height >= minHeight and width >= minWidth:
                cropped_image = image[round(top):round(bottom), round(left):round(right)]
                # grayscale region within bounding box
                gray = cv2.cvtColor(cropped_image, cv2.COLOR_RGB2GRAY)
                # threshold the image using Otsus method to preprocess for tesseract
                thresh = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
                # perform a median blur to smooth image slightly
                blur = cv2.medianBlur(thresh, 3)
                # resize image to double the original size as tesseract does better with certain text size
                blur = cv2.resize(blur, None, fx = 2, fy = 2, interpolation = cv2.INTER_CUBIC)
                cv2.imshow('', blur)
                cv2.waitKey(0)
                result = reader.readtext(blur, blocklist="hwybikehighwaytoexit-.:';,[]()*&^%$#@!?/{}", detail=0, paragraph=True)
                if result:
                    result = result[0].lower()
                    streets.append([result, time.time()])
        except:
            return "Unable to detect text"
    cv2.destroyAllWindows()
    return streets

def geocodeIntersection(streets, state="California", country="USA", threshold=5):
    if streets[1][1] - streets[0][1] <= threshold:
        param = "{} and {}, {}, {}".format(streets[0][0], streets[1][0], state, country)
        location = geolocator.geocode(param)
        return (location.latitude, location.longitude)
    return "No intersection found"