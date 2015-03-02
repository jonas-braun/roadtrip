#!/usr/bin/env python2.7



import os
import sys
import math
import urllib2


import Image


class Camera(object):
    def __init__(self, yaw, pitch, fov, apr, pix, roll=None):
        # fov - horizontal field of view in degrees
        # apr - aspect ratio
        # pix - number of horizontal pixels
        self.yaw = yaw
        self.pitch = pitch  # positive pitch is downwards from equator
        self.fov = fov
        self.apr = apr
        self.pix = pix

    def res(self):
        return self.pix / self.fov


# download all pictures for a frame
def view(camera, target_camera):

    # assume 13312x6656px images with 512px^2 tiles
    tile_size = 512
    zoom_levels = 5
    max_tiles = 26    # strangely
    max_pix = 13312

    ###### make list of needed tiles

    # transformations
    center = target_camera.yaw - camera.yaw
    pitch = target_camera.pitch - camera.pitch

    ratio = target_camera.res() / camera.res()
    if ratio > 1.:
        print 'Resolution not available'
    vzoom = - math.log(ratio, 2)
    #print ratio,vzoom

    vtiles = 26 / 2** math.floor(vzoom)
    #print 'vtiles', vtiles

    zoom = zoom_levels - int(vzoom)
    #zoom = max(zoom, 4)   # only allow zoom levels 4 and 5
                          # because they don't have clipping at 0 deg
    #print zoom

    # top left corner of new image
    left = center - .5 * target_camera.fov    # correct sign +- ?
    top = pitch - .5 * target_camera.fov / target_camera.apr
    right = center + .5 * target_camera.fov    # correct sign +- ?
    bottom = pitch + .5 * target_camera.fov / target_camera.apr
    print center, pitch, vtiles, "center, pitch, vtiles"
    print left, top, vtiles, "left, top, vtiles"
    print right, bottom, vtiles, "right, bottom, vtiles"
    print position(center, pitch, vtiles), "position(center, pitch)"
    print position(left, top, vtiles), "position(left, top)"
    print position(right, bottom, vtiles), "position(right, bottom)"

    lt = position(left, top, vtiles)
    rb = position(right, bottom, vtiles)

    if lt[0] > rb[0]:     # pano overlaps 0 deg line
        X = range(lt[0], int(vtiles)) + range(0, rb[0]+1)
        print rb[0], lt[0], X
    else:
        X = range(lt[0], rb[0]+1)
    if lt[1] > rb[1]:     # pano overlaps 0 deg line
        Y = range(lt[1], int(vtiles/2)) + range(0, rb[1]+1)
    else:
        Y = range(lt[1], rb[1]+1)

    return X, Y, [lt[2], rb[2]], [lt[3], rb[3]], zoom


def position(yaw, pitch, vtiles):
    # give pixel and tile position of yaw and pitch view

    tile_size = 512

    x = vtiles * tile_size / 360. * ((yaw+180) % 360.)
    x_tile = int(x / tile_size)
    x_pix = int(x % tile_size)
    y = vtiles * tile_size / 360. * ( (pitch + 90.) % 180.) # 360
    y_tile = int(y / tile_size)
    y_pix = int(y % tile_size)
    return x_tile, y_tile, x_pix, y_pix


def download_image(folder, pano_id, zoom, X, Y):
    print pano_id, X, Y

    path = os.path.join(folder, pano_id)

    if not os.path.exists(path):
        #print 'make dir'
        os.mkdir(path)

    for x in X:
        for y in Y:
            download_tile(folder, pano_id, zoom, x, y)


def download_tile(folder, pano_id, zoom, x, y):
    #print 'download', x, y
    base_url = 'https://cbk0.google.com/cbk?output=tile'
    url = base_url + '&panoid=%s'%(pano_id)
    url = url + '&zoom=%d'%(zoom)
    url = url + '&x=%d'%(x)
    url = url + '&y=%d'%(y)

    path = os.path.join(folder, pano_id, '%d_%d.jpg'%(x,y))

    if not os.path.exists(path):
        try:
            internet = urllib2.urlopen(urllib2.Request(url))
            with open(path, 'w') as computerfile:
                computerfile.write(internet.read())
            return True
        except urllib2.HTTPError, e:
            print 'HTTP Error:', e.code, url
            return False
        except urllib2.URLError, e:
            print 'URL Error:', e.reason, url
            return False
    else:
        #print 'skipping'
        return False


def stitch_image(folder, pano_id, X, Y, x_lim, y_lim, width, height):
    # min and max x and y

    tile_size = 512

    filename = pano_id + '.jpg'
    x_size = len(X) * tile_size
    y_size = len(Y) * tile_size
    image = Image.new('RGB', (x_size,y_size))

    for x, x_tile in enumerate(X):
        for y, y_tile in enumerate(Y):
            #print x, x_tile, y, y_tile
            tilename = os.path.join(folder, pano_id, '%d_%d.jpg'%(x_tile,y_tile))
            tile = Image.open(tilename)
            image.paste(tile, (x*tile_size, y*tile_size))

    box = (x_lim[0], y_lim[0],\
                   x_size - tile_size + x_lim[1],\
                   y_size - tile_size + y_lim[1])
    #print box
    image = image.crop(box)
    image = image.resize((int(width), int(height)))

    image.save(os.path.join(folder, filename))        #, quality=50)

    

def load(folder, pano_id, tile_set, x_dim, y_dim):
    
    download_image(folder, pano_id, tile_set[4], list(set(tile_set[0])), list(set(tile_set[1])))

    stitch_image(folder, pano_id, tile_set[0], tile_set[1], tile_set[2], tile_set[3], x_dim, y_dim)



if __name__ == '__main__':

    image_size = 512

    folder = 'test-roadtrip2'
    camera1 = Camera(212.71, 2., 360., 2., 13312) # yaw 137.
    camera2 = Camera(230., 0., 90., 1., image_size)

    pano_id = 'MbNmn1-aYnFdxNSRV_1ngg' #'mwSJK8cFs3tfisKApVwujw'

    tile_set = view(camera1, camera2)

    if not os.path.exists(folder):
        print 'make dir'
        os.mkdir(folder)

    download_image(folder, pano_id, tile_set[4], list(set(tile_set[0])), list(set(tile_set[1])))

    stitch_image(folder, pano_id, tile_set[0], tile_set[1], tile_set[2], tile_set[3], image_size, image_size/1.)


