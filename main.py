import cherrypy
import socket
import webbrowser
import os
import hashlib
import urllib
import urllib2
import time
import threading
import sqlite3
import json
import datetime
import base64
import sys
from cherrypy.process.plugins import Monitor
reload(sys)
sys.setdefaultencoding('utf-8')


def getIP():
    # Returns the internal IP address of the current machine of which the server is to be hosted on 
    try:
        ip = socket.gethostbyname(socket.getfqdn())  # return fully-qualified domain name
    except:
        ip = socket.gethostbyname(socket.gethostname()) 
    print ip
    return ip


ext_ip = '122.62.141.222'
port = 10008  # TCP port to listen 
salt = "COMPSYS302-2017"
db_file = 'app.db'
curs = ''
upi = ""
pw = ""



def connectDatabse(db_file):
    # Establishes connection to database 
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        print(sqlite3.version)
    except:
        print 'could not  connect to database!'
    return conn


# Create table in database 
def createTable(db, create_table_sql):
    try:
        curs = db.cursor() 
        curs.execute(create_table_sql)
        db.commit() 
    except:
        print 'could not create table!'



def insertUser(user_details, db, cursor):
    """ Insert a user into the user_list table
    If user already exists, update their fields 
    """
    username = user_details[0]
    location = user_details[1]
    ip = user_details[2]
    port = user_details[3]
    login_time = user_details[4]
    status = 'Online'
    cursor.execute('''SELECT * FROM user_list WHERE username=?''', (username,))
    if (cursor.fetchone() is None): # if user does not exist 
        cursor.execute('''INSERT INTO user_list (username, location, ip, port, login_time)
        VALUES (?, ?, ?, ?, ?)''', (username, location, ip, port, login_time))
    else: # update existing user details 
        cursor.execute('''UPDATE user_list SET location=?, ip=?, port=?, login_time=? WHERE username=?''', (location, ip, port, login_time, username))
    cursor.execute('''UPDATE user_list SET status=? WHERE username=?''', (status, username))
    db.commit()


def initUsers(db):
    # Make sure user statuses from last session is reset to Offline
    cursor.execute('''UPDATE user_list SET status="Offline"''')
    db.commit()


def initProfile(user_details, db, cursor):
    """Create a row for a user's profile and insert some default values 
    This function is only called if the user does not already exist in the database
    """
    username = user_details[0]
    cursor.execute('''SELECT * FROM profiles WHERE username=?''', (username,))
    if (cursor.fetchone() is None):
        location = user_details[1]
        if (location == '0'):
            location_str = 'Lab'
        elif (location == '1'): 
            location_str = 'UoA Wifi'
        elif (location == '2'): 
            location_str = 'Outside world'
        else: 
            location_str = '???'
        cursor.execute('''INSERT INTO profiles (username, fullname, position, description, location, picture)
        VALUES (?,?,?,?,?,?)''', (username, username, 'student', 'this is my description', location_str, 'http://i.imgur.com/gRTdtu0.png'))
        db.commit()


def initPeople(db):
    """Populate the users panel with the list of users 
    Used in HTML 
    """
    people = ""
    curs = db.execute("""SELECT id, username, location, ip, port, login_time, status from user_list""")
    for row in curs: 
        people += '<li class="person" data-chat="' + row[1] + '">'
        people += '<img src="" alt="" />'
        people += '<span class="name">' + row[1] + '</span>'
        people += '<span class="time"> </span>'
        people += '<span class="preview">' + row[6] + '</span>'
    return people


def initChat(db):
    # Initialise chat panel HTML 
    chat = ""
    curs = db.execute("""SELECT id, username, location, ip, port, login_time from user_list""")
    for row in curs: 
        chat += '<div class="chat" data-chat="' + row[1] + '">'
        chat += '</div>'
    return chat


