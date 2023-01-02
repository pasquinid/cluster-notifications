import slack_sdk
import time
from slack_sdk import WebClient
# from slack.errors import SlackApiError


class Slack:
    def __init__(self,channel,token):
        self.channel = channel
        self.token   = token
        self.client  = WebClient(token=self.token)

    def sendMessage(self,text):
        self.client.chat_postMessage(channel=self.channel,text=text,mrkdwn=True)

    def sendMessageInThread(self,text,ts):
        self.client.chat_postMessage(channel=self.channel,text=text,mrkdwn=True,thread_ts=ts)
        
    def listMessages(self):
        return self.client.conversations_history(channel=self.channel)

    def sendFileInThread(self,filename,ts,file):
        self.client.files_upload(channels=self.channel,thread_ts=ts,filename=filename,file=file)