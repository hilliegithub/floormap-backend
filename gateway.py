from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
from flask_mysqldb import MySQL
import boto3
from botocore.exceptions import ClientError
import json
import os
import logging
import csv
from send import email

server = Flask(__name__)
mysql = MySQL(server)
CORS(server)
logging.basicConfig(level=logging.DEBUG)

#config
server.config["MYSQL_HOST"] = '127.0.0.1'
server.config["MYSQL_USER"] = 'floormap_db_user'
server.config["MYSQL_PASSWORD"] = '123456'
server.config["MYSQL_DB"] = 'floormap'
server.config["MYSQL_PORT"] = 3306

AWS_CONFIG = {
    'bucket' : 'floor-mapping',
    'region' : 'ca-central-1'
}

## POST /Upload --- Upload the image to the blob storage.
## Return the image name so that the image can be queried.
@server.route("/upload", methods=["POST"])
def upload():
    f = request.files['image']
    currentFileLocation = './temp/' + request.files['image'].filename
    f.save(currentFileLocation)
    old_filename, ext = os.path.splitext(currentFileLocation)

    building = request.form['building']
    floor = request.form['floor']
    email = request.form['email']

    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    newFilename = building + "_" + floor + "_" + current_datetime
    newFilename = newFilename.lower()
    print(newFilename)

    # Store image to aws s3 blob storage
    status = uploadtoS3((newFilename + ext), currentFileLocation, "floor-images/")

    # Store details mysql database
    isRequestStored =  False
    if status:
        isRequestStored = storerequest(email,(newFilename+ext))

    if isRequestStored and status:
        data = {
            'imagename': newFilename,
            'error': {
                'status': 'false',
                'message': 'No Errors'
            }
        }
    else:
        data = {
            'imagename': newFilename,
            'error': {
                'status': 'true',
                'message': 'Could not store request'
            }
        }
    json_data = jsonify(data)
    response = server.make_response(json_data)
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response

# Uploading to Amazon S3
def uploadtoS3(newFilename, currentFileLocation, folder):
    print("Inside uploadtos3: " + newFilename)
    bucket = AWS_CONFIG['bucket']
    object_key = folder + newFilename
    url = 'https://' + AWS_CONFIG['bucket'] + '.s3.' + AWS_CONFIG['region'] + '.amazonaws.com/' + object_key

    #s3_client = boto3.client('s3')
    try:
        print("test")
        #response = s3_client.upload_file(currentFileLocation, bucket, object_key)
    except ClientError as e:
        logging.error(e)
        return False
    print(url)
    return True

def storerequest(email,filename):
    try:
        cur = mysql.connection.cursor()
        res = cur.execute(
            "INSERT INTO request (email,floormapname) VALUES (%s,%s);", (email,filename,)
        )
        mysql.connection.commit()
        cur.close()
        return True
    except Exception as err:
        logging.debug(err)
        return False

def getImageFrmMySql(imgname):
    try:
        cur = mysql.connection.cursor()
        cur.execute(
            "SELECT * FROM request WHERE floormapname LIKE %s LIMIT 1", ("%" + imgname + "%",)
        )
        res = cur.fetchall()
        cur.close()
        return res

    except Exception as err:
        logging.debug(err)
        return ''

## GET /floor-map-select/:id --- Get the image
## Return the image to use
@server.route("/getimage", methods=["GET"])
def getimage():
    imgName = request.args.get("img")
    if not imgName:
        data = {"status": False,"imageKey": ""}
        response = server.make_response(jsonify(data))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    imgKey = None
    try:
        ## get the image url from database
        imgKey = getImageFrmMySql(imgName)
        print(imgKey)
        # print(imgKey[0])
        print(imgKey[0][1])
        print(imgKey[0][2])

    except Exception as err:
        logging.debug(err)

    if(len(imgKey) == 0):
        data = {
            'imageKey': '',
            'error': {
                'status': 'true',
                'message': 'Could not find a matching image-map'
            }
        }
    else:
        data = {
            'imageKey': imgKey[0][2],
            'error': {
                'status': 'false',
                'message': 'No errors found'
            }
        }

    print(data)
    response = server.make_response(jsonify(data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

@server.route("/createmap", methods=["POST"])
# @cross_origin()
def createmap():
    data = None
    try:
        json_data = request.json
        jsonMap = request.get_json(silent=True)

        filename = './tempmaps/' + jsonMap['boundary']['floormapname'] + '.csv'
        print(filename)
        with open(filename, mode='w') as map_file:
            file_writer = csv.writer(map_file, delimiter=',',quotechar='|', quoting=csv.QUOTE_MINIMAL)
            file_writer.writerow(['Name','top','right','bottom','left','width','height'])
            file_writer.writerow([jsonMap['boundary']['floormapname'],
            jsonMap['boundary']['top'],
            jsonMap['boundary']['right'],
            jsonMap['boundary']['bottom'],
            jsonMap['boundary']['left'],
            jsonMap['boundary']['width'],
            jsonMap['boundary']['height']]
            )
            for seat in jsonMap['seats']:
                file_writer.writerow([seat['name'],
                seat['relativeTop'],
                seat['relativeRight'],
                seat['relativeBottom'],
                seat['relativeLeft']]
                )

        # Store file to aws s3 blob storage
        status = uploadtoS3((jsonMap['boundary']['floormapname'] + '.csv'), filename, "floor-mappings/")
        if not status:
            raise Exception('Could not upload mapping file to s3')

        result = getImageFrmMySql(jsonMap['boundary']['floormapname'])
        if(len(result) == 0):
            raise Exception('Createmap: Could not find image name in database.')
        # print(result)
        url = 'https://' + AWS_CONFIG['bucket'] + '.s3.' + AWS_CONFIG['region'] + '.amazonaws.com/floor-images/' + result[0][2]
        print(url)
        # err = email.notify(filename,url,result[1])
        # if err:
            # raise Exception('Could not send email')

    except Exception as exp:
        print(exp)
        print(dir(exp))
        data = {
            'imagename': jsonMap['boundary']['floormapname'],
            'error': {
                'status': 'true',
                'message': 'Unexpected error'
            }
        }

    if not data:
        data = {
            'imagename': jsonMap['boundary']['floormapname'],
            'error': {
                'status': 'false',
                'message': 'No Errors'
            }
        }


    response = server.make_response(jsonify(data))
    response.headers.add('Access-Control-Allow-Origin','*')
    return response

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)