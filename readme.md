roadtrip - download images from google street view and make a timelapse movie
=============================================================================

inspired by http://hyperlapse.tllabs.io/

Note: Using this software might be against googles terms of service, since both the directions and the street view apis are intended for showing maps in web apps only. The street view images are copyrighted by google.


Requirements
------------
* matplotlib.pyplot for route overview
* scipy.ndimage for smoothing of route


Usage
-----

Place two (latitude, longitude) pairs in a file for beginning and end location of route. (Optional) Put a third coordinate if you want the camera to look at that point instead of straight ahead. See `san-fancisco` example.

`./roadtrip.py coordinate-file`

After downloading the images you can use mencoder to make the movie.

`./movie.sh image-folder`

For higher quota, get an API key from google and save it in `api.key`. The API is documented on https://developers.google.com/maps/documentation/streetview/
