import random
import sys, os, math
import numpy as np
import sounddevice as sd
import librosa
import sqlite3
from datetime import datetime
from mutagen import File
from mutagen.id3 import ID3
from mutagen.mp3 import MP3
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from mutagen.easyid3 import EasyID3
from mutagen.mp4 import MP4
from mutagen.asf import ASF

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QFileDialog, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QSlider, QStyle,
    QFrame, QGroupBox, QGridLayout, QMessageBox, QMenuBar, QLineEdit,
    QMenu
)
from PyQt5.QtGui import QIcon, QPainter, QColor, QFont, QLinearGradient, QBrush, QPen, QPolygonF, QPainterPath, QRadialGradient
from PyQt5.QtCore import QThread, Qt, QTimer, pyqtSignal, QPointF, QSize, QRect


# ================= METADATA EXTRACTION FUNCTIONS =================

def extract_metadata(file_path):
    """Extract metadata from audio file using mutagen"""
    metadata = {
        'title': '',
        'artist': 'Unknown Artist',
        'album': 'Unknown Album',
        'genre': 'Unknown',
        'year': 0,
        'track_number': 0,
        'bitrate': 0,
        'sample_rate': 0,
        'channels': 0
    }
    
    try:
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.mp3':
            try:
                try:
                    audio = EasyID3(file_path)
                    if 'title' in audio:
                        metadata['title'] = str(audio['title'][0])
                    if 'artist' in audio:
                        metadata['artist'] = str(audio['artist'][0])
                    if 'album' in audio:
                        metadata['album'] = str(audio['album'][0])
                    if 'genre' in audio:
                        metadata['genre'] = str(audio['genre'][0])
                    if 'date' in audio:
                        try:
                            metadata['year'] = int(str(audio['date'][0])[:4])
                        except:
                            pass
                    if 'tracknumber' in audio:
                        try:
                            metadata['track_number'] = int(str(audio['tracknumber'][0]).split('/')[0])
                        except:
                            pass
                except:
                    audio = ID3(file_path)
                    if 'TIT2' in audio:
                        metadata['title'] = str(audio['TIT2'])
                    if 'TPE1' in audio:
                        metadata['artist'] = str(audio['TPE1'])
                    if 'TALB' in audio:
                        metadata['album'] = str(audio['TALB'])
                    if 'TCON' in audio:
                        metadata['genre'] = str(audio['TCON'])
                    if 'TDRC' in audio:
                        try:
                            metadata['year'] = int(str(audio['TDRC'])[:4])
                        except:
                            pass
                    if 'TRCK' in audio:
                        try:
                            metadata['track_number'] = int(str(audio['TRCK']).split('/')[0])
                        except:
                            pass
            except Exception as e:
                print(f"MP3 metadata error for {os.path.basename(file_path)}: {e}")
            
        elif ext == '.flac':
            try:
                audio = FLAC(file_path)
                if audio.tags:
                    if 'title' in audio.tags:
                        metadata['title'] = audio.tags['title'][0]
                    if 'artist' in audio.tags:
                        metadata['artist'] = audio.tags['artist'][0]
                    if 'album' in audio.tags:
                        metadata['album'] = audio.tags['album'][0]
                    if 'genre' in audio.tags:
                        metadata['genre'] = audio.tags['genre'][0]
                    if 'date' in audio.tags:
                        try:
                            metadata['year'] = int(audio.tags['date'][0][:4])
                        except:
                            pass
                    if 'tracknumber' in audio.tags:
                        try:
                            metadata['track_number'] = int(audio.tags['tracknumber'][0].split('/')[0])
                        except:
                            pass
            except Exception as e:
                print(f"FLAC metadata error for {os.path.basename(file_path)}: {e}")
                
        elif ext == '.ogg':
            try:
                audio = OggVorbis(file_path)
                if audio.tags:
                    if 'title' in audio.tags:
                        metadata['title'] = audio.tags['title'][0]
                    if 'artist' in audio.tags:
                        metadata['artist'] = audio.tags['artist'][0]
                    if 'album' in audio.tags:
                        metadata['album'] = audio.tags['album'][0]
                    if 'genre' in audio.tags:
                        metadata['genre'] = audio.tags['genre'][0]
            except Exception as e:
                print(f"OGG metadata error for {os.path.basename(file_path)}: {e}")
                
        elif ext == '.m4a' or ext == '.mp4':
            try:
                audio = MP4(file_path)
                if audio.tags:
                    if '\xa9nam' in audio.tags:
                        metadata['title'] = audio.tags['\xa9nam'][0]
                    if '\xa9ART' in audio.tags:
                        metadata['artist'] = audio.tags['\xa9ART'][0]
                    if '\xa9alb' in audio.tags:
                        metadata['album'] = audio.tags['\xa9alb'][0]
                    if '\xa9gen' in audio.tags:
                        metadata['genre'] = audio.tags['\xa9gen'][0]
            except Exception as e:
                print(f"M4A/MP4 metadata error for {os.path.basename(file_path)}: {e}")
        
        elif ext == '.wma':
            try:
                audio = ASF(file_path)
                if audio.tags:
                    if 'Title' in audio.tags:
                        metadata['title'] = str(audio.tags['Title'][0])
                    if 'Author' in audio.tags:
                        metadata['artist'] = str(audio.tags['Author'][0])
                    if 'WM/AlbumTitle' in audio.tags:
                        metadata['album'] = str(audio.tags['WM/AlbumTitle'][0])
                    if 'WM/Genre' in audio.tags:
                        metadata['genre'] = str(audio.tags['WM/Genre'][0])
            except Exception as e:
                print(f"WMA metadata error for {os.path.basename(file_path)}: {e}")
        
        else:
            try:
                audio = File(file_path, easy=True)
                if audio is not None:
                    if 'title' in audio:
                        metadata['title'] = str(audio['title'][0])
                    if 'artist' in audio:
                        metadata['artist'] = str(audio['artist'][0])
                    if 'album' in audio:
                        metadata['album'] = str(audio['album'][0])
                    if 'genre' in audio:
                        metadata['genre'] = str(audio['genre'][0])
                    if 'date' in audio:
                        try:
                            metadata['year'] = int(str(audio['date'][0])[:4])
                        except:
                            pass
                    if 'tracknumber' in audio:
                        try:
                            metadata['track_number'] = int(str(audio['tracknumber'][0]).split('/')[0])
                        except:
                            pass
            except Exception as e:
                print(f"Generic metadata error for {os.path.basename(file_path)}: {e}")
        
        try:
            audio_info = File(file_path)
            if audio_info is not None:
                if hasattr(audio_info.info, 'bitrate'):
                    metadata['bitrate'] = audio_info.info.bitrate // 1000
                if hasattr(audio_info.info, 'sample_rate'):
                    metadata['sample_rate'] = audio_info.info.sample_rate
                if hasattr(audio_info.info, 'channels'):
                    metadata['channels'] = audio_info.info.channels
        except:
            pass
            
    except Exception as e:
        print(f"General metadata error for {os.path.basename(file_path)}: {e}")
    
    for key in ['title', 'artist', 'album', 'genre']:
        if metadata[key] and isinstance(metadata[key], str):
            metadata[key] = metadata[key].strip()
            metadata[key] = metadata[key].replace('\x00', '').replace('\ufffd', '')
            if len(metadata[key]) > 200:
                metadata[key] = metadata[key][:197] + "..."
    
    if not metadata['title']:
        metadata['title'] = os.path.splitext(os.path.basename(file_path))[0]
    
    return metadata

def get_audio_duration(file_path):
    """Get audio duration using mutagen (more reliable than librosa for metadata)"""
    try:
        audio = File(file_path)
        if audio is not None and hasattr(audio.info, 'length'):
            return audio.info.length
    except:
        pass
    
    try:
        return librosa.get_duration(path=file_path)
    except:
        return 0





