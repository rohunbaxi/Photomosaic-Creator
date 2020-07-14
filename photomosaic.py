from PIL import Image
import os
import glob
import imghdr

#FLASK-----------------
from flask import Flask, render_template, request, send_file

app = Flask(__name__)

@app.route('/', methods = ['POST', 'GET']) #home page
def home():
    return render_template('index.html')

@app.route('/upload', methods = ['POST', 'GET']) #runs photomosaic code, loads intermediary page
def upload():

    sideLen = int(request.form['amountRange'])
    selection = 'imageCollection' + str(request.form['selectIMG'])
    for file in request.files.getlist('myfiles[]'):
        file.save('outputPhotomosaic/input.jpg')

    #PHOTOMOSAIC CODE--------------------------------------------------
    photo = Image.open('outputPhotomosaic/input.jpg')
    width, height = photo.size

    def pixelmatrix(image):
        pixels = list(image.getdata())
        # loops through each row of the image through the image height
        return [pixels[i * width:(i + 1) * width] for i in range(height)]

    def squarePixels(pixels, size, corner):
        # (height,width), starts at top left
        opposite = (corner[0] + size, corner[1] + size)
        rowMatrix = pixels[corner[0]:opposite[0]]
        squareMatrix = []
        for row in rowMatrix:
            squareMatrix.append(row[corner[1]:opposite[1]])
        return squareMatrix

    def AvgRGB(pixels):
        R = 0
        G = 0
        B = 0
        pixelCount = 0
        for i in pixels:
            for j in i:
                R += j[0]
                G += j[1]
                B += j[2]
                pixelCount += 1
        return [int(R / pixelCount), int(G / pixelCount), int(B / pixelCount)]

    def squareImages(path, output):
        images = {}
        for image in os.listdir(path):
            i = Image.open(os.path.join(path, image))
            crop = i.crop((0, 0, min(i.size), min(i.size)))
            crop.save(os.path.join(output, image))
            images[image] = path
        return images

    def inputRGB(output, images):
        for image in os.listdir(output):
            path = os.path.join(output, image)
            i = Image.open(path)
            if str(path) == "processing\keep.jpg":
                continue
            images[image] = (AvgRGB(pixelmatrix(i)))
        return images

    def pythagoreanMatch(images, avg):
        difference = float('inf')
        keeper = None
        for key, value in images.items():
            check = (value[2] - avg[2]) ** 2 + (value[1] - avg[1]) ** 2 + (value[0] - avg[0]) ** 2
            if check < difference:
                difference = check
                keeper = key
        return keeper

    def printMosaic(input, output, size):


        files = glob.glob("processing/*")
        for f in files:
            if str(f) == "processing\keep.jpg":
                continue
            os.remove(f)

        imageMatrix = pixelmatrix(photo)
        inputImgColors = inputRGB(output, squareImages(input, output))
        i = Image.new("RGB", (width, height), (255, 255, 255, 0))  # new white fully transparent image
        for x in range(0, height, size):
            for y in range(0, width, size):
                sq = squarePixels(imageMatrix, size, (x, y))
                colors = AvgRGB(sq)
                matchingImage = pythagoreanMatch(inputImgColors, colors)
                im = Image.open(output + '/' + matchingImage, 'r')
                im.thumbnail((size, size))
                i.paste(im, (y, x))
        i.save('outputPhotomosaic/Photomosaic.jpg')

    printMosaic(selection, 'processing', sideLen)
    #-------------------------------------------------------------

    return render_template('complete.html')

@app.route('/final', methods = ['POST', 'GET'])#displays img in new tab
def final():
    return send_file('outputPhotomosaic/Photomosaic.jpg')

if __name__ == "__main__":
    app.run(debug=False)

#------------------------------
