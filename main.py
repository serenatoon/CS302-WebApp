import cherrypy
import socket
import webbrowser
import os

def getIP():
	#try:
		# internal IP 
		#return socket.gethostbyname(socket.getfqdn())
	#except:
	return "localhost"	

ip = getIP() # socket to listen  
port = 10032 # TCP port to listen on 

class main(object):
	@cherrypy.expose
	def home(self):
		html = open('main.html')
		page = html.read()
		return page
		#return "Hello, world!"

	webbrowser.open_new('http://%s:%d/home' % (ip, port))



def runMain():
	conf = {
	'/': {
		'tools.sessions.on': True, # enable sessions to synchronise activity between users 
		'tools.staticdir.root:': os.path.abspath(os.getcwd()) # serve whole dir
		}
	}

	cherrypy.tree.mount(main(), "/", conf)

	cherrypy.config.update({'server.socket_host': ip,
						'server.socket_port': port,
						#'engine.autoreload.on': True,
						})

	print "starting........"

	cherrypy.engine.start() # start webserver

	cherrypy.engine.block() # stop doing anything else 

runMain()