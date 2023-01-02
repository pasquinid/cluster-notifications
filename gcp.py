import googleapiclient.discovery
from oauth2client.client import GoogleCredentials
from datetime import datetime
from google.cloud import storage
import json
import time
import os

class GCP:
    def __init__(self):
        self.projects = []
        self.compute     = googleapiclient.discovery.build('compute', 'v1')
        self.resourcemng = googleapiclient.discovery.build('cloudresourcemanager', 'v1')
        self.gke         = googleapiclient.discovery.build('container', 'v1')


    def filterProjectIds(self,response,currentIds):
        for project in response['projects']:
            if not project['projectId'].startswith('sys-'):
                currentIds.append(project['projectId'])
        return currentIds

    def setProjectList(self):
        print("Searching for the current project list...")
        requestList = self.resourcemng.projects().list()
        print("...wait for it...")
        response = requestList.execute()
        print("...wait more for it...")
        #print(response)
        self.projects = []
        
        while 'nextPageToken' in  response:
            self.projects = self.filterProjectIds(response,self.projects)
            response = self.resourcemng.projects().list(pageToken=response['nextPageToken']).execute()
            print("...wait a bit more for it...")
        
        self.projects = self.filterProjectIds(response,self.projects)
        print ("and finally done!")


    def listClusters(self,project):
        clustersNames=[]
        print(f"Searching for gke clusters in current project {project}...")
        try:
            clusters = self.gke.projects().zones().clusters().list(projectId=project,zone='',parent=f'projects/{project}/locations/-').execute()
            #  https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/ListNodePoolsResponse   https://cloud.google.com/kubernetes-engine/docs/reference/rest/v1/projects.zones.clusters.nodePools/list
        except:
            print(f"Erro tentando achar cluster no projeto {project}.")
            return []
        if len(clusters) > 0:
            for cluster in clusters['clusters']:
                clustersNames.append(cluster['name'])
            print(f"..found clusters : {clustersNames}")
            return clustersNames
        else:
            return []