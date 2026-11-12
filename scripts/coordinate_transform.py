"""Approximate GCJ-02 conversion for candidate tracks, NOT a surveying transform.
Forward formula ported from wandergis/coordtransform (MIT, Copyright 2015 记忆的残骸).
https://github.com/wandergis/coordtransform ; license: data/licenses/coordtransform-MIT.txt
Inverse uses five residual-correction iterations. Numerical convergence is not accuracy.
Use only with the accompanying official-service comparison evidence for this study region.
"""
import math
PI=math.pi;A=6378245.0;EE=0.00669342162296594323

def wgs_to_gcj(lon,lat):
    if not (107<lon<115 and 30<lat<35):raise ValueError('Outside tested planning region')
    x=lon-105;y=lat-35
    dlat=-100+2*x+3*y+.2*y*y+.1*x*y+.2*math.sqrt(abs(x))
    dlat+=(20*math.sin(6*x*PI)+20*math.sin(2*x*PI))*2/3
    dlat+=(20*math.sin(y*PI)+40*math.sin(y/3*PI))*2/3
    dlat+=(160*math.sin(y/12*PI)+320*math.sin(y*PI/30))*2/3
    dlon=300+x+2*y+.1*x*x+.1*x*y+.1*math.sqrt(abs(x))
    dlon+=(20*math.sin(6*x*PI)+20*math.sin(2*x*PI))*2/3
    dlon+=(20*math.sin(x*PI)+40*math.sin(x/3*PI))*2/3
    dlon+=(150*math.sin(x/12*PI)+300*math.sin(x/30*PI))*2/3
    rad=lat/180*PI;magic=1-EE*math.sin(rad)**2;sqrt=math.sqrt(magic)
    return [lon+dlon*180/(A/sqrt*math.cos(rad)*PI),lat+dlat*180/((A*(1-EE))/(magic*sqrt)*PI)]

def gcj_to_wgs(lon,lat):
    x,y=lon,lat
    for _ in range(5):
        a,b=wgs_to_gcj(x,y);x-=a-lon;y-=b-lat
    return [x,y]
