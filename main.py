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

# Returns the internal IP address of the current machine of which the server is to be hosted on 
def getIP():
    try:
        ip = socket.gethostbyname(socket.getfqdn())  # return fully-qualified domain name
    except:
        ip = socket.gethostbyname(socket.gethostname())
    # if (not ip) or (ip.startswith('127.')):
    #   s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # create new socket 
 #        s.connect(("8.8.8.8", 80)) # open socket to google's DNS server 
 #        ip = s.getsockname()[0] # take address from that connection 
   
    return ip


local_ip = getIP() # socket to listen  
ext_ip = '122.62.141.222'
#ip = "127.0.0.1"
port = 10008  # TCP port to listen 
salt = "COMPSYS302-2017"
db_file = 'app.db'
curs = ''


def connectDatabse(db_file):
    try:
        conn = sqlite3.connect(db_file, check_same_thread=False)
        print(sqlite3.version)
    except Error as e:
        print(e)
    # finally: 
    #   conn.close()
    return conn


def createTable(db, create_table_sql):
    try:
        curs = db.cursor() 
        curs.execute(create_table_sql)
        db.commit() 
    except Error as e:
        print(e)

# def formatUserList(response):
#   user_details = response.replace("0, Online user list returned", "")

#   user_details = user_details.split() 
#   for i in range (len(user_details)):
#       if (',' in user_details[i]):
#           split_details = user_details[i].split(',')
#           if (split_details[0] != cherrypy.session['username']):
#               print split_details[0]
#               insertUser(split_details, db, cursor)
#               # TODO: put in db 

def insertUser(user_details, db, cursor): 
    username = user_details[0]
    print username 
    cursor.execute('''SELECT * FROM user_list WHERE username=?''', (username,))
    if (cursor.fetchone() is None):
        location = user_details[1]
        ip = user_details[2]
        print ip
        port = user_details[3]
        login_time = user_details[4]
        cursor.execute('''INSERT INTO user_list (username, location, ip, port, login_time)
        VALUES (?, ?, ?, ?, ?)''', (username, location, ip, port, login_time))
        db.commit() 

