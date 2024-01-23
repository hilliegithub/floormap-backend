from flask import Flask, request, jsonify
from datetime import datetime
from flask_mysqldb import MySQL
import boto3
from botocore.exceptions import ClientError
import os
import logging

server = Flask(__name__)
mysql = MySQL(server)
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
    building = request.form['building']
    floor = request.form['floor']
    email = request.form['email']

    current_datetime = datetime.now().strftime("%Y%m%d%H%M%S")
    newFilename = building + "_" + floor + "_" + current_datetime
    newFilename = newFilename.lower()

    # Store image to aws s3 blob storage
    status = uploadtoS3(newFilename, currentFileLocation)

    # Store details mysql database
    isRequestStored =  False
    if status["stat"]:
        isRequestStored = storerequest(email,newFilename,status["url"])

    if isRequestStored and status["stat"]:
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
def uploadtoS3(newFilename, currentFileLocation):
    old_filename, ext = os.path.splitext(currentFileLocation)
    bucket = AWS_CONFIG['bucket']
    object_key = "floor-images/" + newFilename + ext
    url = 'https://' + AWS_CONFIG['bucket'] + '.s3.' + AWS_CONFIG['region'] + '.amazonaws.com/' + object_key

    #s3_client = boto3.client('s3')
    try:
        print("test")
        #response = s3_client.upload_file(currentFileLocation, bucket, object_key)
    except ClientError as e:
        logging.error(e)
        return {"stat" : False, "url" : url}
    print(url)
    return {"stat" : True, "url" :url}

def storerequest(email,filename,imageurl):
    try:
        cur = mysql.connection.cursor()
        res = cur.execute(
            "INSERT INTO request (email,floormapname,imageurl) VALUES (%s,%s,%s);", (email,filename,imageurl,)
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
            "SELECT imageurl FROM request WHERE floormapname=%s", (imgname,)
        )
        res = cur.fetchall()
        cur.close()

        for id in res:
            print(id)

        return id

    except Exception as err:
        logging.debug(err)
        return ''

## GET /floor-map-select/:id --- Get the image
## Return the image to use
@server.route("/getimage", methods=["GET"])
def getimage():
    imgName = request.args.get("img")
    #print(imgName)

    if not imgName:
        data = {"status": False,"imgurl": "../../assets/floorplan.png"}
        response = server.make_response(jsonify(data))
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response


    ## get the image url from database
    imgurl = getImageFrmMySql(imgName)

    data = {"status": True,"imgurl": imgurl[0]}
    response = server.make_response(jsonify(data))
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)