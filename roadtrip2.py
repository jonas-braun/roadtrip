#!/usr/bin/env python2.7




import os
import sys
import json
import urllib2
from math import sin, cos, radians, degrees, atan2, sqrt


import load_image


def load_coordinates(filename):
    # get Coordinate objects from file
    coord_list = []
    with open(filename) as f:
        for line in f:
            numbers = line.split(',')
            coord_list.append([float(numbers[0]), float(numbers[1])])
    return coord_list



    # load info for point
def download_info(lat, lon, pano_id=None, folder=None):
        base_url = 'https://cbk0.google.com/cbk?output=json'
        if lat:
            info_url = base_url + '&ll=%f,%f'%(lat, lon)
        elif pano_id:
            info_url = base_url + '&panoid=%s'%(pano_id)
            
        # check if exists on file
        if not folder \
           or not os.path.exists(os.path.join(folder, pano_id, pano_id+'.json')):
            try:
                internet = \
                   urllib2.urlopen(urllib2.Request(info_url))            
                data = json.load(internet)

                if folder and os.path.exists(os.path.join(folder, pano_id)):
                    with open(os.path.join(folder, pano_id, pano_id+'.json'), 'w') as f:
                        json.dump(data, f)

            except urllib2.HTTPError, e:
                print 'HTTP Error:', e.code, info_url
            except urllib2.URLError, e:
                print 'URL Error:', e.reason, info_url
             
        else:
            with open(os.path.join(folder,\
                              pano_id, pano_id+'.json')) as f:
                data = json.load(f)

        links = [ [float(l[u'yawDeg']),\
                     str(l[u'panoId'])] for l in data[u'Links'] ]
        return Info(data[u'Location'][u'panoId'], links,\
                     data[u'Location'][u'lat'],\
                     data[u'Location'][u'lng'],\
                     data[u'Projection'][u'pano_yaw_deg'],\
                     data[u'Projection'][u'tilt_yaw_deg'],\
                     data[u'Projection'][u'tilt_pitch_deg'])





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
            dlat = point[0] + cos(radians(bear)) * dist / self.slat 
            dlon = point[1] + sin(radians(bear)) * dist / self.slon 
            return dlat, dlon


class Info(object):
    def __init__(self, pano_id, links, lat, lon,\
                                yaw, tilt_yaw, tilt_pitch):
        self.pano_id = str(pano_id)
        self.links = links
        self.lat = float(lat)
        self.lon = float(lon)
        self.yaw = float(yaw)
        self.tilt_yaw = float(tilt_yaw)
        self.tilt_pitch = float(tilt_pitch)



if __name__ == '__main__':


    image_size = 1024
    target_tolerance = 0.01    # distance from target in km

    coordinate_file = sys.argv[1]
    directory = coordinate_file.split('.')[0]
    if directory == coordinate_file:
        directory += '-data'

    if not os.path.exists(directory):
        os.makedirs(directory)

    coords = load_coordinates(coordinate_file)

    if len(coords) == 3:
        lookat = coords[2]


    # load info for start point
    start_info = download_info(coords[0][0], coords[0][1], directory)

    # find out which way endpoint is
    local_map = LocalMap(coords[0])
    end_info = download_info(coords[1][0], coords[1][1], directory)
    heading = local_map.bearing(coords[0], coords[1])
    next_id = min(start_info.links, key=lambda x: abs(x[0]-heading))
    info = download_info(None, None, next_id[1], directory)

    # download first image
    
    camera1 = load_image.Camera(start_info.yaw, 0., 360., 2., 13312)
    camera2 = load_image.Camera(next_id[0], 0., 90., 1., image_size)

    tile_set = load_image.view(camera1, camera2)
    
    load_image.load(directory, start_info.pano_id, tile_set, image_size, image_size)

    ids = [start_info.pano_id] # unused
    framelist_file = os.path.join(directory, 'framelist.txt')
    if os.path.exists(framelist_file):
        os.remove(framelist_file)
    with open(framelist_file, 'a') as f:
        f.write(start_info.pano_id + '\n')

    for i in range(9999):
        print next_id
        old_heading = next_id[0]
        next_id = min(info.links,\
                  key=lambda x: min(abs(x[0]-old_heading),\
                                    abs(x[0]+360-old_heading)))
        info = download_info(None, None, next_id[1], directory)

        camera1 = load_image.Camera(info.yaw, 0., 360., 2., 13312)
        camera2 = load_image.Camera(info.yaw, 0., 90., 1., image_size)

        tile_set = load_image.view(camera1, camera2)
    
        load_image.load(directory, info.pano_id, tile_set,\
                            image_size, image_size)

        ids.append(info.pano_id)
        with open(framelist_file, 'a') as f:
            f.write(info.pano_id + '\n')

        if local_map.distance([info.lat, info.lon],\
                    [end_info.lat, end_info.lon]) < target_tolerance:
            print local_map.distance([info.lat, info.lon],\
                    [end_info.lat, end_info.lon])
            break




