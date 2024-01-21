from flask import Flask, request, jsonify
from datetime import datetime
from flask_mysqldb import MySQL
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

## POST /Upload --- Upload the image to the blob storage.
## Return the image name so that the image can be queried.
@server.route("/upload", methods=["POST"])
def upload():
    #logging.debug(f"{request.headers}")
    logging.debug(f"Image filename: {request.files['image'].filename}")
    logging.debug(f"Building name: {request.form['building']}")
    building = request.form['building']

    logging.debug(f"Floor: {request.form['floor']}")
    floor = request.form['floor']
    logging.debug(f"Email: {request.form['email']}")
    email = request.form['email']

    current_datetime = datetime.now().strftime("%Y%m%d")
    s = building + "_" + floor + "_" + current_datetime
    logging.debug(f"New Filename: {s}")

    # Store image to aws s3 blob storage
    f = request.files['image']
    #f.save('/Users/hyltonmcdonald/Desktop/gatewaydump/upload.png')
    imageURL = 'dummy.s3.image.url'

    # Store details mysql database
    isRequestStored = storerequest(email,s,imageURL)

    if isRequestStored == True:
        data = {
            'imagename': s,
            'imageURL': imageURL,
            'error': {
                'status': 'false',
                'message': 'No Errors'
            }
        }
    else:
        data = {
            'imagename': s,
            'imageURL': imageURL,
            'error': {
                'status': 'true',
                'message': 'Could not store request'
            }
        }
    json_data = jsonify(data)
    response = server.make_response(json_data)
    response.headers['Access-Control-Allow-Origin'] = '*'

    return response

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

## GET /floor-map-select/:id --- Get the image
## Return the image to use

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8080)