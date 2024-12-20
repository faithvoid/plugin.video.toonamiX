# -*- coding: utf-8 -*-
# Module: default
# Author: Toon E. J. - Modified to work with XBMC4Xbox by faithvoid
# Created on: 02.27.2017

import sys
from urllib import urlencode
from urlparse import parse_qsl
import xbmcgui
import xbmcplugin
import requests

# Get the plugin url in plugin:// notation.
_url = sys.argv[0]
# Get the plugin handle as an integer number.
_handle = int(sys.argv[1])

# from some web-site or online service.
response = requests.get(url="http://toonamiaftermath.com/tatv.json")
VIDEOS = response.json() if response.status_code == 200 else {}

def get_url(**kwargs):
    """
    Create a URL for calling the plugin recursively from the given set of keyword arguments.

    :param kwargs: "argument=value" pairs
    :type kwargs: dict
    :return: plugin call URL
    :rtype: str
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_videos(category):
    """
    Get the list of videofiles/streams.

    Here you can insert some parsing code that retrieves
    the list of video streams in the given category from some site or server.

    .. note:: Consider using `generators functions <https://wiki.python.org/moin/Generators>`_
        instead of returning lists.

    :param category: Category name
    :type category: str
    :return: the list of videos in the category
    :rtype: list
    """
    return VIDEOS.get(category, [])

def list_videos(category):
    videos = get_videos(category)
    for video in videos:
        list_item = xbmcgui.ListItem(label=video['title'])
        list_item.setInfo('video', {'title': video['title']})
        list_item.setThumbnailImage(video['appImageURL'])
        list_item.setProperty('IsPlayable', 'true')
        url = get_url(action='play', video=video['id'])
        is_folder = False
        xbmcplugin.addDirectoryItem(_handle, url, list_item, is_folder)
    # Add a sort method for the virtual folder items (alphabetically, ignore articles)
    xbmcplugin.addSortMethod(_handle, xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
    xbmcplugin.endOfDirectory(_handle)

def play_video(id):
    response = requests.get(url="http://api.toonamiaftermath.com:3000/streamUrl", params={'channelName': id})
    path = response.text if response.status_code == 200 else ''
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params:
        if params['action'] == 'listing':
            list_videos(params['category'])
        elif params['action'] == 'play':
            play_video(params['video'])
        else:
            raise ValueError('Invalid paramstring: {0}!'.format(paramstring))
    else:
        list_videos("channels")

if __name__ == '__main__':
    router(sys.argv[2][1:])
