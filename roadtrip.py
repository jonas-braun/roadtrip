#!/usr/bin/env python2.7


''' a program to download images from google street view
    for a time-lapse movie.
'''




import os
import sys
import urllib2
import time

import json

from itertools import izip_longest
from math import radians, cos, sin, asin, sqrt, pi, pow, atan, atan2, degrees

import numpy as np
import scipy.ndimage
import matplotlib.pyplot as plt

# using a script for decoding google polylines
# https://gist.github.com/2031157.git
import gpoly   # import lib.gpoly.gistfile1 as gpoly




class Coordinate(object):
    ''' an image url '''
    
    fov = 120   # field of view in degrees (max 120 deg)
    size = 640  # image size in pixels     (max 640px)

    keyfile = 'api.key'

    def __init__(self, coordinates, heading=270.):
        self.coordinates = [ float(coord) for coord in coordinates ]  # lat, lon coordinates
        self.heading = heading  # direction in which to look (north: 0, east:90, ...)
        try:
            with open(self.keyfile) as f:
                self.key = f.readline() # google api key
        except IOError:
            self.key = None
            print "No API key."


    def url(self):
        base_url = 'https://maps.googleapis.com/maps/api/streetview?'
        base_url = base_url + 'size=%dx%d'%(self.size, self.size)
        base_url = base_url + '&fov=%d'%(self.fov)
        base_url = base_url + '&heading=%f'%(self.heading)
        base_url = base_url + '&location=%s,%s'%(self.coordinates[0], self.coordinates[1])
        if self.key:
            base_url = base_url + '&key=' + self.key
        return base_url
               

    def url2(self):
        panoid = self.download_info()
        x = int(self.heading / 360 * 8)
        base_url = 'https://cbk0.google.com/cbk?output=tile'
        base_url = base_url + '&panoid=%s'%(panoid) # 'mwSJK8cFs3tfisKApVwujw')
        base_url = base_url + '&zoom=%d'%(3)    # 8x4 tiles 512x512px each
        base_url = base_url + '&x=%d'%(6)
        base_url = base_url + '&y=%d'%(1)
        return base_url

    def download_info(self):
        base_url = 'https://cbk0.google.com/cbk?output=json'
        info_url = base_url + '&ll=%f,%f'%(self.coordinates[0], self.coordinates[1])
        try:
            internet = urllib2.urlopen(urllib2.Request(info_url))            
            data = json.load(internet)
        except urllib2.HTTPError, e:
            print 'HTTP Error:', e.code, info_url
        except urllib2.URLError, e:
            print 'URL Error:', e.reason, info_url
        return data[u'Location'][u'panoId']

        

    def __str__(self):
        return '%f,%f'%(self.coordinates[0], self.coordinates[1])
    def __unicode__(self):
        return '%f,%f'%(self.coordinates[0], self.coordinates[1])

    


def load_coordinates(filename):
    # get Coordinate objects from file
    coord_list = []
    with open(filename) as f:
        for line in f:
            numbers = line.split(',')
            coord_list.append(Coordinate([numbers[0], numbers[1]]))
    return coord_list



class Directions(object):
    def __init__(self, coordinates):
        self.origin = coordinates[0]
        self.destination = coordinates[1]

        self.base_url = 'https://maps.googleapis.com/maps/api/directions/json?'

    def url(self):
        return self.base_url + 'origin=%s&destination=%s'%(self.origin, self.destination)


    def download(self, directory):
        url = self.url()
        print 'url' + url
        if not os.path.exists('%s/directions'%(directory)):
            try:
                internet = urllib2.urlopen(urllib2.Request(url))
                with open('%s/directions'%(directory), 'w') as computerfile:
                    computerfile.write(internet.read())
            except urllib2.HTTPError, e:
                print 'HTTP Error:', e.code, url
            except urllib2.URLError, e:
                print 'URL Error:', e.reason, url




def download_image(i, point, directory):
    # point is Coordinate object
    # skip if file exists
    if not os.path.exists('%s/%d.jpg'%(directory,i)):
        try:
            internet = urllib2.urlopen(urllib2.Request(point.url()))  # url2
            with open('%s/%d.jpg'%(directory,i), 'w') as computerfile:
                computerfile.write(internet.read())
            return True
        except urllib2.HTTPError, e:
            print 'HTTP Error:', e.code, point.url()
            return False
        except urllib2.URLError, e:
            print 'URL Error:', e.reason, point.url()
            return False
    else:
        print 'skipping'
        return False




