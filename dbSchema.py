from PyQt5.QtSql import QSqlQuery
import os

def initializeDb(path, db):
    exists = path in os.listdir()
    db.setDatabaseName(path)
    db.open()

    # New database, generating tables
    if not exists:
        queries =  ["""CREATE TABLE "channels" (
                        "channel_id"    TEXT NOT NULL UNIQUE,
                        "channel_title" TEXT NOT NULL,
                        PRIMARY KEY("channel_id")
                    )""",
                    """CREATE TABLE "playlists" (
                        "playlist_id"   TEXT NOT NULL UNIQUE,
                        "playlist_title"    TEXT NOT NULL,
                        "description"   TEXT,
                          PRIMARY KEY("playlist_id")
                    )""",
                    """CREATE TABLE "videos" (
                        "video_id"  TEXT NOT NULL UNIQUE,
                        "video_title"   TEXT NOT NULL,
                        "description"   TEXT,
                        "publish_date"  TEXT NOT NULL,
                        "save_date" TEXT,
                        "channel_id"    TEXT,
                        "notes" TEXT,
                        PRIMARY KEY("video_id"),
                        FOREIGN KEY("channel_id") REFERENCES "channels"("channel_id")
                    )""",
                    """CREATE TABLE "channel_thumbnails" (
                        "channel_id"    TEXT NOT NULL,
                        "size"  TEXT NOT NULL,
                        "width" INTEGER NOT NULL,
                        "height"    INTEGER NOT NULL,
                        "url"   TEXT NOT NULL UNIQUE,
                        FOREIGN KEY("channel_id") REFERENCES "channels"("channel_id"),
                        PRIMARY KEY("channel_id","size")
                    )""",
                    """CREATE TABLE "playlist_thumbnails" (
                        "playlist_id"   TEXT NOT NULL,
                        "size"  TEXT NOT NULL,
                        "width" INTEGER NOT NULL,
                        "height"    INTEGER NOT NULL,
                        "url"   TEXT NOT NULL UNIQUE,
                        FOREIGN KEY("playlist_id") REFERENCES "playlists"("playlist_id"),
                        PRIMARY KEY("playlist_id","size")
                    )""",
                    """CREATE TABLE "video_thumbnails" (
                        "video_id"  TEXT NOT NULL,
                        "size"  TEXT NOT NULL,
                        "width" INTEGER NOT NULL,
                        "height"    INTEGER NOT NULL,
                        "url"   TEXT NOT NULL UNIQUE,
                        FOREIGN KEY("video_id") REFERENCES "videos"("video_id"),
                        PRIMARY KEY("video_id","size")
                    )"""
                    """CREATE TABLE "videos_playlists_link" (
                        "video_id"  TEXT NOT NULL,
                        "playlist_id"   TEXT NOT NULL,
                        FOREIGN KEY("video_id") REFERENCES "videos"("video_id"),
                        FOREIGN KEY("playlist_id") REFERENCES "playlists"("playlist_id"),
                        PRIMARY KEY("video_id","playlist_id")
                    )""",
                    """CREATE TABLE "tags" (
                        "tag_name"  TEXT NOT NULL UNIQUE,
                        PRIMARY KEY("tag_name")
                    )""",
                    """CREATE TABLE "yt_tags" (
                        "tag_name"  TEXT NOT NULL UNIQUE,
                        PRIMARY KEY("tag_name")
                    )""",
                    """CREATE TABLE "tags_parent" (
                        "parent_tag"    TEXT NOT NULL,
                        "child_tag" TEXT NOT NULL,
                        FOREIGN KEY("parent_tag") REFERENCES "tags"("tag_name"),
                        FOREIGN KEY("child_tag") REFERENCES "tags"("tag_name"),
                        PRIMARY KEY("child_tag","parent_tag")
                    )""",
                    """CREATE TABLE "yt_tags_parent" (
                        "parent_tag"    TEXT NOT NULL,
                        "child_tag" TEXT NOT NULL,
                        FOREIGN KEY("parent_tag") REFERENCES "yt_tags"("tag_name"),
                        FOREIGN KEY("child_tag") REFERENCES "yt_tags"("tag_name"),
                        PRIMARY KEY("parent_tag","child_tag")
                    )""",
                    """CREATE TABLE "videos_tags_link" (
                        "video_id"  TEXT NOT NULL,
                        "tag_name"  TEXT NOT NULL,
                        FOREIGN KEY("video_id") REFERENCES "videos"("video_id"),
                        FOREIGN KEY("tag_name") REFERENCES "tags"("tag_name"),
                        PRIMARY KEY("video_id","tag_name")
                    )""",
                    """CREATE TABLE "videos_yt_tags_link" (
                        "video_id"  TEXT NOT NULL,
                        "tag_name"  TEXT NOT NULL,
                        FOREIGN KEY("tag_name") REFERENCES "yt_tags"("tag_name"),
                        FOREIGN KEY("video_id") REFERENCES "videos"("video_id"),
                        PRIMARY KEY("video_id","tag_name")
                    )"""]
        for query in queries:
            q = QSqlQuery(query)
            q.exec()

if __name__ == "__main__":
    dbInitialize("saved.db")
