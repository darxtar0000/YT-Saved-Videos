import os
import json
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import google.oauth2.credentials

class YouTubeApi:
    def __init__(self):
        # Disable OAuthlib's HTTPS verification when running locally.
        # *DO NOT* leave this option enabled in production.
        os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

        self.scopes = ["https://www.googleapis.com/auth/youtube.readonly"]
        self.api_service_name = "youtube"
        self.api_version = "v3"
        self.client_secrets_file = "client_secret.json"

        # Get credentials and create an API client
        try:
            self.credentials = google.oauth2.credentials.Credentials("").from_authorized_user_file("credentials.json", self.scopes)
        except (json.decoder.JSONDecodeError, FileNotFoundError):
            # Open flow to authorize client
            self.flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
                self.client_secrets_file, self.scopes)
            self.credentials = self.flow.run_console()
            # Save credentials to file
            with open("credentials.json", "w") as out_file:
                out_file.write(self.credentials.to_json())

        self.youtube = googleapiclient.discovery.build(
            self.api_service_name, self.api_version, credentials=self.credentials)

    def getVideoDetails(self, videoIds, pageToken=""):
        '''
        Return list of video details from video_ids
        '''
        request = self.youtube.videos().list(
            part="snippet",
            id=",".join(videoIds),
            maxResults=50,
            pageToken=pageToken
        )
        response = request.execute()
        nextPageToken = response.get("nextPageToken")
        if nextPageToken is None:
            return response["items"]
        else:
            return response["items"] + self.getVideoDetails(videoIds, nextPageToken)

    def getUserPlaylists(self, pageToken=""):
        '''
        Return list of user playlists
        '''
        request = self.youtube.playlists().list(
            part="snippet",
            maxResults=50,
            mine=True,
            pageToken=pageToken
        )
        response = request.execute()
        nextPageToken = response.get("nextPageToken")
        if nextPageToken is None:
            return response["items"]
        else:
            return response["items"] + self.getUserPlaylists(nextPageToken)

    def getVideosFromPlaylist(self, playlistId, pageToken=""):
        '''
        Return list of videos in playlist
        '''
        request = self.youtube.playlistItems().list(
            part="snippet,contentDetails,status",
            maxResults=50,
            playlistId=playlistId,
            pageToken=pageToken
        )
        response = request.execute()
        nextPageToken = response.get("nextPageToken")
        totalResults = response["pageInfo"]["totalResults"]
        # if nextPageToken is None:
        #     return response["items"]
        # else:
        #     return response["items"] + self.getVideosFromPlaylist(playlistId, pageToken=nextPageToken)
        return response["items"], nextPageToken, totalResults

    def getChannelDetails(self, channelIds, pageToken=""):
        '''
        Return list of channel details from channel_ids
        '''
        request = self.youtube.channels().list(
            part="snippet",
            id=",".join(channelIds),
            maxResults=50,
            pageToken=pageToken
        )
        response = request.execute()
        nextPageToken = response.get("nextPageToken")
        if nextPageToken is None:
            return response["items"]
        else:
            return response["items"] + self.getChannelDetails(channelIds, nextPageToken)


if __name__ == "__main__":
    api = YouTubeApi()
    print(api.getChannelDetails(["UC35BWbs-oqvE87-yvsE93gg"]))
