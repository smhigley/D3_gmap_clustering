import urllib2
import json
import math

# get data from flickr
# build flickr url
flickr_api_key = '5f6652a08b32dd50ae264fb3f47a9632'
flickr_api_secret = '6826da1b61cf3f39'
tags = 'cat'
url = 'http://api.flickr.com/services/rest/?method=flickr.photos.search&api_key=' + flickr_api_key + '&tags=' + tags + '&woe_id=2347602&has_geo=1&extras=geo&format=json&nojsoncallback=1&per_page=800';

# get data from url
json_data = urllib2.urlopen(url)
data = json.load(json_data)
data = data['photos']['photo']

# map settings
max_zoom = 12
min_zoom = 4

# clustering settings
clusters = {} # empty dictionary to add to later
max_distance_base = 200.0 # max distance in km for zoom 4

# clustering function, takes array of data and int zoom
# returns clusters in array of [{latitude: latitude, longitude: longitude, size: # of points, points: [array of points' indices]}, ... ]
def cluster(data, zoom):
  # find max distance in km for this zoom level
  # google maps scales up by 2 for each zoom level
  max_distance = max_distance_base / ( 2 ** (zoom - min_zoom) )
  print "zoom is " + str(zoom) + " and max distance is " + str(max_distance)

  # empty cluster set for this zoom level
  cluster_set = []

  # Add clusters by incrementing through data
  for point in data:
    x = point['longitude']
    y = point['latitude']
    clustered = False

    #now increment through cluster set and check distance
    for cluster in cluster_set:
      dist = distance([y, x], [cluster['latitude'], cluster['longitude']])

      if dist <= max_distance:
        # if close enough, add point to cluster, update cluster x and y, set clustered to true
        cluster['points'].append(point['id'])
        cluster['longitude'] = average(x, cluster['longitude'], cluster['size'])
        cluster['latitude'] = average(y, cluster['latitude'], cluster['size'])
        cluster['size'] += 1
        clustered = True
        break

    #if it is not close enough to join an existing cluster, create a new one
    if clustered == False:
      new_cluster = {'longitude': x, 'latitude': y, 'size': 1, 'points': [point['id']], 'zoom': zoom }
      cluster_set.append(new_cluster)

  return cluster_set

# return distance in km between two points in format [lat, long]
def distance(origin, destination):
    lat1, lon1 = origin
    lat2, lon2 = destination
    radius = 6371 # km radius of earth

    dlat = math.radians(lat2-lat1)
    dlon = math.radians(lon2-lon1)
    a = math.sin(dlat/2) * math.sin(dlat/2) + math.cos(math.radians(lat1)) \
        * math.cos(math.radians(lat2)) * math.sin(dlon/2) * math.sin(dlon/2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    d = radius * c

    return d

# average of two points, weighted by size
def average(n1, n2, size):
  #n2 is always a cluster with [size] points, n1 size is always 1
  return (n1 + size*n2)/(size + 1)

def mode(list):
  modes = {}
  for item in list:
    modes[item] = list.count(item)

  mode = max(modes, key=modes.get)
  return mode

#return index of parent cluster
def parent_cluster(zoom, d):
  points = d['points']
  parent_zoom_data = clusters[zoom-1]
  parents = []

  for point in points:
    # find which cluster of the parent zoom level the point is in
    for c in parent_zoom_data:
      if point in c['points']:
        parents.append(parent_zoom_data.index(c))
        break

  parent_cluster_index = mode(parents)
  d['parent'] = parent_cluster_index

# build cluster data
for zoom in range(min_zoom, max_zoom + 1):
  clusters[zoom] = cluster(data, zoom)

  #add index of parent cluster to each cluster in the zoom level, if we're not at the min zoom
  if(zoom != min_zoom):
    for c in clusters[zoom]:
      parent_cluster(zoom, c)

# now write data to a file
with open('clusters.json', 'w') as outfile:
  json.dump(clusters, outfile)

with open('data.json', 'w') as outfile:
  json.dump(data, outfile)