class MainApp(object):
    msg = " "
    chat_error = ""
    chat = ""
    conversation = ""
    profile_html = ""

    global db
    db = connectDatabse(db_file)
    global cursor
    cursor = db.cursor()
    # Make user list db
    createTable(db, """CREATE TABLE IF NOT EXISTS user_list ( id INTEGER PRIMARY KEY, username TEXT, location INTEGER, ip TEXT, port INTEGER, login_time TEXT, status TEXT);""")
    # Make messages db 
    createTable(db, """CREATE TABLE IF NOT EXISTS messages ( id INTEGER PRIMARY KEY, sender TEXT, recipient TEXT, message TEXT, stamp INTEGER, mime TEXT);""")
    # Make profiles db 
    createTable(db, """CREATE TABLE IF NOT EXISTS profiles ( id INTEGER PRIMARY KEY, username TEXT, fullname TEXT, position TEXT, description TEXT, location TEXT, picture TEXT);""")

    # Init chat panels
    initUsers(db)
    people = initPeople(db)
    conv = initChat(db)

    @cherrypy.expose
    def index(self):
        # Landing page; entry point of application (login page)
        page = open('main.html', 'r').read().format(message=self.msg)
        return page

    @cherrypy.expose
    # Index page
    def home(self):
        try:
            self.getList()
            self.people = initPeople(db)
            page = open('loggedin.html', 'r').read().format(username=cherrypy.session['username'], chat_error=self.chat_error, chat_messages=self.chat, conversation=self.conversation, people=self.people, chat=self.conv, profile_html=self.profile_html)
        except KeyError:
            self.msg = "Session expired, please login again"
            raise cherrypy.HTTPRedirect('/')
        return page

    
    @cherrypy.expose
    def signin(self, username=None, password=None):
        """Sign-in function.  Called when user submits login form
        Reports user to login server.  Starts thread for continual reporting to login server 
        """
        hash_pw = hashlib.sha256(str(password+salt)).hexdigest() # hash password 
        error = self.report(username, hash_pw) # report to login server
        print error
        if (int(error) == 0): # if successfully reported, start session and report thread 
            global upi
            global pw
            upi = username
            pw = hash_pw
            cherrypy.session['username'] = username
            cherrypy.session['password'] = hash_pw 
            self.report_thread.start()
            raise cherrypy.HTTPRedirect('/home')
        else:
            print "login failed!2"
            self.msg = "Incorrect credentials, please try again" # prompt user to log in again 
            raise cherrypy.HTTPRedirect('/') # redirect to login page

    @cherrypy.expose
    def report(self, username, hash_pw):
        # Report to login server
        try:
            url = 'http://cs302.pythonanywhere.com/report?username=' + str(username)
            url += '&password=' + str(hash_pw)  + '&location=' + '2' + '&ip=' + ext_ip
            url += '&port=' + str(port) + '&enc=0'
            print "logged in as " + username
        except:
            self.msg = 'Login failed!'
            print "login failed!"
            raise cherrypy.HTTPRedirect('/')
        # Getting the error code from the server
        response_message = (urllib2.urlopen(url)).read()
        response = str(response_message)[0]
        # Display response message from the server
        print "Server response: " + str(response_message)
        return response

    @cherrypy.expose
    # Thread to report to report to login server continually 
    def reportThread():
        print 'reporting'
        try:
            url = 'http://cs302.pythonanywhere.com/report?username=' + upi
            url += '&password=' + pw + '&location=' + '0' + '&ip=' + ext_ip
            url += '&port=' + str(port) + '&enc=0'
            print url
        except:
            print 'could not report!'
        response_message = (urllib2.urlopen(url)).read()
        response = str(response_message)[0]
        # Display response message from the server
        print "Server response: " + str(response_message)
        return
          
    # Thread to report to login server regularly
    # Will report once every 60 seconds 
    report_thread = Monitor(cherrypy.engine, reportThread, frequency=60)

    @cherrypy.expose
    def signout(self):
        # Log user out from login server 
        url = 'http://cs302.pythonanywhere.com/logoff?username=' + str(cherrypy.session['username']) + '&password=' + str(cherrypy.session['password']) + '&enc=0'
        self.report_thread.stop() # stop regularly reporting to login server
        response = (urllib2.urlopen(url)).read()
        error = str(response)[0]
        if (int(error) == 0):
            self.msg = 'Logout successful!'
            cherrypy.session.clear() # clear user session 
            raise cherrypy.HTTPRedirect('/')

    def getList(self):
        # Get list of users currently online
        try: 
            url = 'http://cs302.pythonanywhere.com/getList?username=' + str(cherrypy.session['username']) + '&password=' + str(cherrypy.session['password']) + '&enc=0'
        except: 
            print 'getList failed!'
            raise cherrypy.HTTPRedirect('/')

        response = str((urllib2.urlopen(url)).read())
        error = int(response[0])
        if (error == 0):
            usernames = []
            # Format user list 
            user_details = response.replace("0, Online user list returned", "")
            user_details = user_details.split() 
            for i in range (len(user_details)):
                if (',' in user_details[i]):
                    split_details = user_details[i].split(',')
                    if (split_details[0] != cherrypy.session['username']):
                        usernames.append(split_details[0])
                        insertUser(split_details, db, cursor)
                        initProfile(split_details, db, cursor)
            return ", ".join(usernames)

    @cherrypy.expose
    def ping(self, sender=None):
        """Implements ping API.  
        Always returns 0 to indicate server is online
        """
        return '0'

    @cherrypy.expose 
    def listAPI(self):
        """Implements listAPI API
        Returns APIs supported by this client 
        """
        return '/ping [sender] /listAPI /receiveMessage [sender] [destination] [message] [stamp] /receiveFile [sender] [destination] [file] [filename] [content_type] [stamp] /getProfile [profile_username] [sender] /receiveFile [sender] [destination] [file] [filename] [content_type] [stamp]'

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveMessage(self):
        """Implements receiveMessage API
        """
        data = cherrypy.request.json # Retrieve json input 
        # Put into db 
        cursor.execute('''INSERT INTO messages (sender, recipient, message, stamp)
        VALUES (?, ?, ?, ?)''', (data['sender'], data['destination'], data['message'], data['stamp']))
        db.commit()
        self.chat_error = 'Someone sent you a message!: ' + data['message']
        print self.chat_error
        return '0'

    @cherrypy.expose 
    def sendMessage(self, recipient, message):
        """Sends a message 
        Calls recipient's receiveMessage
        """
        current_time = time.time() # get timestamp 
        curs = db.execute("""SELECT id, username, location, ip, port, login_time, status from user_list""")
        for row in curs: 
            if (recipient == row[1]):
                recipient_ip = row[3]
                recipient_port = row[4]
                if (row[6] != 'Online'):
                    # If user is not online, message cannot be sent
                    return 'Your message could not be delivered!'

                post_data = {"sender": cherrypy.session['username'], "destination": recipient, "message": message, "stamp": int(current_time)}
                post_data = json.dumps(post_data) # json encode
                url = 'http://' + str(recipient_ip) + ":" + str(recipient_port) + '/receiveMessage?'
                try:
                    req = urllib2.Request(url, post_data, {'Content-Type': 'application/json'})
                    response = urllib2.urlopen(req).read()
                except: 
                    return 'Your message could not be delivered!'
                print response
                if (str(response[0]) == '0'): # check if message was successfully sent 
                    self.chat = 'Message sent!'
                    # only insert into database if successfully sent
                    cursor.execute('''INSERT INTO messages (sender, recipient, message, stamp)
                    VALUES (?, ?, ?, ?)''', (cherrypy.session['username'], recipient, message, current_time))
                    db.commit()
                    return 'Your message has been sent!' # display on page successful message receipt
                else:
                    error = 'Your message could not be delivered!'
                    print error
                    self.chat = error
                    return error
                break
        cherrypy.HTTPRedirect('/home')

    @cherrypy.expose
    def updateConversation(self, username):
        """Formats the chat panel (chat bubbles)
        Responsible for in-line media content display
            i.e. plaintext, image, video, audio
        Periodically called via jQuery
        Returns HTML of the current conversation
        Dynamically updates conversation 
        """
        conversation = ""
        # query database for messages 
        curs = db.execute("""SELECT id, sender, recipient, message, stamp, mime from messages""")
        # format messages 
        for row in curs:
            # only insert messages which were sent or received by this user
            if ((cherrypy.session['username'] == row[1]) or (cherrypy.session['username'] == row[2])):
                if (username == row[1]): # recipient
                    conversation += '<div class="bubble you">'
                    if row[5] is None: # plaintext message
                        conversation += row[3] + '</div>'
                    elif 'image' in row[5]:
                        conversation += '<img src="data:' + row[5] + ';base64,'
                        conversation += row[3] + '"/></div>'
                    elif 'audio' in row[5]:
                        conversation += '<audio controls src="data:' + row[5] + ';base64,'
                        conversation += row[3] + '"/></div>'
                    elif 'video' in row[5]:
                        conversation += '<video controls><source type="video/webm" src="data:video/webm;base64,'
                        conversation += row[3] + '">'
                        conversation += '<source type=' + row[5] + 'src="' + row[5]
                        conversation += ';base64,' + row[3] + '"></video></div>'
                elif (username == row[2]): # sender
                    conversation += '<div class="bubble me">'
                    if row[5] is None:
                        conversation += row[3] + '</div>'
                    elif 'image' in row[5]:
                        conversation += '<img src="data:' + row[5] + ';base64, '
                        conversation += row[3] + '"/></div>'
                    elif 'audio' in row[5]:
                        conversation += '<audio controls src="data:' + row[5] + ';base64,'
                        conversation += row[3] + '"/></div>'
                    elif 'video' in row[5]:
                        conversation += '<video controls><source type="video/webm" src="data:video/webm;base64,'
                        conversation += row[3] + '">'
                        conversation += '<source type=' + row[5] + 'src="' + row[5]
                        conversation += ';base64,' + row[3] + '"></video></div>'
        return conversation

    @cherrypy.expose
    @cherrypy.tools.json_in()
    def receiveFile(self):
        """Implements receiveFile API
        Writes file to local disk and stores in database
        """
        print 'Someone sent you a file! '
        data = cherrypy.request.json
        sender = data['sender']
        recipient = data['destination']
        file = data['file']
        filename = data['filename']
        mime = data['content_type']
        print filename
        stamp = data['stamp']

        # Write to local disk 
        with open(filename, "wb") as fh:
            fh.write(file.decode('base64'))

        # Insert in database 
        try:
            cursor.execute('''INSERT INTO messages (sender, recipient, message, stamp, mime)
            VALUES (?, ?, ?, ?, ?)''', (sender, recipient, file, stamp, mime))
            db.commit()
        except:
            print 'failed to put file in db!'

        return '0'

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def sendFile(self, send_file, recipient):
        """Sends files 
        Calls recipient's receiveFile API
        """
        stamp = int(time.time())
        enc_file = base64.b64encode(send_file.file.read()) # encode as base64 string
        post_data = {"sender": cherrypy.session['username'], "destination": recipient, "file": enc_file, "stamp": stamp, "filename": send_file.filename, "content_type": str(send_file.content_type)}
        post_data = json.dumps(post_data)

        # send request
        curs = db.execute("""SELECT id, username, location, ip, port, login_time from user_list""")
        for row in curs: 
            if (recipient == row[1]):
                recipient_ip = row[3]
                recipient_port = row[4]
                url = 'http://' + str(recipient_ip) + ":" + str(recipient_port) + '/receiveFile?'
                print url
                req = urllib2.Request(url, post_data, {'Content-Type': 'application/json'})

                response = urllib2.urlopen(req).read()
                print response
                break
        if (str(response[0]) == '0'):  # check if file was successfully sent 
            # put file in db 
            cursor.execute('''INSERT INTO messages (sender, recipient, message, stamp, mime)
            VALUES (?, ?, ?, ?, ?)''', (cherrypy.session['username'], recipient, enc_file, stamp, str(send_file.content_type)))
            db.commit()
        raise cherrypy.HTTPRedirect('/home')

    @cherrypy.expose
    @cherrypy.tools.json_in()
    @cherrypy.tools.json_out()
    def getProfile(self, user=None):
        """Implements getProfile API
        """
        if user is None: # viewing own profile
            data = cherrypy.request.json
            username = data['profile_username']
        else:
            username = user

        # In order to output as dict, need to utilise row_factory
        db_row = sqlite3.connect(db_file, check_same_thread=False)
        db_row.row_factory = sqlite3.Row
        c = db_row.cursor()
        c.execute('''SELECT * FROM profiles WHERE username=?''', (username,))
        profile_data = c.fetchone()
        return dict(profile_data) # format as dict 

    @cherrypy.expose
    @cherrypy.tools.json_out()
    def retrieveProfile(self, user=None):
        """Get other users' profiles
        Calls recipient's getProfile
        """
        try:
            cursor.execute('''SELECT * FROM user_list WHERE username=?''', (user,))
            row = cursor.fetchone()
            ip = row[3]
            port = row[4]
            url = 'http://' + str(ip) + ':' +str(port) + '/'
            post_data = {"profile_username": user, "sender": cherrypy.session['username']}
            post_data = json.dumps(post_data)
            getProfile_url = url + 'getProfile?'
            req = urllib2.Request(getProfile_url, post_data, {'Content-Type': 'application/json'})
            response = urllib2.urlopen(req).read()
            data = json.loads(response)  # json encode request
            try:
                # update db 
                cursor.execute('''SELECT * FROM profiles WHERE username=?''', (user,))
                cursor.execute('''UPDATE profiles SET fullname=?, position=?, description=?, location=?, picture=? WHERE username=?''', (data['fullname'], data['position'], data['description'], data['location'], data['picture'], user))
            except:
                print 'user does not exist in db!'
        except:
            print 'user does not exist!'
        db.commit()


    @cherrypy.expose
    def viewProfile(self, user=None):
        """View someone's profile
        """
        try:
            if user is None: # view own profile
                username = cherrypy.session['username']
            else:
                username = user
                try:
                    cursor.execute('''SELECT * FROM user_list WHERE username=?''', (user,))
                    row = cursor.fetchone()
                    if (row[6] != 'Offline'):
                        # Try to call their getProfile if they are not offline
                        self.retrieveProfile(user=username)
                except:
                    print 'could not retrieve profile!'

            # retrieve profile from own db
            cursor.execute('''SELECT * FROM profiles WHERE username=?''', (username,))
            row = cursor.fetchone()
            # Format profile
            profile_html = '<img src="' + row[6] + '">' + '<br><br>'
            profile_html += 'Username: ' + row[1] + '<br>'
            profile_html += 'Full name: ' + row[2] + '<br>'
            profile_html += 'Position: ' + row[3] + '<br>'
            profile_html += 'Description: ' + row[4] + '<br>'
            profile_html += 'Location: ' + row[5] + '<br>'
            return profile_html
        except:
            self.msg = 'Session expired, please login again'
            raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def myProfile(self, user=None):
        """Page showing my (current logged in user) profile
        """
        try:
            if user is None:
                username = cherrypy.session['username']
            else:
                username = user

            cursor.execute('''SELECT * FROM profiles WHERE username=?''', (username,))
            row = cursor.fetchone()
            print row
            profile_data = '<img src="' + row[6] + '">' + '<br><br>'
            profile_data += 'Username: ' + row[1] + '<br>'
            profile_data += 'Full name: ' + row[2] + '<br>'
            profile_data += 'Position: ' + row[3] + '<br>'
            profile_data += 'Description: ' + row[4] + '<br>'
            profile_data += 'Location: ' + row[5] + '<br>'
            page = open('profile.html', 'r').read().format(profile_data=str(profile_data))
            return page
        except:
            self.msg = 'Session expired, please login again'
            raise cherrypy.HTTPRedirect('/')

    @cherrypy.expose
    def editProfile(self, parameter, changes, user=None):
        """Make changes to my (current logged in user) profile
        """
        if user is None:
            username = cherrypy.session['username']
        else:
            username = user

        if (parameter == 'fullname'):
            cursor.execute('''UPDATE profiles SET fullname=? WHERE username=?''', (changes, username,))
        elif (parameter == 'position'):
            cursor.execute('''UPDATE profiles SET position=? WHERE username=?''', (changes, username,))
        elif (parameter == 'desc'):
            cursor.execute('''UPDATE profiles SET description=? WHERE username=?''', (changes, username,))
        elif (parameter == 'location'):
            cursor.execute('''UPDATE profiles SET location=? WHERE username=?''', (changes, username,))
        elif (parameter == 'picture'):
            cursor.execute('''UPDATE profiles SET location=? WHERE username=?''', (changes, username,))
        else:
            print "invalid parameter!"

        db.commit()
        raise cherrypy.HTTPRedirect('/myProfile')

    webbrowser.open_new('http://%s:%d/' % (ext_ip, port))

def runMainApp():
    conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './static'
         }
    }

    cherrypy.tree.mount(MainApp(), "/", conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': port,
                        'tools.encode.on': True,
                        'tools.encode.encoding': 'utf-8'
                            })

    cherrypy.engine.start()  # start webserver

    cherrypy.engine.block()  # stop doing anything else 
    
runMainApp()