# ================= DATABASE MANAGER =================
class MusicDatabase:
    def __init__(self):
        self.db_path = "music_library.db"
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create tables if they don't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                last_scan TIMESTAMP,
                scan_duration REAL
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tracks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                folder_id INTEGER,
                file_path TEXT UNIQUE NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER,
                duration REAL,
                title TEXT,
                artist TEXT,
                album TEXT,
                genre TEXT,
                year INTEGER,
                track_number INTEGER,
                bitrate INTEGER,
                sample_rate INTEGER,
                channels INTEGER,
                last_modified TIMESTAMP,
                created_date TIMESTAMP,
                play_count INTEGER DEFAULT 0,
                last_played TIMESTAMP,
                rating INTEGER DEFAULT 0,
                FOREIGN KEY (folder_id) REFERENCES folders (id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS playlist_tracks (
                playlist_id INTEGER,
                track_id INTEGER,
                position INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (playlist_id, track_id),
                FOREIGN KEY (playlist_id) REFERENCES playlists (id),
                FOREIGN KEY (track_id) REFERENCES tracks (id)
            )
        ''')
        
        # Create recent_folders table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recent_folders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT UNIQUE NOT NULL,
                last_accessed TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create config table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS player_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        
        # Create indexes for faster queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracks_file_path ON tracks(file_path)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracks_artist ON tracks(artist)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracks_album ON tracks(album)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracks_genre ON tracks(genre)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_tracks_folder ON tracks(folder_id)')
        
        conn.commit()
        conn.close()
    
    def add_folder(self, folder_path):
        """Add a scanned folder to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO folders (path, last_scan)
                VALUES (?, CURRENT_TIMESTAMP)
            ''', (folder_path,))
            folder_id = cursor.lastrowid
            conn.commit()
            return folder_id
        except Exception as e:
            print(f"Error adding folder: {e}")
            return None
        finally:
            conn.close()
    
    def update_folder_scan_time(self, folder_path, scan_duration=None):
        """Update the last scan time for a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            if scan_duration:
                cursor.execute('''
                    UPDATE folders 
                    SET last_scan = CURRENT_TIMESTAMP, scan_duration = ?
                    WHERE path = ?
                ''', (scan_duration, folder_path))
            else:
                cursor.execute('''
                    UPDATE folders 
                    SET last_scan = CURRENT_TIMESTAMP
                    WHERE path = ?
                ''', (folder_path,))
            conn.commit()
        except Exception as e:
            print(f"Error updating folder: {e}")
        finally:
            conn.close()
    
    def get_folder_id(self, folder_path):
        """Get folder ID from path"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM folders WHERE path = ?', (folder_path,))
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None
    
    def folder_needs_rescan(self, folder_path, max_age_days=30):
        """Check if folder needs rescan based on last scan time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT last_scan FROM folders 
            WHERE path = ?
        ''', (folder_path,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result or result[0] is None:
            return True  # Never scanned
        
        # Parse timestamp and check if older than max_age_days
        try:
            last_scan = datetime.strptime(result[0], '%Y-%m-%d %H:%M:%S')
            days_diff = (datetime.now() - last_scan).days
            return days_diff > max_age_days
        except:
            return True  # If timestamp format is invalid, rescan
    
    def add_track(self, folder_id, file_path, file_name, file_size, duration, metadata=None):
        """Add a track to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Extract metadata
        title = metadata.get('title', file_name) if metadata else file_name
        artist = metadata.get('artist', 'Unknown Artist') if metadata else 'Unknown Artist'
        album = metadata.get('album', 'Unknown Album') if metadata else 'Unknown Album'
        genre = metadata.get('genre', 'Unknown') if metadata else 'Unknown'
        year = metadata.get('year', 0) if metadata else 0
        track_number = metadata.get('track_number', 0) if metadata else 0
        bitrate = metadata.get('bitrate', 0) if metadata else 0
        sample_rate = metadata.get('sample_rate', 0) if metadata else 0
        channels = metadata.get('channels', 0) if metadata else 0
        
        # Get file modification time
        try:
            last_modified = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime('%Y-%m-%d %H:%M:%S')
        except:
            last_modified = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            cursor.execute('''
                INSERT OR REPLACE INTO tracks 
                (folder_id, file_path, file_name, file_size, duration, title, artist, album, 
                 genre, year, track_number, bitrate, sample_rate, channels, last_modified, created_date)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE((SELECT created_date FROM tracks WHERE file_path = ?), CURRENT_TIMESTAMP))
            ''', (folder_id, file_path, file_name, file_size, duration, title, artist, album, 
                  genre, year, track_number, bitrate, sample_rate, channels, last_modified, file_path))
            
            conn.commit()
            return cursor.lastrowid
        except Exception as e:
            print(f"Error adding track {file_path}: {e}")
            return None
        finally:
            conn.close()
    
    def get_tracks_from_folder(self, folder_path):
        """Get all tracks from a folder (fast database query)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT t.file_path, t.file_name, t.duration, t.title, t.artist, t.album, t.genre
            FROM tracks t
            JOIN folders f ON t.folder_id = f.id
            WHERE f.path = ?
            ORDER BY t.artist, t.album, t.track_number, t.title
        ''', (folder_path,))
        
        tracks = cursor.fetchall()
        conn.close()
        
        return tracks
    
    def track_exists(self, file_path):
        """Check if track exists in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM tracks WHERE file_path = ?', (file_path,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def update_track_play_stats(self, file_path):
        """Update play count and last played time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE tracks 
                SET play_count = play_count + 1, last_played = CURRENT_TIMESTAMP
                WHERE file_path = ?
            ''', (file_path,))
            conn.commit()
        except Exception as e:
            print(f"Error updating play stats: {e}")
        finally:
            conn.close()
    
    def get_recently_played(self, limit=50):
        """Get recently played tracks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, file_name, artist, title, play_count, last_played
            FROM tracks 
            WHERE last_played IS NOT NULL
            ORDER BY last_played DESC
            LIMIT ?
        ''', (limit,))
        
        tracks = cursor.fetchall()
        conn.close()
        
        return tracks
    
    def get_most_played(self, limit=50):
        """Get most played tracks"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_path, file_name, artist, title, play_count, last_played
            FROM tracks 
            WHERE play_count > 0
            ORDER BY play_count DESC
            LIMIT ?
        ''', (limit,))
        
        tracks = cursor.fetchall()
        conn.close()
        
        return tracks
    
    def search_tracks(self, search_term, limit=100):
        """Search tracks by title, artist, or album"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        search_pattern = f"%{search_term}%"
        cursor.execute('''
            SELECT file_path, file_name, artist, title, album, duration
            FROM tracks 
            WHERE title LIKE ? OR artist LIKE ? OR album LIKE ? OR genre LIKE ? OR file_name LIKE ?
            ORDER BY artist, album, title
            LIMIT ?
        ''', (search_pattern, search_pattern, search_pattern, search_pattern, search_pattern, limit))
        
        tracks = cursor.fetchall()
        conn.close()
        
        return tracks
    
    def delete_folder_tracks(self, folder_path):
        """Delete all tracks from a folder"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get folder id
            folder_id = self.get_folder_id(folder_path)
            if folder_id:
                cursor.execute('DELETE FROM tracks WHERE folder_id = ?', (folder_id,))
                conn.commit()
        except Exception as e:
            print(f"Error deleting folder tracks: {e}")
        finally:
            conn.close()
    
    def cleanup_missing_files(self, folder_path):
        """Remove entries for files that no longer exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get all tracks for this folder
            cursor.execute('''
                SELECT t.id, t.file_path 
                FROM tracks t
                JOIN folders f ON t.folder_id = f.id
                WHERE f.path = ?
            ''', (folder_path,))
            
            tracks = cursor.fetchall()
            deleted_count = 0
            
            for track_id, file_path in tracks:
                if not os.path.exists(file_path):
                    cursor.execute('DELETE FROM tracks WHERE id = ?', (track_id,))
                    deleted_count += 1
            
            conn.commit()
            print(f"Cleaned up {deleted_count} missing files from database")
            return deleted_count
        except Exception as e:
            print(f"Error cleaning up missing files: {e}")
            return 0
        finally:
            conn.close()
    
    def add_recent_folder(self, folder_path):
        """Add a folder to recent folders list"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Update or insert the folder
        cursor.execute('''
            INSERT OR REPLACE INTO recent_folders (path, last_accessed)
            VALUES (?, CURRENT_TIMESTAMP)
        ''', (folder_path,))
        
        conn.commit()
        conn.close()

    def get_recent_folders(self, limit=10):
        """Get list of recently accessed folders"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT path, last_accessed 
            FROM recent_folders 
            ORDER BY last_accessed DESC 
            LIMIT ?
        ''', (limit,))
        
        folders = cursor.fetchall()
        conn.close()
        
        return folders

    def save_last_folder(self, folder_path):
        """Save the last loaded folder to a config table"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO player_config (key, value)
            VALUES (?, ?)
        ''', ('last_folder', folder_path))
        
        conn.commit()
        conn.close()

    def get_last_folder(self):
        """Get the last loaded folder from config"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT value FROM player_config WHERE key = 'last_folder'
        ''')
        
        result = cursor.fetchone()
        conn.close()
        
        return result[0] if result else None

