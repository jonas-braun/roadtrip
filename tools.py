#!/usr/bin/env python2.7


import os
import sys
import glob

import matplotlib.pyplot as plt

import roadtrip2


def check_route(folder):
    jpegs = glob.glob(folder+'*.jpg')
    data = []
    for i, filename in enumerate(jpegs):
        pano_id = os.path.basename(filename).split('.')[0]
        print 'loading info %d / %d'%(i+1, len(jpegs))
        info = roadtrip2.download_info(lat=None, lon=None, pano_id=pano_id)
        data.append([float(info.lat), float(info.lon)])

    x, y = zip(*data)
    plt.scatter(y, x, color='b')
    plt.show()


def check_size(filename):
    # estimate the number of images for a coordinate file (start, end)
    # no knowledge of route shape, so estimate is based on straight line

    test_size = 10    # number of points to check for estimation

    coords = roadtrip2.load_coordinates(filename)

    # load info for start point
    start_info = roadtrip2.download_info(coords[0][0], coords[0][1])

    # find out which way endpoint is
    local_map = roadtrip2.LocalMap(coords[0])
    end_info = roadtrip2.download_info(coords[1][0], coords[1][1])
    heading = local_map.bearing(coords[0], coords[1])
    next_id = min(start_info.links, key=lambda x: abs(x[0]-heading))

    for i in range(test_size):
        info = roadtrip2.download_info(None, None, next_id[1])
        print info.lat, info.lon
        old_heading = next_id[0]
        next_id = min(info.links, key=lambda x: abs(x[0]-old_heading))

    test_info = roadtrip2.download_info(None, None, next_id[1])

    dist1 = local_map.distance([start_info.lat, start_info.lon],\
                [test_info.lat, test_info.lon])
    dist2 = local_map.distance(coords[0], coords[1])
    print 'start', coords[0]
    print 'end', coords[1]
    print dist1, dist2
    print 'estimated number of images: ', int(dist2/dist1*(test_size+1))

if __name__ == '__main__':


    path = sys.argv[1]
    if os.path.isdir(path):
        check_route(path)
    elif os.path.exists(path):
        check_size(path)
