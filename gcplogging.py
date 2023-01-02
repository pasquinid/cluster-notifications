from datetime import datetime, timedelta
from datetime import date
from platform import node
from textwrap import indent
from pytz import timezone
import requests
import google.auth
import json
from google.oauth2 import service_account
import jwt
import time


### https://cloud.google.com/kubernetes-engine/docs/how-to/cluster-autoscaler-visibility#noscaledown-top-level-reasons



class Logging: 
    def getJWTcredentials(self,SERVICE_ACCOUNT):
        
        svcacc = json.loads(open(SERVICE_ACCOUNT,'r').read())

        iat = time.time()
        exp = iat + 36
        payload = {'iss': svcacc['client_email'],
                'scope': 'https://www.googleapis.com/auth/logging.read',
                'aud': 'https://oauth2.googleapis.com/token',
                'iat': iat,
                'exp': exp}
        additional_headers = {'kid': svcacc['private_key_id']}
        signed_jwt = jwt.encode(payload, svcacc['private_key'], headers=additional_headers,
                            algorithm='RS256')   

        BODY={
            'assertion': signed_jwt,
            'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer'
        }

        HEADERS={
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        response = json.loads(requests.post('https://oauth2.googleapis.com/token',headers=HEADERS,data=BODY).content.decode('UTF-8'))
        
        return response['access_token']                      

    def __init__(self,servcacc):
        SERVICE_ACCOUNT=servcacc

        self.tz = timezone('America/Sao_Paulo')
        self.current_time = datetime.now(self.tz)
        self.previous_hour = (self.current_time.replace(minute=0, second=0, microsecond=0) - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.current_hour = (self.current_time.replace(minute=0, second=0, microsecond=0)).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.TOKEN=self.getJWTcredentials(SERVICE_ACCOUNT)
        self.API_URL='https://logging.googleapis.com/v2/entries:list'

    def getAutoscalerNoScaleDownErrors(self,project,clusterName):
        
        FILTER = fr'''
        resource.type="k8s_cluster"
        resource.labels.cluster_name="{clusterName}"
        logName="projects/{project}/logs/container.googleapis.com%2Fcluster-autoscaler-visibility"
        (jsonPayload.noDecisionStatus.noScaleDown.reason.messageId=~"no.scale.down" OR jsonPayload.noDecisionStatus.noScaleDown.nodes.reason.messageId=~"no.scale.down")
        timestamp >= "{self.previous_hour}" 
        timestamp <= "{self.current_hour}" 
        '''

        BODY={
            "projectIds": [
                project
            ],
            "resourceNames": [
                f"projects/{project}"
            ],
            "orderBy": "timestamp desc",
            "filter": FILTER,
            "pageSize": 10
        }

        HEADERS={
            'Authorization': f"Bearer {self.TOKEN}",
            'Content-Type': 'application/json'
        }

        apps = []

        response=json.loads(requests.post(self.API_URL,headers=HEADERS,json=BODY).content.decode('utf-8'))
        if not 'entries' in response: 
            return False

        for entry in response['entries']: 
            # noDecisionStatus.noScaleDown.nodes[].reason
            if 'nodes' in entry['jsonPayload']['noDecisionStatus']['noScaleDown']:
                print(f"Log entry found in category: noDecisionStatus.noScaleDown.nodes[].reason")
                try:
                    for nodeEntry in entry['jsonPayload']['noDecisionStatus']['noScaleDown']['nodes']:
                        if 'parameters' in nodeEntry['reason']:
                            for parameter in nodeEntry['reason']['parameters']:
                                apps.append({'appName': parameter, 'reason': nodeEntry['reason']['messageId'],'cluster': clusterName,'project':project})
                        elif 'messageId' in nodeEntry['reason']:
                            apps.append({'appName': 'null', 'reason': nodeEntry['reason']['messageId'],'cluster': clusterName,'project':project})
                except:
                    print(f"Error: Erro ao interprestar o erro do tipo \"noDecisionStatus.noScaleDown.nodes[].reason\"\n{entry}")
                    apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleDown.nodes[].reason"','cluster': clusterName,'project':project})
            
            elif 'reason' in entry['jsonPayload']['noDecisionStatus']['noScaleDown']:
                # noDecisionStatus.noScaleDown.reason
                print(f"Log entry found in category: noDecisionStatus.noScaleDown.reason")
                try:
                    if 'parameters' in entry['jsonPayload']['noDecisionStatus']['noScaleDown']['reason']:
                        for parameter in entry['jsonPayload']['noDecisionStatus']['noScaleDown']['reason']['parameters']:
                            apps.append({'appName': parameter, 'reason': parameter['reason']['messageId'],'cluster': clusterName,'project':project})                
                    elif 'messageId' in entry['jsonPayload']['noDecisionStatus']['noScaleDown']['reason']:
                        apps.append({'appName': 'null', 'reason': entry['jsonPayload']['noDecisionStatus']['noScaleDown']['reason']['messageId'],'cluster': clusterName,'project':project})
                except:
                    print(f"Error: Erro ao interprestar o erro do tipo \" noDecisionStatus.noScaleDown.reason\"\n{entry}")
                    apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleDown.reason"','cluster': clusterName,'project':project})
        return apps

    def getAutoscalerNoScaleUpErrors(self,project,clusterName):
        FILTER = fr'''
        resource.type="k8s_cluster"
        resource.labels.cluster_name="{clusterName}"
        logName="projects/{project}/logs/container.googleapis.com%2Fcluster-autoscaler-visibility"
        (jsonPayload.noDecisionStatus.noScaleUp.reason.messageId=~"no.scale.up" OR jsonPayload.noDecisionStatus.noScaleUp.nodes.reason.messageId=~"no.scale.up")
        timestamp >= "{self.previous_hour}" 
        timestamp <= "{self.current_hour}" 
        '''

        BODY={
            "projectIds": [
                project
            ],
            "resourceNames": [
                f"projects/{project}"
            ],
            "orderBy": "timestamp desc",
            "filter": FILTER,
            "pageSize": 10
        }

        HEADERS={
            'Authorization': f"Bearer {self.TOKEN}",
            'Content-Type': 'application/json'
        }

        apps = []

        response=json.loads(requests.post(self.API_URL,headers=HEADERS,json=BODY).content.decode('utf-8'))
        if not 'entries' in response: 
            return False
        for entry in response['entries']: 
            # noDecisionStatus.noScaleUp.reason
            print(f"Log entry found in category: noDecisionStatus.noScaleUp.reason")
            if 'reason' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']:
                try:
                    if 'parameters' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['reason']:
                        for parameter in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['reason']['parameters']:
                            apps.append({'appName': parameter, 'reason': entry['jsonPayload']['noDecisionStatus']['noScaleUp']['reason']['messageId'],'cluster': clusterName,'project':project})                
                    elif 'messageId' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['reason']:
                        apps.append({'appName': 'null', 'reason': entry['jsonPayload']['noDecisionStatus']['noScaleUp']['reason']['messageId'],'cluster': clusterName,'project':project})                
                except:
                    print(f"Error: Erro ao interprestar o erro do tipo \" noDecisionStatus.noScaleUp.reason\"\n{entry}")
                    apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleUp.reason"','cluster': clusterName,'project':project})
                    
            # noDecisionStatus.noScaleUp.napFailureReason
            elif 'napFailureReason' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']:
                print(f"Log entry found in category: noDecisionStatus.noScaleUp.napFailureReason")
                try:
                    if 'parameters' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['napFailureReason']:
                        for parameter in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['napFailureReason']['parameters']:
                            apps.append({'appName': parameter, 'reason': entry['jsonPayload']['noDecisionStatus']['noScaleUp']['napFailureReason']['reason']['messageId'],'cluster': clusterName,'project':project})    
                    elif 'messageId' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['napFailureReason']:
                        apps.append({'appName': 'null', 'reason': entry['jsonPayload']['noDecisionStatus']['noScaleUp']['napFailureReason']['reason']['messageId'],'cluster': clusterName,'project':project})    
                except:
                    print(f"Error: Erro ao interprestar o erro do tipo \" noDecisionStatus.noScaleUp.napFailureReason\"\n{entry}")
                    apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleUp.napFailureReason"','cluster': clusterName,'project':project})
                    
            # noDecisionStatus.noScaleUp.skippedMigs[].reason
            elif 'skippedMigs' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']:
                print(f"Log entry found in category: noDecisionStatus.noScaleUp.skippedMigs[].reason")
                try:
                    for skippedMig in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['skippedMigs']:
                        if 'parameters' in skippedMig['reason']:
                            for parameter in skippedMig['reason']['parameters']:
                                apps.append({'appName': parameter, 'reason': skippedMig['reason']['messageId'],'cluster': clusterName,'project':project})   
                        elif 'messageId' in skippedMig['reason']:
                            apps.append({'appName': parameter, 'reason': skippedMig['reason']['messageId'],'cluster': clusterName,'project':project})   
                except:
                    print(f"Error: Erro ao interprestar o erro do tipo \" noDecisionStatus.noScaleUp.skippedMigs[].reason\"\n{entry}")
                    apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleUp.skippedMigs[].reason"','cluster': clusterName,'project':project})
                                    
            # noDecisionStatus.noScaleUp.unhandledPodGroups[].rejectedMigs[].reason
            elif 'unhandledPodGroups' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']:
                if 'rejectedMigs' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['unhandledPodGroups']:
                    print(f"Log entry found in category: noDecisionStatus.noScaleUp.unhandledPodGroups[].rejectedMigs[].reason")
                    try:
                        for unhandledPodGroup in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['unhandledPodGroups']:
                            for rejectedMig in unhandledPodGroup['rejectedMigs']:
                                if 'parameters' in rejectedMig['reason']:
                                    for parameter in rejectedMig['reason']['parameters']:
                                        apps.append({'appName': parameter, 'reason': rejectedMig['reason']['messageId'],'cluster': clusterName,'project':project})   
                                elif 'messageId' in rejectedMig['reason']:
                                    apps.append({'appName': 'null', 'reason': rejectedMig['reason']['messageId'],'cluster': clusterName,'project':project})   
                    except:
                        print(f"Error: Erro ao interprestar o erro do tipo \"noDecisionStatus.noScaleUp.unhandledPodGroups[].rejectedMigs[].reason\"\n{entry}")
                        apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleUp.unhandledPodGroups[].rejectedMigs[].reason"','cluster': clusterName,'project':project})

            # noDecisionStatus.noScaleUp.unhandledPodGroups[].napFailureReasons[]
            elif 'unhandledPodGroups' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']:
                if 'napFailureReasons' in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['unhandledPodGroups']:
                    print(f"Log entry found in category: noDecisionStatus.noScaleUp.unhandledPodGroups[].napFailureReasons[]")
                    try:
                        for unhandledPodGroup in entry['jsonPayload']['noDecisionStatus']['noScaleUp']['unhandledPodGroups']:
                            for napFailureReason in unhandledPodGroup['napFailureReasons']:
                                if 'parameters' in napFailureReason['reason']:
                                    for parameter in napFailureReason['reason']['parameters']:
                                        apps.append({'appName': parameter, 'reason': unhandledPodGroup['napFailureReasons']['reason']['messageId'],'cluster': clusterName,'project':project}) 
                                elif 'messageId' in napFailureReason['reason']:
                                    apps.append({'appName': 'null', 'reason': unhandledPodGroup['napFailureReasons']['reason']['messageId'],'cluster': clusterName,'project':project})
                    except:
                        print(f"Error: Erro ao interprestar o erro do tipo \"noDecisionStatus.noScaleUp.unhandledPodGroups[].napFailureReasons[]\"\n{entry}")
                        apps.append({'appName': 'Erro', 'reason':  'Erro ao interprestar o erro do tipo "noDecisionStatus.noScaleUp.unhandledPodGroups[].napFailureReasons[]"','cluster': clusterName,'project':project})

        return apps