# ================= AUDIO THREAD =================
class AudioThread(QThread):
    position_changed = pyqtSignal(float)
    loading_complete = pyqtSignal(str)
    loading_started = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8

        self.mono = None
        self.sr = 44100
        self.current_position = 0.0
        self.angle = 0.0
        self.duration = 0.0
        self.force_seek = None

        self.visual_samples = np.zeros(256, dtype=np.float32)

    def load(self, file):
        """Load audio file"""
        self.loading_started.emit(os.path.basename(file))
        
        try:
            y, self.sr = librosa.load(file, mono=True, sr=22050)
            y = y / max(np.max(np.abs(y)), 1e-6)
            self.mono = y.astype(np.float32)
            self.current_position = 0.0
            self.angle = 0.0
            self.duration = len(y) / self.sr
            self.position_changed.emit(0.0)
            self.loading_complete.emit(os.path.basename(file))
            return True
        except Exception as e:
            print(f"Error loading file: {e}")
            return False

    def seek(self, position):
        """Force seek to position in seconds"""
        if self.mono is not None:
            position = max(0.0, min(position, self.duration))
            print(f"AudioThread: Seeking to {position:.2f} seconds")
            self.force_seek = position
            self.current_position = position

    def callback(self, outdata, frames, time, status):
        if status:
            print(status)
            
        if self.mono is None:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return

        out = np.zeros((frames, 2), np.float32)
        
        if self.force_seek is not None:
            self.current_position = self.force_seek
            self.force_seek = None
        
        start_sample = int(self.current_position * self.sr)
        
        if start_sample >= len(self.mono):
            outdata[:] = np.zeros((frames, 2), np.float32)
            self.running = False
            return
        
        if not self.running:
            outdata[:] = np.zeros((frames, 2), np.float32)
            return
        
        frames_processed = 0
        for i in range(frames):
            if start_sample + i >= len(self.mono):
                self.running = False
                break

            base = self.mono[start_sample + i] * self.volume
            self.visual_samples[i % 256] = base

            pan = (math.sin(self.angle) + 1) * 0.5
            self.angle += 0.0006

            L = R = base

            if self.effect == "Rock":
                L *= 1.35
                R *= 1.35

            elif self.effect == "3D":
                L = base * (1 - pan) * 1.3
                R = base * pan * 1.3

            elif self.effect == "8D":
                depth = 1.0 - abs(math.cos(self.angle)) * 0.3
                L = base * (1 - pan) * depth * 1.4
                R = base * pan * depth * 1.4

            elif self.effect == "Dolby":
                side = math.sin(self.angle) * 0.3
                bass = base * 0.3
                L = base + side + bass
                R = base - side + bass

            out[i, 0] = np.tanh(L)
            out[i, 1] = np.tanh(R)
            frames_processed += 1
        
        self.current_position += frames_processed / self.sr
        self.position_changed.emit(self.current_position)

        outdata[:] = out

    def run(self):
        print("AudioThread.run() started")
        self.running = True
        with sd.OutputStream(
            samplerate=self.sr,
            channels=2,
            callback=self.callback,
            blocksize=1024
        ):
            while True:
                sd.sleep(50)
                if not hasattr(self, '_should_exit'):
                    self._should_exit = False
                if self._should_exit:
                    break
        
        print("AudioThread.run() ended")

    def stop(self):
        self.running = False
        self._should_exit = True


# ================= SPECTRUM VISUALIZER =================
class Spectrum(QWidget):
    def __init__(self, audio):
        super().__init__()
        self.audio = audio
        self.mode = "Bars"
        self.phase = 0.0
        self.setMinimumHeight(250)

    def set_mode(self, mode):
        self.mode = mode
        self.update()

    def paintEvent(self, e):
        if self.audio.visual_samples is None:
            return

        data = np.abs(np.fft.rfft(self.audio.visual_samples))[:64]

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w, h = self.width(), self.height()
        cx, cy = w // 2, h // 2

        if self.mode == "Bars":
            bw = w / len(data)
            for i, v in enumerate(data):
                bh = min(v * 40, h)
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawRect(
                    int(i * bw),
                    h - int(bh),
                    int(bw - 2),
                    int(bh)
                )

        elif self.mode == "Wave particle":
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(0, 200, 255, 180), 2))
            
            self.phase += 0.04
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                painter.setBrush(QColor.fromHsv((i * 6) % 360, 255, 255))
                painter.drawEllipse(x - 3, y - 3, 6, 6)
                
        elif self.mode == "Wave":
            if not hasattr(self, 'trail_history'):
                self.trail_history = []
            
            if len(self.trail_history) > 10:
                self.trail_history.pop(0)
            
            painter.setPen(Qt.NoPen)
            for trail_idx, trail in enumerate(self.trail_history):
                alpha = int(100 * (trail_idx + 1) / len(self.trail_history))
                painter.setBrush(QColor(0, 200, 255, alpha))
                for x, y in trail:
                    painter.drawEllipse(x - 2, y - 2, 4, 4)
            
            current_frame = []
            self.phase += 0.04
            
            painter.setPen(QPen(QColor(0, 200, 255, 180), 1))
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                
                current_frame.append((x, y))
                
                hue = (i * 6 + int(self.phase * 50)) % 360
                painter.setBrush(QColor.fromHsv(hue, 255, 255, 220))
                painter.drawEllipse(x - 3, y - 3, 6, 6)
                
                if i > 0 and i % 5 == 0:
                    prev_x = int(((i-1) / len(data)) * w)
                    prev_y = int(cy + math.sin(self.phase + (i-1) * 0.25) * data[i-1] * 25)
                    painter.setPen(QPen(QColor(0, 200, 255, 80), 1))
                    painter.drawLine(prev_x, prev_y, x, y)
            
            self.trail_history.append(current_frame)

        elif self.mode == "Circle":
            radius = min(cx, cy) - 30
            for i, v in enumerate(data):
                angle = (i / len(data)) * 2 * math.pi
                r = radius + v * 25
                x = cx + math.cos(angle) * r
                y = cy + math.sin(angle) * r
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(int(x), int(y), 6, 6)
        
        elif self.mode == "Disk":
            max_radius = min(cx, cy) - 10
            disk_radius = max_radius * 0.5
            max_bar_length = max_radius - disk_radius - 5
            
            outer_ring_radius = disk_radius * 0.95
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(180, 180, 200, 200), 3))
            painter.drawEllipse(int(cx - outer_ring_radius), int(cy - outer_ring_radius), 
                               int(outer_ring_radius * 2), int(outer_ring_radius * 2))
            
            ring_colors = [
                QColor(255, 0, 0, 180),
                QColor(255, 127, 0, 180),
                QColor(255, 255, 0, 180),
                QColor(0, 255, 0, 180),
                QColor(0, 0, 255, 180),
                QColor(75, 0, 130, 180),
                QColor(148, 0, 211, 180)
            ]
            
            for i, color in enumerate(ring_colors):
                ring_radius = disk_radius * (0.7 - (i * 0.08))
                if ring_radius > disk_radius * 0.2:
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(color, 2))
                    painter.drawEllipse(int(cx - ring_radius), int(cy - ring_radius), 
                                       int(ring_radius * 2), int(ring_radius * 2))
            
            data_area_radius = disk_radius * 0.65
            gradient = QLinearGradient(cx - data_area_radius, cy - data_area_radius, 
                                      cx + data_area_radius, cy + data_area_radius)
            gradient.setColorAt(0, QColor(0, 100, 200, 180))
            gradient.setColorAt(0.5, QColor(0, 150, 255, 200))
            gradient.setColorAt(1, QColor(0, 100, 200, 180))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(0, 180, 255, 220), 2))
            painter.drawEllipse(int(cx - data_area_radius), int(cy - data_area_radius), 
                               int(data_area_radius * 2), int(data_area_radius * 2))
            
            center_hole_radius = disk_radius * 0.15
            center_gradient = QLinearGradient(cx - center_hole_radius, cy - center_hole_radius,
                                             cx + center_hole_radius, cy + center_hole_radius)
            center_gradient.setColorAt(0, QColor(220, 220, 220, 200))
            center_gradient.setColorAt(1, QColor(180, 180, 180, 200))
            
            painter.setBrush(QBrush(center_gradient))
            painter.setPen(QPen(QColor(200, 200, 200, 150), 2))
            painter.drawEllipse(int(cx - center_hole_radius), int(cy - center_hole_radius), 
                               int(center_hole_radius * 2), int(center_hole_radius * 2))
            
            spindle_radius = center_hole_radius * 0.4
            painter.setBrush(QBrush(QColor(100, 100, 120, 200)))
            painter.setPen(QPen(QColor(80, 80, 100, 150), 1))
            painter.drawEllipse(int(cx - spindle_radius), int(cy - spindle_radius), 
                               int(spindle_radius * 2), int(spindle_radius * 2))
            
            bar_count = len(data)
            bar_width = 6
            
            for i, v in enumerate(data):
                angle = (i / bar_count) * 2 * math.pi
                bar_length = min(v * 80, max_bar_length)
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                
                start_x = cx + math.cos(angle) * disk_radius
                start_y = cy + math.sin(angle) * disk_radius
                end_x = cx + math.cos(angle) * (disk_radius + bar_length)
                end_y = cy + math.sin(angle) * (disk_radius + bar_length)
                
                perp_angle = angle + math.pi / 2
                perp_dx = math.cos(perp_angle) * bar_width / 2
                perp_dy = math.sin(perp_angle) * bar_width / 2
                
                bar_polygon = QPolygonF([
                    QPointF(start_x - perp_dx, start_y - perp_dy),
                    QPointF(start_x + perp_dx, start_y + perp_dy),
                    QPointF(end_x + perp_dx, end_y + perp_dy),
                    QPointF(end_x - perp_dx, end_y - perp_dy)
                ])
                
                painter.drawPolygon(bar_polygon)
                
                if bar_length > 5:
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(color.lighter(150), 1))
                    painter.drawEllipse(int(end_x - 2), int(end_y - 2), 4, 4)

    def set_mode(self, mode):
        self.mode = mode
        self.update()


