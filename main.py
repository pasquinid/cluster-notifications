from gcplogging import Logging
import botslack as botslack
import gcp as gcp
from datetime import datetime
import os

slackCtl = botslack.Slack(os.environ.get('SLACKCHNL'),os.environ.get('SLACKAPPTKN'))
gcpCtl = gcp.GCP()

def proccessNoScaleDown(errors):
    clusters = []
    projects = []
    reasons  = [] 

    for error in errors:
        if not error['cluster'] in clusters:
            clusters.append(error['cluster'])
        if not error['project'] in projects:
            projects.append(error['project'])
        if not error['reason'] in reasons:
            reasons.append(error['reason'])

    bannermsg = f"> :reupi: Estamos com clusters GKE com downscale prejudicados.\n> Clusters: {len(clusters)} \n> Projetos: {len(projects)}\n> Razões: {reasons}"

    slackCtl.sendMessage(bannermsg)

    # Criar arquivo csv
    datestr = datetime.now().strftime("%b-%d-%Y-%H%M%S")
    folder = "/tmp/"
    filename = "downscale-error-log-"+datestr+".csv"
    path = folder+filename
    with open(path,"w") as file:
        file.write("CLUSTER,PROJECT,APPNAME,REASON\n")

        for message in slackCtl.listMessages()['messages']:
            if 'bot_id' in message and message['bot_id'] == 'B0487RURQN7': 
                for error in errors:
                    file.write(f"{error['cluster']},{error['project']},{error['appName']},{error['reason']}\n")
                file.close()
                slackCtl.sendFileInThread(filename,message['ts'],path)
                break
    
def proccessNoScaleUp(errors):
    clusters = []
    projects = []
    reasons  = [] 

    for error in errors:
        if not error['cluster'] in clusters:
            clusters.append(error['cluster'])
        if not error['project'] in projects:
            projects.append(error['project'])
        if not error['reason'] in reasons:
            reasons.append(error['reason'])

    bannermsg = f"> :reupi: Estamos com clusters GKE com upscale prejudicados.\n> Clusters: {len(clusters)} \n> Projetos: {len(projects)}\n> Razões: {reasons}"

    slackCtl.sendMessage(bannermsg)

    # Criar arquivo csv
    datestr = datetime.now().strftime("%b-%d-%Y-%H%M%S")
    folder = "/tmp/"
    filename = "upscale-error-log-"+datestr+".csv"
    path = folder+filename
    with open(path,"w") as file:
        file.write("CLUSTER,PROJECT,APPNAME,REASON\n")

        for message in slackCtl.listMessages()['messages']:
            if 'bot_id' in message and message['bot_id'] == 'B0487RURQN7': 
                for error in errors:
                    file.write(f"{error['cluster']},{error['project']},{error['appName']},{error['reason']}\n")
                file.close()
                slackCtl.sendFileInThread(filename,message['ts'],path)
                break
def main(arg):
    loggingCtl = Logging()

    gcpCtl.setProjectList()
     
    downscale_errors=[]
    upscale_errors=[]

    for project in gcpCtl.projects:
        for cluster in gcpCtl.listClusters(project):
            downscaleerrors = loggingCtl.getAutoscalerNoScaleDownErrors(project,cluster)
            if not downscaleerrors == False :
                for err in downscaleerrors:
                    if not err in downscale_errors:
                        downscale_errors.append(err)
            
            upscaleerrors = loggingCtl.getAutoscalerNoScaleUpErrors(project,cluster)
            if not upscaleerrors == False :
                for err in upscaleerrors:
                    if not err in upscale_errors:
                        upscale_errors.append(err)

    if len(downscale_errors)>0:
        proccessNoScaleDown(downscale_errors)
    if len(upscale_errors)>0:
        proccessNoScaleUp(upscale_errors)

            
main(1)