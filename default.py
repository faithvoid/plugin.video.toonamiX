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
import os
import json
from difflib import get_close_matches
from datetime import datetime, timedelta

# Get the plugin URL and handle
_url = sys.argv[0]
_handle = int(sys.argv[1])

# Load local channel data
try:
    local_file_path = os.path.join(os.getcwd(), "tatv.json")
    with open(local_file_path, "r") as file:
        CHANNELS = json.load(file)
except IOError as e:
    xbmc.log("Error loading tatv.json: {0}".format(e), xbmc.LOGERROR)
    CHANNELS = {}

# Load current media data from the API
current_media_response = requests.get(url="http://api.toonamiaftermath.com:3000/channelsCurrentMedia")
CURRENT_MEDIA = current_media_response.json() if current_media_response.status_code == 200 else {}

def get_url(**kwargs):
    """
    Create a plugin call URL.
    """
    return '{0}?{1}'.format(_url, urlencode(kwargs))

def get_videos(category):
    """
    Get the list of videos for a given category.
    """
    return CHANNELS.get(category, [])

def fuzzy_find_schedule(channel_name):
    """
    Find the closest match for the given channel name and get its schedule.
    """
    def normalize_name(name):
        """
        Normalize the channel name by making 'Pacific' and 'West' interchangeable.
        """
        return name.replace("Pacific", "PST").replace("West", "PST")

    # Normalize the input channel name
    normalized_input = normalize_name(channel_name)

    # Normalize the names in the channel list
    channel_names = [normalize_name(channel['name']) for channel in CURRENT_MEDIA]

    # Find the closest match
    match = get_close_matches(normalized_input, channel_names, n=1, cutoff=0.6)
    if not match:
        return None

    # Find the corresponding channel media schedule
    for channel in CURRENT_MEDIA:
        if normalize_name(channel['name']) == match[0]:
            # Check if 'media' key exists in the channel data
            if 'media' in channel:
                return channel['media']
            else:
                xbmc.log("No 'media' key found in channel: {}".format(channel['name']), xbmc.LOGERROR)
                return None
    return None

def show_schedule_dialog(schedule):
    """
    Display a schedule in a dialog box with times converted to the local timezone.
    """
    if not schedule:
        xbmcgui.Dialog().ok("Schedule", "No schedule found.")
        return

    # Define the timezone offset for your local timezone (e.g., UTC -8 for Pacific Time)
    # Adjust the offset according to your needs (e.g., -8 hours for Pacific Time)
    timezone_offset = timedelta(hours=-5)  # Adjust this based on your local timezone

    # Prepare the schedule items for display
    lines = []
    for item in schedule:
        # Update the datetime format to handle milliseconds and 'Z' at the end of the timestamp
        utc_time = datetime.strptime(item["startDate"], "%Y-%m-%dT%H:%M:%S.%fZ")  # Parse the UTC time with milliseconds
        local_time = utc_time + timezone_offset  # Apply timezone offset
        formatted_time = local_time.strftime("%I:%M %p")  # Format as 12-hour with AM/PM
        lines.append("{time} - {name}".format(time=formatted_time, name=item["name"]))

    # Display up to 3 lines in the dialog box
    xbmcgui.Dialog().ok(
        "Schedule",
        lines[0] if len(lines) > 0 else "",
        lines[1] if len(lines) > 1 else "",
        lines[2] if len(lines) > 2 else ""
    )


def list_videos(category):
    """
    List all videos for a given category.
    """
    videos = get_videos(category)
    for video in videos:
        channel_name = video['title']
        
        # Get the current show title from the schedule
        schedule = fuzzy_find_schedule(channel_name)  # Get the schedule for the channel
        if schedule and isinstance(schedule, list) and len(schedule) > 0:
            # Append the first scheduled show's title to the channel name
            channel_name += " - " + schedule[0]["name"]  # Access the "name" of the first show in the schedule
        
        # Create a list item
        list_item = xbmcgui.ListItem(label=channel_name)
        list_item.setInfo('video', {'title': channel_name})
        list_item.setThumbnailImage(video.get('appImageURL', ''))
        list_item.setProperty('IsPlayable', 'true')
        
        # Add context menu for schedule
        context_menu = [
            ("View Schedule", "XBMC.RunPlugin({})".format(get_url(action='show_schedule', channel=channel_name)))
        ]
        list_item.addContextMenuItems(context_menu, replaceItems=True)
        
        # Add the item to the directory
        url = get_url(action='play', video=video.get('id', ''))
        xbmcplugin.addDirectoryItem(_handle, url, list_item, False)

    xbmcplugin.endOfDirectory(_handle)

def play_video(id):
    response = requests.get(url="http://api.toonamiaftermath.com:3000/streamUrl", params={'channelName': id})
    path = response.text if response.status_code == 200 else ''
    play_item = xbmcgui.ListItem(path=path)
    xbmcplugin.setResolvedUrl(_handle, True, listitem=play_item)

def router(paramstring):
    """
    Router function to handle plugin actions.
    """
    params = dict(parse_qsl(paramstring))
    if params:
        action = params.get('action')
        if action == 'list_videos':
            list_videos(params['category'])
        elif action == 'play':
            play_video(params['video'])
        elif action == 'show_schedule':
            channel_name = params['channel']
            schedule = fuzzy_find_schedule(channel_name)
            show_schedule_dialog(schedule)
    else:
        list_videos("channels")

if __name__ == '__main__':
    router(sys.argv[2][1:])
