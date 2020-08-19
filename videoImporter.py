from PyQt5.QtSql import QSqlQuery, QSqlDatabase
import os
import requests
from ytApi import YouTubeApi

DBPATH = "saved.db"

class VideoImporter:
    def __init__(self):
        self.api = YouTubeApi()

    def connectDatabase(self):
        '''
        Connect to SQLite database
        '''
        self.db = QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(DBPATH)
        self.db.open()

    def videoInDb(self, video_id):
        '''
        Checks if db contains video_id
        '''
        query = QSqlQuery()
        query.prepare("""SELECT count(1) FROM videos WHERE video_id = (?)""")
        query.addBindValue(video_id)
        query.exec()
        query.first()
        return query.value(0)

    def channelInDb(self, channel_id):
        '''
        Checks if db contains channel_id
        '''
        query = QSqlQuery()
        query.prepare("""SELECT count(1) FROM channels WHERE channel_id = (?)""")
        query.addBindValue(channel_id)
        query.exec()
        query.first()
        return query.value(0)

    def playlistInDb(self, playlist_id):
        '''
        Checks if db contains playlist_id
        '''
        query = QSqlQuery()
        query.prepare("""SELECT count(1) FROM playlists WHERE playlist_id = (?)""")
        query.addBindValue(playlist_id)
        query.exec()
        query.first()
        return query.value(0)

    def tagInDb(self, tag_name, yt_tags=False):
        '''
        Checks if db contains tag
        '''
        table_name = "yt_tags" if yt_tags else "tags"
        query = QSqlQuery()
        query.prepare("""SELECT count(1) FROM {} WHERE tag_name = (?)""".format(table_name))
        query.addBindValue(tag_name)
        query.exec()
        query.first()
        return query.value(0)

    def getChannelTitle(self, channel_id):
        if self.channelInDb(channel_id):
            query = QSqlQuery()
            query.prepare("""SELECT channel_title FROM channels WHERE channel_id = (?)""")
            query.addBindValue(channel_id)
            query.exec()
            query.first()
            return query.value(0)
        else:
            return ""

    def addChannel(self, channel_id, channel_title):
        if not self.channelInDb(channel_id):
            query = QSqlQuery()
            query.prepare("""INSERT INTO channels VALUES (?, ?)""")
            query.addBindValue(channel_id)
            query.addBindValue(channel_title)
            query.exec()
            return True
        else:
            return False

    def addTags(self, tag_list, yt_tags=False):
        table_name = "yt_tags" if yt_tags else "tags"
        for tag_name in tag_list:
            if not self.tagInDb(tag_name, yt_tags):
                query = QSqlQuery()
                query.prepare(f"""INSERT INTO {table_name} VALUES (?)""")
                query.addBindValue(tag_name)
                query.exec()


    def removeTags(self, tag_list, yt_tags=False):
        table_name_link = "videos_yt_tags_link" if yt_tags else "videos_tags_link"
        table_name = "yt_tags" if yt_tags else "tags"
        for tag_name in tag_list:
            query = QSqlQuery()
            query.prepare(f"""DELETE FROM {table_name_link} WHERE tag_name = (?)""")
            query.addBindValue(tag_name)
            query.exec()
            
            query = QSqlQuery()
            query.prepare(f"""DELETE FROM {table_name} WHERE tag_name = (?)""")
            query.addBindValue(tag_name)
            query.exec()

    def detectParentChildCycle(self, parent_tag, child_tag, yt_tags=False):
        parent_table = "yt_tags_parent" if yt_tags else "tags_parent"
        
        # Build directed graph of child -> parent relationships
        query = QSqlQuery(f"SELECT parent_tag, child_tag FROM {parent_table}")
        query.exec()
        directedGraph = {}
        while query.next():
            pTag = query.value(0)
            cTag = query.value(1)
            directedGraph.setdefault(pTag, set())
            directedGraph.setdefault(cTag, set())
            directedGraph[cTag].add(pTag)

        # Insert new relation into graph
        directedGraph.setdefault(child_tag, set())
        directedGraph.setdefault(parent_tag, set())
        directedGraph[child_tag].add(parent_tag)

        # DFS to find cycle
        def DFSutil(v, visited, recStack):
            visited[v] = True
            recStack[v] = True
            for nxt in directedGraph[v]:
                if visited[nxt] is False:
                    if DFSutil(nxt, visited, recStack):
                        return True
                elif recStack[nxt] is True:
                    return True

            recStack[v] = False
            return False

        tags = directedGraph.keys()
        visited = {tag: False for tag in tags}
        recStack = {tag: False for tag in tags}
        for tag in tags:
            if visited[tag] is False:
                if DFSutil(tag, visited, recStack):
                    return True
        return False

    def addParentChild(self, parent_tag, child_tag, yt_tags=False):
        parent_table = "yt_tags_parent" if yt_tags else "tags_parent"

        invalidInsert = self.detectParentChildCycle(parent_tag, child_tag, yt_tags=False)
        if invalidInsert:
            print("Invalid parent child insert")
            print(f"Inserting {parent_tag} <- {child_tag} results in cycle")
            return 
        queryTemplate = f"""INSERT INTO {parent_table} VALUES (?, ?)"""
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(parent_tag)
        query.addBindValue(child_tag)
        query.exec()
        print(f"added {parent_tag} <- {child_tag} link")

    def removeParentChild(self, parent_tag, child_tag, yt_tags=False):
        parent_table = "yt_tags_parent" if yt_tags else "tags_parent"
        queryTemplate = f"""DELETE FROM {parent_table} WHERE parent_tag = (?) AND child_tag = (?)"""
        query = QSqlQuery()
        query.prepare(queryTemplate)
        query.addBindValue(parent_tag)
        query.addBindValue(child_tag)
        query.exec()
        print(f"removed {parent_tag} <- {child_tag} link")

    def renameTag(self, old_tag, new_tag, yt_tags=False):
        table_name_link = "videos_yt_tags_link" if yt_tags else "videos_tags_link"
        parent_table = "tags_parent" if yt_tags else "yt_tags_parent"
        self.addTags([new_tag], yt_tags)
        queries = [(table_name_link, "tag_name", "tag_name"),
                   (parent_table, "child_tag", "child_tag"),
                   (parent_table, "parent_tag", "parent_tag")]

        for q in queries:
            query = QSqlQuery()
            query.prepare(f"""UPDATE {q[0]} SET {q[1]} = (?) WHERE {q[2]} = (?)""")
            query.addBindValue(new_tag)
            query.addBindValue(old_tag)
            query.exec()

        self.removeTags([old_tag], yt_tags)

    def getAllParents(self, tagSet, yt_tags=False):
        parent_table = "yt_tags_parent" if yt_tags else "tags_parent"

        # Build directed graph of child to parent relationships
        query = QSqlQuery(f"SELECT parent_tag, child_tag FROM {parent_table}")
        query.exec()
        directedGraph = {}
        while query.next():
            pTag = query.value(0)
            cTag = query.value(1)
            directedGraph.setdefault(pTag, set())
            directedGraph.setdefault(cTag, set())
            directedGraph[cTag].add(pTag)

        def recursiveGetParents(tag, directedGraph):
            newTagSet = set()
            newTagSet.add(tag)
            for newTag in directedGraph[tag]:
                newTagSet = newTagSet | recursiveGetParents(newTag, directedGraph)
            return newTagSet

        newTagSet = set()
        for tag in tagSet:
            newTagSet = newTagSet | recursiveGetParents(tag, directedGraph)
        return newTagSet

    def addVideoTags(self, video_ids, tag_list, yt_tags=False):
        table_name = "videos_yt_tags_link" if yt_tags else "videos_tags_link"
        self.addTags(tag_list, yt_tags)
        tagSet = set(tag_list)
        newTagSet = self.getAllParents(tagSet, yt_tags)

        for video_id in video_ids:
            for tag_name in newTagSet:
                query = QSqlQuery()
                query.prepare(f"""INSERT INTO {table_name} VALUES (?, ?)""")
                query.addBindValue(video_id)
                query.addBindValue(tag_name)
                query.exec()

    def removeVideoTags(self, video_ids, tag_list, yt_tags=False):
        table_name = "videos_yt_tags_link" if yt_tags else "videos_tags_link"

        for video_id in video_ids:
            for tag_name in tag_list:
                query = QSqlQuery()
                query.prepare(f"""DELETE FROM {table_name} WHERE video_id = (?) AND tag_name = (?)""")
                query.addBindValue(video_id)
                query.addBindValue(tag_name)
                query.exec()

    def downloadVideoThumbnail(self, video_id, thumbnails, refresh=False):
        thumbnailPath = "thumbnails/v/"
        if not refresh and f"{video_id}.jpg" in os.listdir(thumbnailPath):
            return True
        for size in ("high", "medium", "default"):
            if size in thumbnails:
                url = thumbnails[size]["url"]
                thumbnailRequest = requests.get(url)
                if thumbnailRequest.status_code == 200:
                    with open(os.path.join(thumbnailPath, video_id + ".jpg"), "wb") as f:
                        f.write(thumbnailRequest.content)
                        return True
                else:
                    continue
        else:
            return False

    def downloadChannelThumbnail(self, channel_id, thumbnails, refresh=False):
        thumbnailPath = "thumbnails/c/"
        if not refresh and f"{channel_id}.jpg" in os.listdir(thumbnailPath):
            return True
        for size in ("medium", "default"):
            if size in thumbnails:
                url = thumbnails[size]["url"]
                thumbnailRequest = requests.get(url)
                if thumbnailRequest.status_code == 200:
                    with open(os.path.join(thumbnailPath, channel_id + ".jpg"), "wb") as f:
                        f.write(thumbnailRequest.content)
                        return True
                else:
                    continue
        else:
            return False

    def generateVideoThumbnails(self, video_ids, refresh=False):
        successes = 0
        failedVideos = []
        for video_id in video_ids:
            query = QSqlQuery()
            query.prepare("""SELECT size, url FROM video_thumbnails WHERE video_id=(?)""")
            query.addBindValue(video_id)
            query.exec()
            thumbnails = {}
            while query.next():
                thumbnails[query.value(0)] = {"url": query.value(1)}
            if self.downloadVideoThumbnail(video_id, thumbnails, refresh):
                successes += 1
            else:
                failedVideos.append(video_id)
        print(f"Successfully generated {successes} thumbnails out of {len(video_ids)} video ids.")
        if len(failedVideos) > 0:
            print(f"Couldn't generate thumbnails for these videos: {failedVideos}")

    def generateChannelThumbnails(self, channel_ids, refresh=False):
        successes = 0
        failedChannels = []
        for channel_id in channel_ids:
            query = QSqlQuery()
            query.prepare("""SELECT size, url FROM channel_thumbnails WHERE channel_id=(?)""")
            query.addBindValue(channel_id)
            query.exec()
            thumbnails = {}
            while query.next():
                thumbnails[query.value(0)] = {"url": query.value(1)}
            if self.downloadChannelThumbnail(channel_id, thumbnails, refresh):
                successes += 1
            else:
                failedChannels.append(channel_id)
        print(f"Successfully generated {successes} thumbnails out of {len(channel_ids)} channel ids.")
        if len(failedChannels) > 0:
            print(f"Couldn't generate thumbnails for these channels: {failedChannels}")

    def regenerateAllVideoThumbnails(self, refresh=True):
        query = QSqlQuery("""SELECT video_id FROM videos""")
        query.exec()
        video_ids = []
        while query.next():
            video_ids.append(query.value(0))
        self.generateVideoThumbnails(video_ids, refresh)

    def regenerateAllChannelThumbnails(self, refresh=True):
        query = QSqlQuery("""SELECT channel_id FROM channels""")
        query.exec()
        channel_ids = []
        while query.next():
            channel_ids.append(query.value(0))
        self.generateChannelThumbnails(channel_ids, refresh)

    def insertPlaylist(self, playlist):
        '''
        Insert playlist into db
        '''
        playlist_id = playlist["id"]
        playlist_title = playlist["snippet"]["title"]
        description = playlist["snippet"]["description"]
        thumbnails = playlist["snippet"]["thumbnails"]

        if not self.playlistInDb(playlist_id):
            query = QSqlQuery()
            query.prepare("""INSERT INTO playlists VALUES (?,?,?)""")
            for value in (playlist_id, playlist_title, description):
                query.addBindValue(value)
            query.exec()
            for size, entry in thumbnails.items():
                width = entry["width"]
                height = entry["height"]
                url = entry["url"]
                query = QSqlQuery()
                query.prepare("""INSERT INTO playlist_thumbnails VALUES (?,?,?,?,?)""")
                for value in (playlist_id, size, width, height, url):
                    query.addBindValue(value)
                query.exec()

            # Provide way to update details after initialization
            # else:
            #     c.execute('''UPDATE playlists SET playlist_title=(?), description=(?) WHERE playlist_id=(?)''', (playlist_title, description, playlist_id))
            #     for size, entry in thumbnails.items():
            #         width = entry["width"]
            #         height = entry["height"]
            #         url = entry["url"]
            #         c.execute

    def importUserPlaylists(self):
        '''
        Retrieves all user playlists
        '''
        playlists = self.api.getUserPlaylists()
        playlist_ids = []
        for playlist in playlists:
            self.insertPlaylist(playlist)
            playlist_ids.append(playlist["id"])
        return playlist_ids

    def insertVideo(self, video, playlist_id=None, refresh=False):
        '''
        Inserts video into db
        '''
        video_id = video["contentDetails"]["videoId"]
        title = video["snippet"]["title"]
        description = video["snippet"]["description"]
        publish_date = video["contentDetails"]["videoPublishedAt"]
        save_date = video["snippet"]["publishedAt"]
        thumbnails = video["snippet"]["thumbnails"]

        if playlist_id is not None:
            query = QSqlQuery()
            query.prepare("""INSERT INTO videos_playlists_link VALUES (?,?)""")
            query.addBindValue(video_id)
            query.addBindValue(playlist_id)
            query.exec()

        if not self.videoInDb(video_id):
            query = QSqlQuery("""INSERT INTO videos VALUES (?,?,?,?,?,NULL,NULL)""")
            for value in (video_id, title, description, publish_date, save_date):
                query.addBindValue(value)
            query.exec()

            for size, entry in thumbnails.items():
                width = entry["width"]
                height = entry["height"]
                url = entry["url"]
                query = QSqlQuery()
                query.prepare("""INSERT INTO video_thumbnails VALUES (?,?,?,?,?)""")
                for value in (video_id, size, width, height, url):
                    query.addBindValue(value)
                query.exec()

            self.addVideoTags([video_id], ["untagged"])
            self.downloadVideoThumbnail(video_id, thumbnails, refresh)
            
            return True
        else:
            return False

    def importVideosFromPlaylist(self, playlist_id):
        '''
        Retrieves videos from playlist
        '''
        videos = self.api.getVideosFromPlaylist(playlist_id)
        privateVids = []
        newVids = 0
        for video in videos:
            if video["status"]["privacyStatus"] != "private":
                if self.insertVideo(video, playlist_id):
                    newVids += 1
            else:
                privateVids.append(video["contentDetails"]["videoId"])
        # print(f"Imported {newVids} new videos out of {len(videos)} videos from playlist.")
        # print(f"The following {len(privateVids)} videos are private:")
        # print(privateVids)
        return (newVids, len(videos), privateVids)

    def importVideosFromAllPlaylists(self):
        '''
        Imports videos from every playlist in database
        '''
        playlist_ids = self.importUserPlaylists()
        newVids = 0
        totalVids = 0
        privateVidsList = []
        for playlist_id in playlist_ids:
            nv, tv, pvl = self.importVideosFromPlaylist(playlist_id)
            newVids += nv
            totalVids += tv
            privateVidsList += pvl
        print(f"Imported {newVids} new videos out of {totalVids} videos from playlists.")
        print(f"The following {len(privateVidsList)} videos are private:")
        print(privateVidsList)
        self.updateVideoDetails()
        self.updateChannelThumbnails()

    def updateVideoDetails(self, refresh=False):
        '''
        Updates videos in db with extra details (channels, ids)
        '''
        IDS_PER_API_CALL = 50

        query = QSqlQuery("""SELECT video_id FROM videos""") if refresh else QSqlQuery("""SELECT video_id FROM videos WHERE channel_id IS NULL""")
        query.exec()
        video_ids = []
        while query.next():
            video_ids.append(query.value(0))

        def _importDetails(detail):
            video_id = detail["id"]
            channel_id = detail["snippet"]["channelId"]
            channel_title = detail["snippet"]["channelTitle"]
            yt_tags = detail["snippet"].get("tags", [])
            # print(f"{video_id} -> {channel_id} | {channel_title}")

            self.addChannel(channel_id, channel_title)
            query = QSqlQuery()
            query.prepare("""UPDATE videos SET channel_id=(?) WHERE video_id=(?)""")
            query.addBindValue(channel_id)
            query.addBindValue(video_id)
            query.exec()

            for yt_tag in yt_tags:
                self.addVideoTags([video_id], [yt_tag], yt_tags=True)

        def _getDetails(video_list):
            if len(video_list) == 0:
                return
            elif len(video_list) > IDS_PER_API_CALL:
                details = self.api.getVideoDetails(video_list[:IDS_PER_API_CALL])
                for detail in details:
                    _importDetails(detail)
                _getDetails(video_list[IDS_PER_API_CALL:])
            else:
                details = self.api.getVideoDetails(video_list)
                for detail in details:
                    _importDetails(detail)

        _getDetails(video_ids)

    def updateChannelThumbnails(self, refresh=False):
        '''
        Updates channels in db with extra thumbnails
        '''
        IDS_PER_API_CALL = 50
        query = QSqlQuery()
        if refresh:
            query = QSqlQuery("""SELECT channel_id FROM channels""")
        else:
            query = QSqlQuery("""SELECT channel_id FROM videos
                                 WHERE channel_id NOT IN (
                                    SELECT channel_id
                                    FROM channel_thumbnails
                                    GROUP BY 1
                                )""")
        query.exec()
        channel_ids = []
        while query.next():
            channel_ids.append(query.value(0))

        def _importDetails(detail):
            channel_id = detail["id"]
            thumbnails = detail["snippet"]["thumbnails"]
            
            if refresh:
                query = QSqlQuery()
                query.prepare("""DELETE FROM channel_thumbnails WHERE channel_id = (?)""")
                query.addBindValue(channel_id)
                query.exec()

            for size, entry in thumbnails.items():
                width = entry["width"]
                height = entry["height"]
                url = entry["url"]
                query = QSqlQuery()
                query.prepare("""INSERT INTO channel_thumbnails VALUES (?,?,?,?,?)""")
                for value in (channel_id, size, width, height, url):
                    query.addBindValue(value)
                query.exec()

        def _getDetails(channel_list):
            if len(channel_list) == 0:
                return
            elif len(channel_list) > IDS_PER_API_CALL:
                details = self.api.getChannelDetails(channel_list[:IDS_PER_API_CALL])
                for detail in details:
                    _importDetails(detail)
                _getDetails(channel_list[IDS_PER_API_CALL:])
            else:
                details = self.api.getChannelDetails(channel_list)
                for detail in details:
                    _importDetails(detail)

        _getDetails(channel_ids)
        self.generateChannelThumbnails(channel_ids)


if __name__ == "__main__":
    importer = VideoImporter()
    importer.connectDatabase()
    # importer.updateChannelThumbnails(True)