class MainApp(object):
    msg = " "
    global db 
    db = connectDatabse(db_file)
    global cursor 
    cursor = db.cursor()
    createTable(db, """CREATE TABLE IF NOT EXISTS user_list ( id INTEGER PRIMARY KEY, username TEXT, location INTEGER, ip TEXT, port INTEGER, login_time TEXT);""")
    createTable(db, """CREATE TABLE IF NOT EXISTS messages ( id INTEGER PRIMARY KEY, sender TEXT, recepient TEXT, message TEXT, stamp INTEGER);""")


    @cherrypy.expose
    def index(self):
        page = open('main.html', 'r').read().format(message=self.msg)
        #page = html.read()
        logged_in = False
        #page = self.checkLogin(page)
        return page

    @cherrypy.expose
    def home(self):
        try:
            page = open('loggedin.html', 'r').read().format(username=cherrypy.session['username'], user_list=self.getList())
        except KeyError:
            msg = "Session expired"
            raise cherrypy.HTTPRedirect('/')
        #html.close()
        #page = self.checkLogin(page)
        return page

    @cherrypy.expose
    def signin(self, username=None, password=None): 
        hash_pw = hashlib.sha256(str(password+salt)).hexdigest()
        error = self.authoriseLogin(username, hash_pw)
        print error
        if (int(error) == 0):
            cherrypy.session['username'] = username
            cherrypy.session['password'] = hash_pw 
            self.t = threading.Thread(target=self.report, args=[cherrypy.session['username'], cherrypy.session['password'], False])
            self.daemon = True
            self.t.start()
            raise cherrypy.HTTPRedirect('/home')
        else:
            print "login failed!2"
            self.msg = "Incorrect credentials, please try again"
            raise cherrypy.HTTPRedirect('/')

       
    @cherrypy.expose
    def report(self, username, hash_pw, first_login):
        response = 0
        if (int(response) == 0):
            #time.sleep(30)
            try:
                url = 'http://cs302.pythonanywhere.com/report?username=' + str(username)
                url += '&password=' + str(hash_pw)  + '&location=' + '2' + '&ip=' + ext_ip # TODO: DON'T HARDCODE LOCATION
                url += '&port=' + str(port) + '&enc=0'
                print "logged in! " 
            except:
                print "login failed!"
                raise cherrypy.HTTPRedirect('/')
            # Getting the error code from the server
            response_message = (urllib2.urlopen(url)).read()
            response = str(response_message)[0]
            # Display response message from the server
            print "Server response: " + str(response_message)
            if (response == 0):
                print cherrypy.session['username']
            return response
         

    def authoriseLogin(self, username, hash_pw):
        return self.report(username, hash_pw, True)

    def checkLogin(self, page):
        logged_in = True
        try:
            username = cherrypy.session['username']
        except KeyError:
            logged_in = False

        if (logged_in == True):
            html = open('loggedin.html', 'r')
            page = str(html.read())
            html.close()
            page = self.checkLogin(page)

        return page

    @cherrypy.expose
    def signout(self):
        try:
            url = 'http://cs302.pythonanywhere.com/logoff?username=' + str(cherrypy.session['username']) + '&password=' + str(cherrypy.session['password']) + '&enc=0'
        except: 
            print 'logout failed'
        response = (urllib2.urlopen(url)).read()
        error = str(response)[0]
        if (int(error) == 0):
            self.msg = 'Logout successful!'
            cherrypy.session.clear() # clear user session 
            raise cherrypy.HTTPRedirect('/')

    def getList(self): 
        try: 
            url = 'http://cs302.pythonanywhere.com/getList?username=' + str(cherrypy.session['username']) + '&password=' + str(cherrypy.session['password']) + '&enc=0'
        except: 
            print 'getList failed!'
            raise cherrypy.HTTPRedirect('/')

        response = str((urllib2.urlopen(url)).read())
        error = int(response[0])
        if (error == 0):
            user_list = response
            usernames = []
            page = ''
            user_details = response.replace("0, Online user list returned", "")
            user_details = user_details.split() 
            for i in range (len(user_details)):
                if (',' in user_details[i]):
                    split_details = user_details[i].split(',')
                    if (split_details[0] != cherrypy.session['username']):
                        usernames.append(split_details[0])
                        insertUser(split_details, db, cursor)
            return ", ".join(usernames)

    @cherrypy.expose
    def ping(sender):
        print 'SOMEONE PINGED YOU!!!!!'
        return 0

    @cherrypy.expose 
    def receiveMessage(self, sender, destination, message, stamp, markdown=0, enc=0, hashing=0, hash=None, decryption_key=None):
        decoded_msg = message
        print decoded_msg
        #now = time.strftime("%d-%m-%Y %I:%M %p",time.localtime(float(time.mktime(time.localtime()))))
        #print nows
        cursor.execute('''INSERT INTO messages (sender, recepient, message, stamp)
        VALUES (?, ?, ?, ?)''', (sender, destination, decoded_msg, stamp))
        db.commit()
        return '1'

    @cherrypy.expose 
    def sendMessage(self, recepient, message):
        print recepient
        current_time = time.time()
        curs = db.execute("""SELECT id, username, location, ip, port, login_time from user_list""")
        for row in curs: 
            #print row[1]
            if (recepient == row[1]):
                recepient_ip = row[3]
                #print recepient_ip
                recepient_port = row[4]
                #print recepient_port

                # url = 'http://' + str(recepient_ip) + ':' + str(recepient_port)
                # url += '/' + 'receiveMessage?sender=' + cherrypy.session['username']
                # url += '&destination=' + str(recepient) + '&message=' + json_msg
                # url += '&stamp=' + str(int(current_time))
                post_data = {"sender": cherrypy.session['username'], "destination": recepient, "message": message, "stamp": int(current_time)}
                url = 'http://' + str(recepient_ip) + ":" + str(recepient_port) + '/receiveMessage?'
                print url
                req = urllib2.Request(url, post_data, {'Content-Type': 'application/json'})
                response = urllib2.urlopen(req)
                print response

                

                # success = (urllib2.urlopen(url)).read()
                # if (success == 1): 
                #     print 'message sent!'
                # else: 
                #     print 'message failed to send :-('
                # break
        cherrypy.HTTPRedirect('/home')

 
    #webbrowser.open_new('http://%s:%d/login' % (local_ip, port))

def runMainApp():
    conf = {
         '/': {
             'tools.sessions.on': True,
             'tools.staticdir.root': os.path.abspath(os.getcwd())
         },
         '/generator': {
             'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
             'tools.response_headers.on': True,
             'tools.response_headers.headers': [('Content-Type', 'text/plain')],
         },
         '/static': {
             'tools.staticdir.on': True,
             'tools.staticdir.dir': './static'
         }
    }

    cherrypy.tree.mount(MainApp(), "/", conf)

    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                        'server.socket_port': port,
                        #'engine.autoreload.on': True,
                        })


    cherrypy.engine.start() # start webserver

    cherrypy.engine.block() # stop doing anything else 
    #cherrypy.engine.stop() # terminate; stop the channel of the bus 
    #cherrypy.server.unsubscribe() # disable built-in HTTP server 

runMainApp()