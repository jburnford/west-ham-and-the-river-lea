"""Candidate photographic sightlines and the surrounding High Street frontages."""
import asyncio
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
import review_river_network as runner
runner.REPORT_NAME='wall-river-vista-checks.json'
runner.VIEWS={
 'marsh-ditches-overview':{'position':[-710,260,320],'target':[-400,0,70],'fov':60},
 'marsh-ditches-low':{'position':[-460,4,120],'target':[-500,1,-30],'fov':65},
 'marsh-ditches-east':{'position':[-265,12,120],'target':[-202,0,200],'fov':60},
 'sewer-high-street-overview':{'position':[-635,70,-300],'target':[-557,3.5,-375],'fov':60},
 'sewer-high-street-road':{'position':[-610,6,-300],'target':[-540,4,-410],'fov':60},
 'sewer-high-street-path':{'position':[-499,6,-322],'target':[-587,4,-386],'fov':60},
 'wall-vista-east':{'position':[-625,6,-262],'target':[-475,3,-262],'fov':60},
 'wall-vista-continuity':{'position':[-990,400,-80],'target':[-570,0,20],'fov':65},
 'wall-vista-lane-join':{'position':[-635,8,-133],'target':[-600,3,25],'fov':60},
 'tidal-three-mills':{'position':[-720,100,650],'target':[-590,0,440],'fov':65},
 'retained-old-lea':{'position':[-1220,140,230],'target':[-1170,0,0],'fov':60},
 'channelsea-tide-reference':{'position':[0,9.2,0],'target':[-20,0,180],'fov':56},
 'wall-vista-head':{'position':[-623,8,-245],'target':[-641,4,-95],'fov':48},
 'wall-vista-bridge':{'position':[-625,6,-262],'target':[-638,3,-105],'fov':48},
 'wall-vista-bank':{'position':[-627,5,-218],'target':[-645,4,-80],'fov':48},
 'high-street-infill':{'position':[-1020,130,190],'target':[-825,0,-50],'fov':60},
 'wall-vista-plan':{'position':[-633,230,-215],'target':[-634,0,-214],'fov':65},
}
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(runner.QuietHandler,directory=str(runner.ROOT/'docs')))
 Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(runner.review(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