# ================= MUSIC PLAYER UI =================
class MusicPlayer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎧 Professional DJ Music Player")
        self.resize(1200, 720)
        self.db = MusicDatabase()
        
        # Set the exact background color from the image
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0d1117;
            }
            QWidget {
                background-color: #0d1117;
                color: #c9d1d9;
            }
        """)
        
        self.audio = AudioThread()
        self.files = []
        self.durations = []
        self.current_file_index = -1
        self.user_is_seeking = False
        self.playing_color_index = 0
        
        self.play_mode = "sequential"
        self.shuffled_indices = []
        self.original_indices = []
        self.is_shuffled = False
        self.current_shuffle_index = -1
        
        self.current_folder_path = None
        self.all_tracks = []
        self.all_files = []
        self.all_durations = []

        self.init_ui()

        self.audio.position_changed.connect(self.update_progress_from_audio)
        self.audio.loading_started.connect(self.show_loading)
        self.audio.loading_complete.connect(self.hide_loading)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualizer)
        self.timer.start(30)
        QTimer.singleShot(100, self.load_last_folder)


    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # ===== MENU BAR =====
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #161b22;
                color: #c9d1d9;
                border-bottom: 1px solid #30363d;
            }
            QMenuBar::item {
                padding: 4px 10px;
                background-color: transparent;
            }
            QMenuBar::item:selected {
                background-color: #30363d;
                border-radius: 4px;
            }
            QMenu {
                background-color: #161b22;
                color: #c9d1d9;
                border: 1px solid #30363d;
            }
            QMenu::item {
                padding: 5px 25px 5px 20px;
            }
            QMenu::item:selected {
                background-color: #1f6feb;
            }
            QComboBox {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 4px;
                border-radius: 3px;
                font-size: 11px;
                color: white;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            
            QComboBox::down-arrow {
                width: 12px;
                height: 12px;
            }
            
            QComboBox QAbstractItemView {
                background-color: #2d2d2d;
                border: 1px solid #444;
                selection-background-color: #00b4d8;
                color: white;
                outline: none;
            }
            
            QComboBox QAbstractItemView::item {
                padding: 4px;
                border: none;
            }
            
            QComboBox QAbstractItemView::item:hover {
                background-color: #3d3d3d;
            }
            

        """)
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        load_folder_action = file_menu.addAction('Load Folder...')
        load_folder_action.triggered.connect(self.load_folder)
        load_folder_action.setShortcut('Ctrl+O')
        
        file_menu.addSeparator()
        
        # Add Most Played to File menu
        most_played_action = file_menu.addAction('Most Played')
        most_played_action.triggered.connect(self.show_most_played_dialog)
        
        # Add Recently Played to File menu
        recent_action = file_menu.addAction('Recently Played')
        recent_action.triggered.connect(self.show_recently_played_dialog)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Ctrl+Q')
        
        # View menu
        view_menu = menubar.addMenu('View')
        self.most_played_action = view_menu.addAction('Most Played')
        self.recent_action = view_menu.addAction('Recently Played')
        
        # Visual menu
        visual_menu = menubar.addMenu('Visual')
        visual_menu.addAction('Bars').triggered.connect(lambda: self.spectrum.set_mode("Bars"))
        visual_menu.addAction('Wave').triggered.connect(lambda: self.spectrum.set_mode("Wave"))
        visual_menu.addAction('Circle').triggered.connect(lambda: self.spectrum.set_mode("Circle"))
        visual_menu.addAction('Disk').triggered.connect(lambda: self.spectrum.set_mode("Disk"))

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        self.title_label = QLabel("🎧 Professional DJ Music Player")
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #58a6ff; 
                background-color: #0a0a0a;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
            }
        """)
        self.title_label.setMinimumHeight(40)
        
        self.loading_label = QLabel("")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #ff9900; font-style: italic;")
        
        top_bar.addWidget(self.title_label)
        top_bar.addStretch()
        top_bar.addWidget(self.loading_label)
        
        main_layout.addLayout(top_bar)

        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # ===== LEFT PANEL - Playlist =====
        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)
        
        # Playlist group
        playlist_group = QGroupBox("Playlist")
        playlist_group.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                color: #58a6ff;
                border: 2px solid #30363d;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #161b22;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)
        playlist_layout = QVBoxLayout()
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(5, 5, 5, 5)
        
        #search_label = QLabel("Search:")
        #search_label.setStyleSheet("color: #c9d1d9; font-weight: bold;")
        #search_label.setFixedWidth(50)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search tracks...")
        self.search_box.setStyleSheet("""
            QLineEdit {
                background-color: #0d1117;
                color: #c9d1d9;
                border: 1px solid #30363d;
                border-radius: 4px;
                padding: 5px;
                selection-background-color: #1f6feb;
            }
            QLineEdit:focus {
                border: 1px solid #1f6feb;
            }
        """)
        
        #search_layout.addWidget(search_label)
        self.search_box.textChanged.connect(self.filter_tracks)
        search_layout.addWidget(self.search_box)
        playlist_layout.addLayout(search_layout)
        
        # Table
        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Tracks", "Duration", "", ""])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setColumnWidth(0, 200)
        self.table.setColumnWidth(1, 150)
        self.table.setColumnWidth(2, 80)
        self.table.setColumnWidth(3, 80)
        
        self.table.cellDoubleClicked.connect(self.play_selected)
        
        # Set table styles to match image colors
        # self.table.setStyleSheet("""
        #     QTableWidget {
        #         background-color: #1e1e1e;
        #         color: white;
        #         gridline-color: #333;
        #         border: none;
        #         font-size: 11px;
        #         alternate-background-color: #252525;
        #     }
        #     QTableWidget::item {
        #         background-color: transparent;
        #         color: #cccccc;
        #         border-bottom: 1px solid #333;
        #         padding: 4px;
        #     }
        #     QTableWidget::item:selected {
        #         background-color: #00b4d8;
        #         color: white;
        #         font-weight: bold;
        #     }
        #     /* Gray background for playing track */
        #     QTableWidget::item[playing="true"] {
        #         background-color: #404040;
        #         color: white;
        #         font-weight: bold;
        #     }
        #     /* Colorful disc for playing track - will be set dynamically */
        #     QHeaderView::section {
        #         background-color: #2d2d2d;
        #         color: #00b4d8;
        #         font-weight: bold;
        #         padding: 6px;
        #         border: none;
        #         border-bottom: 2px solid #00b4d8;
        #     }
        #     QTableWidget QScrollBar:vertical {
        #         background-color: #1a1a1a;
        #         width: 12px;
        #     }
        #     QTableWidget QScrollBar::handle:vertical {
        #         background-color: #444;
        #         border-radius: 6px;
        #         min-height: 20px;
        #     }
        #     QTableWidget QScrollBar::handle:vertical:hover {
        #         background-color: #555;
        #     }
        # """)
        # Set table styles to match image colors
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                color: white;
                gridline-color: #333;
                border: none;
                font-size: 11px;
                alternate-background-color: #252525;
            }
            QTableWidget::item {
                background-color: transparent;
                color: #cccccc;
                border-bottom: 1px solid #333;
                padding: 4px;
            }
            QTableWidget::item:selected {
                background-color: #00b4d8;
                color: white;
                font-weight: bold;
            }
            /* Gray background for playing track */
            QTableWidget::item[playing="true"] {
                background-color: #404040;
                color: white;
                font-weight: bold;
            }
            /* Colorful disc for playing track - will be set dynamically */
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #00b4d8;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #00b4d8;
            }
            
            /* Vertical Scrollbar */
            QTableWidget QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background-color: #00b4d8;
                border-radius: 6px;
                min-height: 20px;
            }
            QTableWidget QScrollBar::handle:vertical:hover {
                background-color: #00b4d8;
            }
            QTableWidget QScrollBar::add-line:vertical, 
            QTableWidget QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QTableWidget QScrollBar::add-page:vertical, 
            QTableWidget QScrollBar::sub-page:vertical {
                background: none;
            }
            
            /* Horizontal Scrollbar */
            QTableWidget QScrollBar:horizontal {
                background-color: #1a1a1a;
                height: 12px;
                border-radius: 6px;
                margin: 0px;
            }
            QTableWidget QScrollBar::handle:horizontal {
                background-color: #00b4d8;
                border-radius: 6px;
                min-width: 20px;
            }
            QTableWidget QScrollBar::handle:horizontal:hover {
                background-color: #00b4d8;
            }
            QTableWidget QScrollBar::add-line:horizontal, 
            QTableWidget QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QTableWidget QScrollBar::add-page:horizontal, 
            QTableWidget QScrollBar::sub-page:horizontal {
                background: none;
            }
            
            /* Remove the buttons at the ends of scrollbars */
            QTableWidget QScrollBar::add-line:vertical, 
            QTableWidget QScrollBar::sub-line:vertical,
            QTableWidget QScrollBar::add-line:horizontal, 
            QTableWidget QScrollBar::sub-line:horizontal {
                border: none;
                background: none;
            }
        """)
        
        self.table.setAlternatingRowColors(True)
        playlist_layout.addWidget(self.table)
        
        # Control buttons (Load Folder and Clear)
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        
        self.btn_load_folder = QPushButton("📁 Load Folder")
        self.btn_load_folder.clicked.connect(self.load_folder)
        self.btn_load_folder.setStyleSheet("""
            QPushButton {
                
                border-radius: 4px;
                padding: 8px 60px;
                font-weight: bold;
            }

        """)
        
        self.btn_clear = QPushButton("🗑️ Clear")
        self.btn_clear.clicked.connect(self.clear_playlist)
        self.btn_clear.setStyleSheet("""
            QPushButton {
               
                border-radius: 4px;
                padding: 8px 60px;
                font-weight: bold;
            }
            
        """)
                
        control_layout.addWidget(self.btn_load_folder)
        control_layout.addWidget(self.btn_clear)
        control_layout.addStretch()
        
        playlist_layout.addLayout(control_layout)
        playlist_group.setLayout(playlist_layout)
        left_panel.addWidget(playlist_group)
        
        content_layout.addLayout(left_panel, 1)

        # ===== RIGHT PANEL =====
        right_panel = QVBoxLayout()
        right_panel.setSpacing(10)
        
        # Visualizer
        self.spectrum = Spectrum(self.audio)
        self.spectrum.setMinimumHeight(240)
        self.spectrum.setMaximumHeight(410)
        self.spectrum.setStyleSheet("background-color: #0d1117; border: 1px solid #30363d; border-radius: 8px;")
        right_panel.addWidget(self.spectrum)
        
        # Visualizer controls
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        
        mode_label = QLabel("Visual Mode:")
        mode_label.setStyleSheet("color: #c9d1d9; font-weight: bold;")
        
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["Bars", "Wave", "Circle", "Disk"])
        self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
        self.spectrum_mode.setFixedWidth(100)
        
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.spectrum_mode)
        mode_layout.addSpacing(20)
        
        effects_label = QLabel("FX:")
        effects_label.setStyleSheet("color: #c9d1d9; font-weight: bold;")
        
        self.effects_combo = QComboBox()
        self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
        self.effects_combo.currentTextChanged.connect(lambda e: setattr(self.audio, 'effect', e))
        self.effects_combo.setFixedWidth(80)
               
        mode_layout.addWidget(effects_label)
        mode_layout.addWidget(self.effects_combo)
        mode_layout.addStretch()
        
        volume_label = QLabel("Vol:")
        volume_label.setStyleSheet("color: #c9d1d9; font-weight: bold;")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(lambda v: setattr(self.audio, 'volume', v/100))
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                background-color: #30363d;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #1f6feb;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background-color: #1f6feb;
                border-radius: 3px;
            }
        """)
        
        mode_layout.addWidget(volume_label)
        mode_layout.addWidget(self.volume_slider)
        controls_layout.addLayout(mode_layout)
        right_panel.addLayout(controls_layout)
        
        right_panel.addSpacing(10)
        
        # Progress section
        progress_frame = QFrame()
        progress_frame.setFixedHeight(140)
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #161b22;
                border-radius: 8px;
                padding: 2px;

            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 8, 10, 8)
        progress_layout.setSpacing(8)
        
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QSlider::groove:horizontal {
                background-color: #30363d;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background-color: #1f6feb;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::sub-page:horizontal {
                background-color: #1f6feb;
                border-radius: 3px;
            }
        """)
        
        progress_layout.addWidget(self.progress_bar)
        
        time_container = QFrame()
        time_container.setFixedHeight(30)
        time_container.setStyleSheet("background: transparent;")
        time_layout = QHBoxLayout(time_container)
        time_layout.setContentsMargins(1, 2, 2, 2)
        
        self.current_time_label = QLabel("00:00")
        self.current_time_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #58a6ff;
                min-width: 55px;
            }
        """)
        self.current_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                color: #c9d1d9;
                min-width: 55px;
            }
        """)
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(QLabel(""))
        time_layout.addWidget(self.duration_label)
        
        progress_layout.addWidget(time_container)
        
        # Transport controls with icons
        transport_container = QFrame()
        transport_container.setFixedHeight(60)
        transport_container.setStyleSheet("background: transparent;")
        transport_layout = QHBoxLayout(transport_container)
        transport_layout.setContentsMargins(0, 5, 0, 5)
        transport_layout.setSpacing(15)
        
        # Check if icons exist, otherwise use text fallback
        icon_dir = "icons"
        if not os.path.exists(icon_dir):
            os.makedirs(icon_dir, exist_ok=True)
        
        # Shuffle button
        shuffle_icon_path = os.path.join(icon_dir, "shuffle.png")
        if os.path.exists(shuffle_icon_path):
            self.btn_shuffle = QPushButton(QIcon(shuffle_icon_path), "")
        else:
            self.btn_shuffle = QPushButton("🔀")
        
        self.btn_shuffle.setFixedSize(46, 46)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle_mode)
        self.btn_shuffle.setStyleSheet("""
            QPushButton {
                border-radius: 23px;
                background-color: #21262d;
                border: 1px solid #30363d;
                font-size: 17px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
        """)
        self.btn_shuffle.setIconSize(QSize(24, 24))
        
        # Previous button
        prev_icon_path = os.path.join(icon_dir, "prev.png")
        if os.path.exists(prev_icon_path):
            self.btn_prev = QPushButton(QIcon(prev_icon_path), "")
        else:
            self.btn_prev = QPushButton("⏮")
        
        self.btn_prev.setFixedSize(46, 46)
        self.btn_prev.clicked.connect(self.prev)
        self.btn_prev.setStyleSheet("""
            QPushButton {
                border-radius: 23px;
                background-color: #21262d;
                border: 1px solid #30363d;
                font-size: 17px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
        """)
        self.btn_prev.setIconSize(QSize(24, 24))
        
        # Play/Pause button
        play_icon_path = os.path.join(icon_dir, "play.png")
        pause_icon_path = os.path.join(icon_dir, "pause.png")
        
        if os.path.exists(play_icon_path):
            self.btn_play = QPushButton(QIcon(play_icon_path), "")
        else:
            self.btn_play = QPushButton("▶")
        
        self.btn_play.setFixedSize(46, 46)
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setStyleSheet("""
            QPushButton {
                border-radius: 23px;
                
                border: 1px solid #1f6feb;
                font-size: 17px;
                color: white;
            }
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
            }
            QPushButton:pressed {
                background-color: #1a64d1;
            }
        """)
        self.btn_play.setIconSize(QSize(24, 24))
        
        # Store icon paths for toggling
        self.play_icon_path = play_icon_path
        self.pause_icon_path = pause_icon_path
        
        # Next button
        next_icon_path = os.path.join(icon_dir, "next.png")
        if os.path.exists(next_icon_path):
            self.btn_next = QPushButton(QIcon(next_icon_path), "")
        else:
            self.btn_next = QPushButton("⏭")
        
        self.btn_next.setFixedSize(46, 46)
        self.btn_next.clicked.connect(self.next)
        self.btn_next.setStyleSheet("""
            QPushButton {
                border-radius: 23px;
                background-color: #21262d;
                border: 1px solid #30363d;
                font-size: 17px;
                color: #c9d1d9;
            }
            QPushButton:hover {
                background-color: #30363d;
                border: 1px solid #58a6ff;
            }
            QPushButton:pressed {
                background-color: #161b22;
            }
        """)
        self.btn_next.setIconSize(QSize(24, 24))
        
        self.update_shuffle_button_icon()
        
        transport_layout.addWidget(self.btn_shuffle)
        transport_layout.addStretch()
        
        transport_layout.addWidget(self.btn_prev)
        transport_layout.addWidget(self.btn_play)
        transport_layout.addWidget(self.btn_next)
        transport_layout.addStretch()
        
        progress_layout.addWidget(transport_container)
        
        self.progress_bar.sliderPressed.connect(self.start_seeking)
        self.progress_bar.sliderReleased.connect(self.end_seeking)
        self.progress_bar.sliderMoved.connect(self.update_seek_preview)
        
        right_panel.addWidget(progress_frame)
        
        content_layout.addLayout(right_panel, 2)
        main_layout.addLayout(content_layout)

    # ================= FILE MANAGEMENT =================
        
    def load_last_folder(self):
        """Load the last folder from database on startup"""
        last_folder = self.db.get_last_folder()
        if last_folder and os.path.exists(last_folder):
            # Check if folder still exists
            if os.path.isdir(last_folder):
                print(f"Loading last folder from database: {last_folder}")
                self.load_folder_from_db(last_folder)
            else:
                print(f"Last folder no longer exists: {last_folder}")
                # Optionally remove from database
                self.db.save_last_folder("")
        else:
            print("No last folder found in database")
            
    def load_folder_from_db(self, folder_path):
        """Load folder tracks from database (fast loading)"""
        print(f"Loading tracks from database for: {folder_path}")
        self.current_folder_path = folder_path
        self.clear_playlist()
        
        # Get tracks from database
        tracks = self.db.get_tracks_from_folder(folder_path)
        file_count = 0
        
        # Clear all file lists
        self.all_files = []
        self.all_durations = []
        self.files = []
        self.durations = []
        
        for track in tracks:
            file_path, file_name, duration, title, artist, album, genre = track
            
            # Add to all files list (for searching)
            self.all_files.append(file_path)
            self.all_durations.append(duration if duration else 0)
            
            # Add to current display list
            self.files.append(file_path)
            self.durations.append(duration if duration else 0)
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            # Use title if available, otherwise use filename
            display_name = title if title and title.strip() else os.path.splitext(file_name)[0]
            track_item = QTableWidgetItem(f"💿 {display_name}")
            track_item.setData(Qt.UserRole, file_path)
            self.table.setItem(r, 0, track_item)
            
            # Add artist and album columns if they exist in table
            if self.table.columnCount() > 2:
                artist_item = QTableWidgetItem(artist if artist else "Unknown Artist")
                self.table.setItem(r, 1, artist_item)
                
                album_item = QTableWidgetItem(album if album else "Unknown Album")
                self.table.setItem(r, 2, album_item)
            
            if duration and duration > 0:
                mins = int(duration // 60)
                secs = int(duration % 60)
                duration_text = f"{mins:02d}:{secs:02d}"
            else:
                duration_text = "--:--"
            
            # Set duration in appropriate column
            duration_col = 3 if self.table.columnCount() > 3 else 1
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, duration_col, duration_item)
            
            file_count += 1
        
        self.title_label.setText(f"🎧 {os.path.basename(folder_path)} - {file_count} tracks (from database)")
        print(f"Loaded {file_count} files from database for {folder_path}")
        
        # Add to recent folders
        self.db.add_recent_folder(folder_path)
        

    # def load_folder(self):
    #     """Load music folder"""
    #     folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
    #     if not folder:
    #         return
        
    #     self.current_folder_path = folder
    #     self.clear_playlist()
        
    #     audio_extensions = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma")
    #     file_count = 0
        
    #     # Clear all file lists
    #     self.all_files = []
    #     self.all_durations = []
    #     self.files = []
    #     self.durations = []
        
    #     for root, dirs, files in os.walk(folder):
    #         for f in files:
    #             if f.lower().endswith(audio_extensions):
    #                 file_path = os.path.join(root, f)
                    
    #                 # Add to all files list (for searching)
    #                 self.all_files.append(file_path)
                    
    #                 duration = 0
    #                 try:
    #                     duration = get_audio_duration(file_path)
    #                 except:
    #                     pass
                    
    #                 self.all_durations.append(duration)
                    
    #                 # Add to current display list
    #                 self.files.append(file_path)
    #                 self.durations.append(duration)
                    
    #                 r = self.table.rowCount()
    #                 self.table.insertRow(r)
                    
    #                 display_name = os.path.splitext(f)[0]
    #                 track_item = QTableWidgetItem(f"💿 {display_name}")
    #                 track_item.setData(Qt.UserRole, file_path)
    #                 self.table.setItem(r, 0, track_item)
                    
    #                 if duration > 0:
    #                     mins = int(duration // 60)
    #                     secs = int(duration % 60)
    #                     duration_text = f"{mins:02d}:{secs:02d}"
    #                 else:
    #                     duration_text = "--:--"
                    
    #                 duration_item = QTableWidgetItem(duration_text)
    #                 duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
    #                 self.table.setItem(r, 1, duration_item)
                    
    #                 file_count += 1
        
    #     self.title_label.setText(f"🎧 {os.path.basename(folder)} - {file_count} tracks")
    #     print(f"Loaded {file_count} files from {folder}")
    
    def load_folder(self):
        """Load music folder and scan for audio files"""
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return
        
        # Save to database as last folder
        self.db.save_last_folder(folder)
        
        # Check if folder needs rescan
        if self.db.folder_needs_rescan(folder):
            print(f"Folder {folder} needs rescan, scanning now...")
            self.scan_and_load_folder(folder)
        else:
            print(f"Loading folder {folder} from database...")
            self.load_folder_from_db(folder)
    
    def scan_and_load_folder(self, folder):
        """Scan folder for audio files and load them"""
        self.current_folder_path = folder
        self.clear_playlist()
        
        # Add folder to database
        folder_id = self.db.add_folder(folder)
        
        audio_extensions = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma")
        file_count = 0
        start_time = datetime.now()
        
        # Clear all file lists
        self.all_files = []
        self.all_durations = []
        self.files = []
        self.durations = []
        
        for root, dirs, files in os.walk(folder):
            for f in files:
                if f.lower().endswith(audio_extensions):
                    file_path = os.path.join(root, f)
                    
                    # Get file info
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        file_size = 0
                    
                    # Get duration
                    duration = 0
                    try:
                        duration = get_audio_duration(file_path)
                    except:
                        pass
                    
                    # Extract metadata
                    metadata = extract_metadata(file_path)
                    
                    # Add to database
                    if folder_id:
                        self.db.add_track(folder_id, file_path, f, file_size, duration, metadata)
                    
                    # Add to all files list (for searching)
                    self.all_files.append(file_path)
                    self.all_durations.append(duration)
                    
                    # Add to current display list
                    self.files.append(file_path)
                    self.durations.append(duration)
                    
                    r = self.table.rowCount()
                    self.table.insertRow(r)
                    
                    # Use metadata title if available, otherwise use filename
                    display_name = metadata.get('title', os.path.splitext(f)[0])
                    track_item = QTableWidgetItem(f"💿 {display_name}")
                    track_item.setData(Qt.UserRole, file_path)
                    self.table.setItem(r, 0, track_item)
                    
                    # Add artist and album columns if they exist in table
                    if self.table.columnCount() > 2:
                        artist_item = QTableWidgetItem(metadata.get('artist', 'Unknown Artist'))
                        self.table.setItem(r, 1, artist_item)
                        
                        album_item = QTableWidgetItem(metadata.get('album', 'Unknown Album'))
                        self.table.setItem(r, 2, album_item)
                    
                    if duration > 0:
                        mins = int(duration // 60)
                        secs = int(duration % 60)
                        duration_text = f"{mins:02d}:{secs:02d}"
                    else:
                        duration_text = "--:--"
                    
                    # Set duration in appropriate column
                    duration_col = 3 if self.table.columnCount() > 3 else 1
                    duration_item = QTableWidgetItem(duration_text)
                    duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(r, duration_col, duration_item)
                    
                    file_count += 1
        
        # Update folder scan time
        end_time = datetime.now()
        scan_duration = (end_time - start_time).total_seconds()
        self.db.update_folder_scan_time(folder, scan_duration)
        
        # Clean up any missing files from database
        self.db.cleanup_missing_files(folder)
        
        self.title_label.setText(f"🎧 {os.path.basename(folder)} - {file_count} tracks (scanned)")
        print(f"Scanned and loaded {file_count} files from {folder}")
        
        # Add to recent folders
        self.db.add_recent_folder(folder)
      
    def display_tracks(self, files, durations):
        """Display tracks in the table"""
        self.files = []
        self.durations = []
        self.table.setRowCount(0)
        
        for i, (file_path, duration) in enumerate(zip(files, durations)):
            self.files.append(file_path)
            self.durations.append(duration)
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            display_name = os.path.splitext(os.path.basename(file_path))[0]
            # Add disk emoji to track name
            track_item = QTableWidgetItem(f"💿 {display_name}")
            track_item.setData(Qt.UserRole, file_path)
            self.table.setItem(r, 0, track_item)
            
            if duration > 0:
                mins = int(duration // 60)
                secs = int(duration % 60)
                duration_text = f"{mins:02d}:{secs:02d}"
            else:
                duration_text = "--:--"
            
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 1, duration_item)    
    
    def filter_tracks(self):
        """Filter tracks based on search text"""
        search_text = self.search_box.text().strip().lower()
        
        if not search_text:
            # If search is empty, show all tracks
            self.display_tracks(self.all_files, self.all_durations)
            return
        
        # Filter files based on search text
        filtered_files = []
        filtered_durations = []
        
        for file_path, duration in zip(self.all_files, self.all_durations):
            filename = os.path.basename(file_path).lower()
            if search_text in filename:
                filtered_files.append(file_path)
                filtered_durations.append(duration)
        
        # Display filtered tracks
        self.display_tracks(filtered_files, filtered_durations)
    

    # def clear_playlist(self):
    #     """Clear playlist display"""
    #     self.files.clear()
    #     self.durations.clear()
    #     self.shuffled_indices.clear()
    #     self.original_indices.clear()
    #     self.current_shuffle_index = -1
    #     self.table.setRowCount(0)
    #     self.stop()
    def clear_playlist(self):
        """Clear playlist display"""
        # Clear all file lists
        if hasattr(self, 'files'):
            self.files.clear()
        if hasattr(self, 'durations'):
            self.durations.clear()
        if hasattr(self, 'all_files'):
            self.all_files.clear()
        if hasattr(self, 'all_durations'):
            self.all_durations.clear()
        
        self.shuffled_indices.clear()
        self.original_indices.clear()
        self.current_shuffle_index = -1
        self.table.setRowCount(0)
        self.stop()

    # ================= PLAYBACK CONTROLS =================
    
    def play_selected(self, row=None):
        """Play selected track and update database stats"""
        if row is None:
            row = self.table.currentRow()
        
        if 0 <= row < len(self.files):
            # Update current shuffle index if in shuffle mode
            if self.play_mode == "shuffle":
                # Find the position of this track in shuffled list
                if row in self.shuffled_indices:
                    self.current_shuffle_index = self.shuffled_indices.index(row)
                else:
                    # If track not in shuffled list (shouldn't happen), recreate list
                    self.create_shuffled_list()
            
            # Store current index
            self.current_file_index = row
            
            # Clear previous playing track highlight
            for i in range(self.table.rowCount()):
                # Clear playing flag from all items
                for col in range(4):  # Changed from 2 to 4 columns
                    item = self.table.item(i, col)
                    if item:
                        item.setData(Qt.UserRole + 1, None)  # Clear playing flag
                        
                # Reset track disc to gray for non-playing tracks
                track_item = self.table.item(i, 0)
                if track_item:
                    text = track_item.text()
                    # Remove any color emoji and set back to CD emoji
                    if "🔴" in text or "🟢" in text or "🔵" in text or "🟡" in text or "🟣" in text or "🟠" in text:
                        # Extract just the filename
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            track_item.setText(f"💿 {parts[1]}")
            
            file_path = self.files[row]
            
            if self.audio.load(file_path):
                # Update database play stats
                self.db.update_track_play_stats(file_path)
                
                self.title_label.setText(f"🎧 {os.path.basename(file_path)}")
                
                if not self.audio.isRunning():
                    self.audio.start()
                
                self.audio.running = True
                self.update_play_button_icon(playing=True)
                
                # Update duration display
                mins = int(self.audio.duration // 60)
                secs = int(self.audio.duration % 60)
                duration_text = f"{mins:02d}:{secs:02d}"
                
                # Update duration in table
                duration_item = self.table.item(row, 3)  # Changed from 1 to 3
                if duration_item:
                    duration_item.setText(duration_text)
                
                # Store the actual duration
                self.durations[row] = self.audio.duration
                
                # Update progress bar duration
                self.duration_label.setText(duration_text)
                
                # Reset progress
                self.progress_bar.setValue(0)
                
                # Highlight playing track with colorful disc
                track_item = self.table.item(row, 0)
                if track_item:
                    # Get current text (remove the 💿 if present)
                    current_text = track_item.text()
                    parts = current_text.split(" ", 1)
                    filename = parts[1] if len(parts) > 1 else current_text
                    
                    # Choose a color based on track index (rotating colors)
                    colors = ["🔴", "🟢", "🔵", "🟡", "🟣", "🟠"]  # Red, Green, Blue, Yellow, Purple, Orange
                    color_index = row % len(colors)
                    colorful_disc = colors[color_index]
                    
                    # Set colorful disc
                    track_item.setText(f"{colorful_disc} {filename}")
                    
                    # Set playing flag for styling
                    track_item.setData(Qt.UserRole + 1, "playing")
                
                # Also highlight other cells
                for col in range(1, 4):  # Highlight artist, album, duration columns
                    item = self.table.item(row, col)
                    if item:
                        item.setData(Qt.UserRole + 1, "playing")
                
                # Select the row for visual feedback
                self.table.selectRow(row)
                
                # Force style update
                self.table.viewport().update()

    def update_track_play_stats(self, file_path):
        """Update play count and last played time"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                UPDATE tracks 
                SET play_count = play_count + 1, last_played = CURRENT_TIMESTAMP
                WHERE file_path = ?
            ''', (file_path,))
            conn.commit()
        except Exception as e:
            print(f"Error updating play stats: {e}")
        finally:
            conn.close()


    def toggle_play(self):
        if self.audio.mono is None and self.files:
            self.play_selected(0)
        elif self.audio.mono is not None:
            if self.audio.running:
                self.audio.running = False
            else:
                self.audio.running = True
                
                if not self.audio.isRunning():
                    self.audio.start()
            
            self.update_play_button_icon(playing=self.audio.running)

    def update_play_button_icon(self, playing):
        """Update play button icon based on playback state"""
        if playing:
            # Show pause icon
            if hasattr(self, 'pause_icon_path') and os.path.exists(self.pause_icon_path):
                self.btn_play.setIcon(QIcon(self.pause_icon_path))
                self.btn_play.setText("")
                self.btn_play.setToolTip("Pause")
            else:
                # Fallback to text
                self.btn_play.setIcon(QIcon())
                self.btn_play.setText("⏸")
                self.btn_play.setToolTip("Pause")
        else:
            # Show play icon
            if hasattr(self, 'play_icon_path') and os.path.exists(self.play_icon_path):
                self.btn_play.setIcon(QIcon(self.play_icon_path))
                self.btn_play.setText("")
                self.btn_play.setToolTip("Play")
            else:
                # Fallback to text
                self.btn_play.setIcon(QIcon())
                self.btn_play.setText("▶")
                self.btn_play.setToolTip("Play")
        
        # Force button update
        self.btn_play.update()

    def stop(self):
        self.audio.running = False
        self.update_play_button_icon(playing=False)
        self.progress_bar.setValue(0)
        self.current_time_label.setText("00:00")

    def next(self):
        if not self.files:
            return
        
        if self.play_mode == "repeat_one":
            self.play_selected(self.current_file_index)
            return
        
        if self.play_mode == "shuffle":
            if len(self.files) == 1:
                next_index = 0
            else:
                available_indices = [i for i in range(len(self.files)) if i != self.current_file_index]
                next_index = random.choice(available_indices)
        else:
            next_index = (self.current_file_index + 1) % len(self.files)
        
        self.table.selectRow(next_index)
        self.play_selected(next_index)

    def prev(self):
        if not self.files:
            return
        
        if self.play_mode == "repeat_one":
            self.play_selected(self.current_file_index)
            return
        
        if self.play_mode == "shuffle":
            if len(self.files) == 1:
                prev_index = 0
            else:
                available_indices = [i for i in range(len(self.files)) if i != self.current_file_index]
                prev_index = random.choice(available_indices)
        else:
            prev_index = (self.current_file_index - 1) % len(self.files)
        
        self.table.selectRow(prev_index)
        self.play_selected(prev_index)

    def toggle_shuffle_mode(self):
        modes = ["sequential", "shuffle", "repeat_one"]
        current_index = modes.index(self.play_mode)
        next_index = (current_index + 1) % len(modes)
        self.play_mode = modes[next_index]
        self.update_shuffle_button_icon()

    def update_shuffle_button_icon(self):
        """Update shuffle button icon based on current mode"""
        icon_dir = "icons"
        
        if self.play_mode == "shuffle":
            shuffle_icon = os.path.join(icon_dir, "shuffle.png")
            if os.path.exists(shuffle_icon):
                self.btn_shuffle.setIcon(QIcon(shuffle_icon))
                self.btn_shuffle.setText("")
            else:
                self.btn_shuffle.setIcon(QIcon())
                self.btn_shuffle.setText("🔀")
            self.btn_shuffle.setToolTip("Shuffle: On")
            
        elif self.play_mode == "repeat_one":
            repeat_one_icon = os.path.join(icon_dir, "repeat_one.png")
            if os.path.exists(repeat_one_icon):
                self.btn_shuffle.setIcon(QIcon(repeat_one_icon))
                self.btn_shuffle.setText("")
            else:
                self.btn_shuffle.setIcon(QIcon())
                self.btn_shuffle.setText("🔂")
            self.btn_shuffle.setToolTip("Repeat: Current song")
            
        else:  # sequential
            repeat_icon = os.path.join(icon_dir, "repeat.png")
            if os.path.exists(repeat_icon):
                self.btn_shuffle.setIcon(QIcon(repeat_icon))
                self.btn_shuffle.setText("")
            else:
                self.btn_shuffle.setIcon(QIcon())
                self.btn_shuffle.setText("🔁")
            self.btn_shuffle.setToolTip("Play in order")

    # ================= PROGRESS BAR =================
    
    def update_progress_from_audio(self, position):
        if not self.user_is_seeking and self.audio.mono is not None and self.audio.duration > 0:
            value = int((position / self.audio.duration) * 10000)
            self.progress_bar.setValue(value)
            
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            if position >= self.audio.duration and not hasattr(self, '_track_completed'):
                self._track_completed = True
                
                if self.play_mode == "repeat_one":
                    self.play_selected(self.current_file_index)
                else:
                    QTimer.singleShot(100, self.next)
                
                QTimer.singleShot(2000, lambda: delattr(self, '_track_completed'))

    def start_seeking(self):
        self.user_is_seeking = True

    def update_seek_preview(self, value):
        if self.audio.mono is not None and self.audio.duration > 0:
            position = (value / 10000.0) * self.audio.duration
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")

    def end_seeking(self):
        if self.audio.mono is not None and self.audio.duration > 0:
            value = self.progress_bar.value()
            position = (value / 10000.0) * self.audio.duration
            
            self.audio.seek(position)
            
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            if not self.audio.running:
                self.audio.running = True
                self.update_play_button_icon(playing=True)
            
            self.user_is_seeking = False

    # ================= VISUALIZER =================
    
    def update_visualizer(self):
        self.spectrum.update()

    # ================= UI HELPERS =================
    
    def show_loading(self, filename):
        self.loading_label.setText(f"Loading: {filename}...")
        self.loading_label.setVisible(True)

    def hide_loading(self, filename):
        self.loading_label.setText("")
        self.loading_label.setVisible(False)

    # ================= MENU ACTIONS =================
    
    def show_most_played_dialog(self):
        QMessageBox.information(self, "Most Played", 
                              "Most Played feature would be implemented here.\n\nThis would show your most frequently played tracks.")

    def show_recently_played_dialog(self):
        QMessageBox.information(self, "Recently Played", 
                              "Recently Played feature would be implemented here.\n\nThis would show your recently played tracks.")

    # ================= CLEANUP =================
    
    def closeEvent(self, e):
        self.audio.stop()
        if self.audio.isRunning():
            self.audio.terminate()
            self.audio.wait()
        e.accept()


# ================= MAIN =================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    font = QFont("Segoe UI", 9)
    app.setFont(font)
    
    w = MusicPlayer()
    w.show()
    
    sys.exit(app.exec_())