class LocalMap(object):
        ''' represents a flat map at given latitude
            used for computing distances and headings
        '''

        def __init__(self, start):
            # start: a point. only latitude is used
            circ = 6371. # * 2 * pi # km
            lat1 = radians(start[0])
            self.slat = circ / 360.
            self.slon = cos(lat1) * self.slat

        def distance(self, point1, point2):
            return sqrt( pow((point1[0]-point2[0])*self.slat, 2) + pow((point1[1]-point2[1])*self.slon, 2) )

        def bearing(self, point1, point2):
            rad = -1* atan2(-1*(point2[1]-point1[1])*self.slon, (point2[0]-point1[0])*self.slat)
            return degrees(rad) % 360.

        def go(self, point, bear, dist):
            lat = point[0] + cos(radians(bear)) * dist / self.slat 
            lon = point[1] + sin(radians(bear)) * dist / self.slon 
            return lat, lon



if __name__ == '__main__':

    # distance between two images on the path; approximate
    min_dist = .002  # km

    lookat = None

    coordinate_file = sys.argv[1]
    directory = coordinate_file.split('.')[0]
    if directory == coordinate_file:
        directory += '-data'

    if not os.path.exists(directory):
        os.makedirs(directory)

    coords = load_coordinates(coordinate_file)

    if len(coords) == 3:
        lookat = coords[2].coordinates

    directions = Directions(coords)

    directions.download(directory)

    with open(os.path.join(directory, 'directions')) as f:
        data = json.load(f)

    leg = data[u'routes'][0][u'legs'][0]
    distance = leg[u'distance'][u'value']
    overview = data[u'routes'][0][u'overview_polyline'][u'points']
    points = []
    for s in leg[u'steps']:
        path = s[u'polyline'][u'points']
        for p in gpoly.decode(path)[:-1]:    # last waypoint also appears in next step:
            points.append(p)
    points.append(gpoly.decode(leg[u'steps'][-1][u'polyline'][u'points'])[-1])

    x, y = zip(*points)
    plt.scatter(y, x, color='r')

    

    # calculate equidistant points
    new_points = [points[0]]

    print 'first point ', points[0]
    d = LocalMap(points[0])
    if lookat:
        heading = lookat
    else:
        heading = points[1]
    headings = [d.bearing(points[0], heading)]
    i = 0
    while len(new_points)<10000:
        start = new_points[-1]
        #print 'starting from point ', len(new_points), start
        #print 'to point ', i+1, points[i+1]
        # check if first step is long 
        step_length = d.distance(start, points[i+1])
        #print 'first distance', step_length
        if step_length > min_dist:
            b = d.bearing(start, points[i+1])
            #print 'bearing %f'%b
            new_point = d.go(start, b, min_dist)
            #print 'new (first distance)', new_point
            new_points.append(new_point)
            if lookat:
                headings.append(d.bearing(new_point, lookat))
            else:
                headings.append(b)
        # else accumulate points
        else:
            
            for j in range(i+1, len(points)-1):
                #print 'checking point ', j+1, points[j+1]
                dist = d.distance(points[j], points[j+1])
                step_length = step_length + dist
                #print 'distance ', step_length
                if step_length > min_dist:
                    #print 'make new checkpoint '
                    b = d.bearing(points[j], points[j+1])
                    #print 'bearing %f'%b
                    new_point = d.go(points[j], b, min_dist - step_length + dist)
                    #print 'new', new_point
                    new_points.append(new_point)
                    if lookat:
                        headings.append(d.bearing(new_point, lookat))
                    else:
                        headings.append(b)
                    i = j
                    start = new_point
                    break
            else:
                break


    x, y = zip(*new_points)
    plt.scatter(y, x, color='b')
    plt.show()

    # smooth headings
    smooth_headings = scipy.ndimage.filters.gaussian_filter1d(headings, sigma=3)

    # log points and headings in file
    with open('log.txt', 'w') as f:
        for i, point in enumerate(new_points):
            f.write('%f, %f\t%f\t%f\n'%(point[0], point[1], headings[i], smooth_headings[i]))


    for i, point in enumerate(new_points):
        print 'downloading %d / %d: %f , %f'%(i, len(new_points), point[0], point[1])
        stat = download_image(i, Coordinate(point, smooth_headings[i]), directory)
        # if stat:
        #     time.sleep(.5)
    



