"""Render source-checked district roads and period bridge families."""
import asyncio
from functools import partial
from http.server import ThreadingHTTPServer
from threading import Thread
import review_river_network as runner
runner.REPORT_NAME='district-streets-checks.json'
runner.VIEWS={
 'streets-high-street':{'position':[-1190,150,260],'target':[-750,0,-150],'fov':65},
 'streets-bow-bridge':{'position':[-1075,10,180],'target':[-1040,2,112],'fov':50},
 'streets-pegshole':{'position':[-835,12,-65],'target':[-770,1,-115],'fov':55},
 'streets-city-crossings':{'position':[-815,105,-100],'target':[-660,0,-245],'fov':60},
 'streets-channelsea':{'position':[-300,35,-710],'target':[-248,2,-780],'fov':58},
 'streets-sugar-lane':{'position':[-730,125,285],'target':[-714,0,10],'fov':65},
 'streets-marshgate':{'position':[-1080,135,-130],'target':[-885,0,-290],'fov':65},
 'streets-three-mills':{'position':[-720,75,480],'target':[-590,0,390],'fov':65},
 'streets-abbey-regression':{'position':[-55,12,1],'target':[0,1,-45],'fov':65},
 'housing-mill-meads':{'position':[-470,190,-100],'target':[-450,0,-380],'fov':60},
 'housing-north-west':{'position':[-360,230,-470],'target':[-380,0,-750],'fov':65},
 'housing-north-east':{'position':[150,230,-480],'target':[170,0,-760],'fov':65},
 'housing-east':{'position':[430,220,30],'target':[420,0,-230],'fov':65},
 'housing-western-approach':{'position':[-1040,190,690],'target':[-920,0,440],'fov':65},
}
if __name__=='__main__':
 server=ThreadingHTTPServer(('127.0.0.1',0),partial(runner.QuietHandler,directory=str(runner.ROOT/'docs')))
 Thread(target=server.serve_forever,daemon=True).start()
 try:asyncio.run(runner.review(f'http://127.0.0.1:{server.server_port}'))
 finally:server.shutdown()
