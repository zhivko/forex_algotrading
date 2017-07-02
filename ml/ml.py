"""
Find the support/resistance lines in a chart

JonV / May 16 2015
"""

import sys
import pandas
import numpy as np
import json
from sklearn.cluster import MeanShift, estimate_bandwidth

from  http.server import BaseHTTPRequestHandler,HTTPServer
from os import curdir, sep

PORT_NUMBER = 8000


class myHandler(BaseHTTPRequestHandler):
	
	#Handler for the GET requests
	def do_GET(self):
		if self.path=="/":
			self.path="/index_example2.html"

		try:
			#Check the file extension required and
			#set the right mime type

			sendReply = False
			if self.path.endswith(".html"):
				mimetype='text/html'
				sendReply = True
			if self.path.endswith(".jpg"):
				mimetype='image/jpg'
				sendReply = True
			if self.path.endswith(".gif"):
				mimetype='image/gif'
				sendReply = True
			if self.path.endswith(".js"):
				mimetype='application/javascript'
				sendReply = True
			if self.path.endswith(".json"):
				mimetype='application/json'
				sendReply = True
			if self.path.endswith(".css"):
				mimetype='text/css'
				sendReply = True

			if sendReply == True:
				#Open the static file requested and send it
				#f = open(curdir + sep + self.path) 
				#self.send_response(200)
				#self.send_header('Content-type',mimetype)
				#self.end_headers()
				#self.wfile.write(f.read())
				#f.close()
				
				
				in_file = open(curdir + sep + self.path, "rb") # opening for [r]eading as [b]inary
				data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)
				in_file.close()
				
				self.send_response(200)
				self.send_header('Content-type',mimetype)
				self.end_headers()
				self.wfile.write(data)
				
				
				
			return


		except IOError:
			self.send_error(404,'File Not Found: %s' % self.path)
	
def main(filename):
	#This class will handles any incoming request from
	#the browser 
	try:
		#Create a web server and define the handler to manage the
		#incoming request
		server = HTTPServer(('', PORT_NUMBER), myHandler)
		print('Started httpserver on port ' , PORT_NUMBER)
		#Wait forever for incoming htto requests
		server.serve_forever()
	except KeyboardInterrupt:
		print('^C received, shutting down the web server')
		server.socket.close()

	# read csv files with daily data per tick
	df = pandas.read_csv(filename, parse_dates=[0], index_col=0, names=['Date_Time', 'Buy', 'Sell'], date_parser=lambda x: pandas.to_datetime(x, format="%d/%m/%y %H:%M:%S"))
	# group by day and drop NA values (usually weekends)
	grouped_data = df.dropna()
	ticks_data = grouped_data['Sell'].resample('24H').ohlc()
    
    # use 'ask'
	sell_data = grouped_data.as_matrix(columns=['Sell'])

    # calculate bandwidth (expirement with quantile and samples)
	bandwidth = estimate_bandwidth(sell_data, quantile=0.1, n_samples=100)
	ms = MeanShift(bandwidth=bandwidth, bin_seeding=True)
	# fit the data
	ms.fit(sell_data)
	ml_results = []
	for k in range(len(np.unique(ms.labels_))):
		my_members = ms.labels_ == k
		values = sell_data[my_members, 0]    

		# find the edges
		ml_results.append(min(values))
		ml_results.append(max(values))
    # export the data for the visualizations
	ticks_data.to_json('ticks.json', date_format='iso', orient='index')
	# export ml support resisistance
	with open('ml_results.json', 'w') as f:
		f.write(json.dumps(ml_results))
	print("Done. Goto 0.0.0.0:8000/chart.html")
	

if __name__ == "__main__":
    if (len(sys.argv) < 2):
        print('ml.py <inputfile.csv>')
        sys.exit(2)
    main(sys.argv[1])


