#!/usr/bin/env python

import argparse
import os
import time
from pprint import pprint

import googleapiclient.discovery
from oauth2client.client import GoogleCredentials
from six.moves import input

credentials = GoogleCredentials.get_application_default()
service = googleapiclient.discovery.build('compute', 'v1', credentials=credentials)

#
# In the google cloud console, the environment variable GOOGLE_CLOUD_PROJECT
# is automatically set
#
project = os.getenv('GOOGLE_CLOUD_PROJECT') or 'YOUR-PROJECT-NAME-HERE'  # TODO: Update placeholder value.
