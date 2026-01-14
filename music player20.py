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
    QFrame, QGroupBox, QGridLayout, QMessageBox, QMenuBar, QLineEdit
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
        # Get file extension
        ext = os.path.splitext(file_path)[1].lower()
        
        # Handle different file types
        if ext == '.mp3':
            # For MP3 files with ID3 tags
            try:
                # Try EasyID3 first (simpler interface)
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
                    # Fallback to ID3
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
            # For FLAC files
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
            # For OGG files
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
            # For MP4/M4A files
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
            # For WMA files
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
        
        # For WAV and other formats, try generic File
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
        
        # Get audio properties
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
    
    # Clean up the values
    for key in ['title', 'artist', 'album', 'genre']:
        if metadata[key] and isinstance(metadata[key], str):
            metadata[key] = metadata[key].strip()
            # Remove any null characters or other weird characters
            metadata[key] = metadata[key].replace('\x00', '').replace('\ufffd', '')
            if len(metadata[key]) > 200:  # Truncate very long values
                metadata[key] = metadata[key][:197] + "..."
    
    # If title is empty, use filename without extension
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
    
    # Fallback to librosa if mutagen fails
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
    position_changed = pyqtSignal(float)  # Emits current position in seconds
    loading_complete = pyqtSignal(str)    # Emits when loading is complete
    loading_started = pyqtSignal(str)     # Emits when loading starts
    
    def __init__(self):
        super().__init__()
        self.running = False
        self.effect = "Flat"
        self.volume = 0.8

        self.mono = None
        self.sr = 44100
        self.current_position = 0.0  # Current position in seconds
        self.angle = 0.0
        self.duration = 0.0
        self.force_seek = None  # Force seek to this position

        self.visual_samples = np.zeros(256, dtype=np.float32)

    def load(self, file):
        """Load audio file"""
        self.loading_started.emit(os.path.basename(file))
        
        try:
            # Load audio file
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
            # Clamp position to valid range
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
        
        # Handle force seek
        if self.force_seek is not None:
            self.current_position = self.force_seek
            self.force_seek = None
            print(f"Callback: Starting from {self.current_position:.2f}s")
        
        # Calculate starting sample
        start_sample = int(self.current_position * self.sr)
        
        # Check bounds
        if start_sample >= len(self.mono):
            outdata[:] = np.zeros((frames, 2), np.float32)
            self.running = False
            return
        
        # Check if we should output audio
        if not self.running:
            # When paused, output silence AND DO NOT ADVANCE TIME
            outdata[:] = np.zeros((frames, 2), np.float32)
            return
        
        # Process audio frames
        frames_processed = 0
        for i in range(frames):
            if start_sample + i >= len(self.mono):
                # End of track
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
        
        # Update current position only when playing
        self.current_position += frames_processed / self.sr
        
        # Emit position update only when playing
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
            # Keep the stream open even when paused
            while True:
                sd.sleep(50)  # Sleep a bit to prevent busy waiting
                # Check if we should exit
                if not hasattr(self, '_should_exit'):
                    self._should_exit = False
                if self._should_exit:
                    break
        
        print("AudioThread.run() ended")

    def stop(self):
        self.running = False
        self._should_exit = True  # Signal to exit the run loop


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
            # Save history positions for drawing trails
            if not hasattr(self, 'trail_history'):
                self.trail_history = []
            
            # Limit history length
            if len(self.trail_history) > 10:
                self.trail_history.pop(0)
            
            # Draw trails
            painter.setPen(Qt.NoPen)
            for trail_idx, trail in enumerate(self.trail_history):
                alpha = int(100 * (trail_idx + 1) / len(self.trail_history))
                painter.setBrush(QColor(0, 200, 255, alpha))
                for x, y in trail:
                    painter.drawEllipse(x - 2, y - 2, 4, 4)
            
            # Current frame particle positions
            current_frame = []
            self.phase += 0.04
            
            # Draw current particles
            painter.setPen(QPen(QColor(0, 200, 255, 180), 1))
            for i, v in enumerate(data):
                x = int((i / len(data)) * w)
                y = int(cy + math.sin(self.phase + i * 0.25) * v * 25)
                
                # Save position
                current_frame.append((x, y))
                
                # Particle color gradient
                hue = (i * 6 + int(self.phase * 50)) % 360  # Add phase to affect hue
                painter.setBrush(QColor.fromHsv(hue, 255, 255, 220))
                painter.drawEllipse(x - 3, y - 3, 6, 6)
                
                # Optional: connect adjacent particles
                if i > 0 and i % 5 == 0:  # Connect every 5th point
                    prev_x = int(((i-1) / len(data)) * w)
                    prev_y = int(cy + math.sin(self.phase + (i-1) * 0.25) * data[i-1] * 25)
                    painter.setPen(QPen(QColor(0, 200, 255, 80), 1))
                    painter.drawLine(prev_x, prev_y, x, y)
            
            # Save current frame to history
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
            # Calculate sizes
            max_radius = min(cx, cy) - 10
            disk_radius = max_radius * 0.5  # Disk takes 50% of available space
            max_bar_length = max_radius - disk_radius - 5  # Space for bars
            
            # Draw realistic CD disk with rainbow effect
            # Draw outer metallic ring
            outer_ring_radius = disk_radius * 0.95
            painter.setBrush(Qt.NoBrush)
            painter.setPen(QPen(QColor(180, 180, 200, 200), 3))
            painter.drawEllipse(int(cx - outer_ring_radius), int(cy - outer_ring_radius), 
                               int(outer_ring_radius * 2), int(outer_ring_radius * 2))
            
            # Draw CD rainbow effect (concentric rings with different colors)
            ring_colors = [
                QColor(255, 0, 0, 180),      # Red
                QColor(255, 127, 0, 180),    # Orange
                QColor(255, 255, 0, 180),    # Yellow
                QColor(0, 255, 0, 180),      # Green
                QColor(0, 0, 255, 180),      # Blue
                QColor(75, 0, 130, 180),     # Indigo
                QColor(148, 0, 211, 180)     # Violet
            ]
            
            for i, color in enumerate(ring_colors):
                ring_radius = disk_radius * (0.7 - (i * 0.08))
                if ring_radius > disk_radius * 0.2:  # Don't draw too small
                    painter.setBrush(Qt.NoBrush)
                    painter.setPen(QPen(color, 2))
                    painter.drawEllipse(int(cx - ring_radius), int(cy - ring_radius), 
                                       int(ring_radius * 2), int(ring_radius * 2))
            
            # Draw central blue disk area (like a CD's data area)
            data_area_radius = disk_radius * 0.65
            gradient = QLinearGradient(cx - data_area_radius, cy - data_area_radius, 
                                      cx + data_area_radius, cy + data_area_radius)
            gradient.setColorAt(0, QColor(0, 100, 200, 180))  # Dark blue
            gradient.setColorAt(0.5, QColor(0, 150, 255, 200))  # Medium blue
            gradient.setColorAt(1, QColor(0, 100, 200, 180))  # Dark blue
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(0, 180, 255, 220), 2))
            painter.drawEllipse(int(cx - data_area_radius), int(cy - data_area_radius), 
                               int(data_area_radius * 2), int(data_area_radius * 2))
            
            # Draw CD center hole with silver color
            center_hole_radius = disk_radius * 0.15
            center_gradient = QLinearGradient(cx - center_hole_radius, cy - center_hole_radius,
                                             cx + center_hole_radius, cy + center_hole_radius)
            center_gradient.setColorAt(0, QColor(220, 220, 220, 200))
            center_gradient.setColorAt(1, QColor(180, 180, 180, 200))
            
            painter.setBrush(QBrush(center_gradient))
            painter.setPen(QPen(QColor(200, 200, 200, 150), 2))
            painter.drawEllipse(int(cx - center_hole_radius), int(cy - center_hole_radius), 
                               int(center_hole_radius * 2), int(center_hole_radius * 2))
            
            # Draw small inner hole (like a CD spindle)
            spindle_radius = center_hole_radius * 0.4
            painter.setBrush(QBrush(QColor(100, 100, 120, 200)))
            painter.setPen(QPen(QColor(80, 80, 100, 150), 1))
            painter.drawEllipse(int(cx - spindle_radius), int(cy - spindle_radius), 
                               int(spindle_radius * 2), int(spindle_radius * 2))
            
            # Draw spectrum bars radiating from disk
            bar_count = len(data)
            bar_width = 6
            
            for i, v in enumerate(data):
                # Calculate angle for this bar (evenly spaced around the circle)
                angle = (i / bar_count) * 2 * math.pi
                
                # Calculate bar length based on frequency data
                bar_length = min(v * 80, max_bar_length)
                
                # Color based on frequency (same rainbow colors as Bars mode)
                color = QColor.fromHsv((i * 6) % 360, 255, 255)
                painter.setBrush(color)
                painter.setPen(Qt.NoPen)
                
                # Calculate start point (on disk edge)
                start_x = cx + math.cos(angle) * disk_radius
                start_y = cy + math.sin(angle) * disk_radius
                
                # Calculate end point (extending outward from disk)
                end_x = cx + math.cos(angle) * (disk_radius + bar_length)
                end_y = cy + math.sin(angle) * (disk_radius + bar_length)
                
                # Calculate perpendicular direction for bar width
                perp_angle = angle + math.pi / 2
                perp_dx = math.cos(perp_angle) * bar_width / 2
                perp_dy = math.sin(perp_angle) * bar_width / 2
                
                # Create bar polygon (rectangle aligned with angle)
                bar_polygon = QPolygonF([
                    QPointF(start_x - perp_dx, start_y - perp_dy),
                    QPointF(start_x + perp_dx, start_y + perp_dy),
                    QPointF(end_x + perp_dx, end_y + perp_dy),
                    QPointF(end_x - perp_dx, end_y - perp_dy)
                ])
                
                # Draw the bar
                painter.drawPolygon(bar_polygon)
                
                # Add a small glow effect at the tip of each bar
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
        self.setWindowTitle("🎧 Professional DJ Music Player with Database")
        self.resize(1200, 720)
        
        # Initialize database
        self.db = MusicDatabase()
        
        self.audio = AudioThread()
        self.files = []
        self.durations = []  # Store durations for each track
        self.current_file_index = -1
        self.user_is_seeking = False
        self.playing_color_index = 0  # For rotating colors
        
        # Add shuffle/repeat states
        self.play_mode = "sequential"  # sequential, shuffle, repeat_one
        self.shuffled_indices = []  # Stores shuffled order
        self.original_indices = []  # Stores original order
        self.is_shuffled = False  # Track if playlist is shuffled
        self.current_shuffle_index = -1  # Current position in shuffled list
        
        # Store current folder path
        self.current_folder_path = None
        
        # Store all tracks for filtering
        self.all_tracks = []  # Stores all tracks for current folder
        self.all_files = []   # Stores all file paths for current folder
        self.all_durations = []  # Stores all durations for current folder

        # Initialize UI
        self.init_ui()

        # Connect signals
        self.audio.position_changed.connect(self.update_progress_from_audio)
        self.audio.loading_started.connect(self.show_loading)
        self.audio.loading_complete.connect(self.hide_loading)

        # Timer for visualizer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_visualizer)
        self.timer.start(30)
        
        # Auto-load last folder on startup
        QTimer.singleShot(500, self.load_last_folder_on_startup)

    def init_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        main_layout = QVBoxLayout(root)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(8)

        # ===== MENU BAR =====
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('📁 File')
        
        load_folder_action = file_menu.addAction('Load Folder...')
        load_folder_action.triggered.connect(self.load_folder)
        load_folder_action.setShortcut('Ctrl+O')
        
        # Add Recent Folders submenu
        self.recent_folders_menu = file_menu.addMenu('Recent Folders')
        self.recent_folders_menu.aboutToShow.connect(self.update_recent_folders_menu)
        
        file_menu.addSeparator()
        
        reload_action = file_menu.addAction('🔄 Reload Current Folder')
        reload_action.triggered.connect(self.reload_current_folder)
        reload_action.setShortcut('F5')
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction('Exit')
        exit_action.triggered.connect(self.close)
        exit_action.setShortcut('Ctrl+Q')
        
        # Database menu
        db_menu = menubar.addMenu('💾 Database')
        
        rescan_action = db_menu.addAction('Force Rescan Current Folder')
        rescan_action.triggered.connect(self.force_rescan_current_folder)
        
        db_stats_action = db_menu.addAction('Database Statistics')
        db_stats_action.triggered.connect(self.show_database_stats)
        
        db_menu.addSeparator()
        
        search_action = db_menu.addAction('Search in Database...')
        search_action.triggered.connect(self.focus_search_box)
        search_action.setShortcut('Ctrl+F')
        
        recent_action = db_menu.addAction('Recently Played')
        recent_action.triggered.connect(self.load_recently_played)
        
        popular_action = db_menu.addAction('Most Played')
        popular_action.triggered.connect(self.load_most_played)
        
        db_menu.addSeparator()
        
        clear_db_action = db_menu.addAction('Clear Database')
        clear_db_action.triggered.connect(self.clear_database)

        # ===== TOP BAR =====
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        
        self.title_label = QLabel("🎧 No Track Playing")
        self.title_label.setFont(QFont("Segoe UI", 13, QFont.Bold))
        self.title_label.setStyleSheet("""
            QLabel {
                color: #00b4d8; 
                background-color: #0a0a0a;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 6px 10px;
                font-weight: bold;
            }
        """)
        self.title_label.setMinimumHeight(40)
        
        self.loading_label = QLabel("")
        self.loading_label.setVisible(False)
        self.loading_label.setStyleSheet("color: #ff9900; font-style: italic;")
        
        # Add database status label
        self.db_status_label = QLabel("DB: Ready")
        self.db_status_label.setStyleSheet("color: #00ff88; font-size: 10px;")
        
        top_bar.addWidget(self.title_label)
        top_bar.addWidget(self.loading_label)
        top_bar.addStretch()
        top_bar.addWidget(self.db_status_label)
        
        main_layout.addLayout(top_bar)

        # ===== MAIN CONTENT =====
        content_layout = QHBoxLayout()
        content_layout.setSpacing(12)

        # ===== LEFT PANEL - Playlist with Database Controls =====
        left_panel = QVBoxLayout()
        left_panel.setSpacing(6)
        
        # Database controls group
        db_group = QGroupBox("Database")
        db_layout = QGridLayout()
        
        self.btn_load_folder = QPushButton("📁 Load/Scan Folder")
        self.btn_load_folder.clicked.connect(self.load_folder)
        self.btn_load_folder.setToolTip("Load folder from database (fast) or scan if needed")
        
        self.btn_force_rescan = QPushButton("🔄 Force Rescan")
        self.btn_force_rescan.clicked.connect(self.force_rescan_current_folder)
        self.btn_force_rescan.setToolTip("Force rescan of current folder (ignore database)")
        
        self.btn_db_stats = QPushButton("📊 Database Stats")
        self.btn_db_stats.clicked.connect(self.show_database_stats)
        
        self.btn_clear_db = QPushButton("🗑️ Clear DB")
        self.btn_clear_db.clicked.connect(self.clear_database)
        self.btn_clear_db.setStyleSheet("background-color: #6a1b1b;")
        
        db_layout.addWidget(self.btn_load_folder, 0, 0)
        db_layout.addWidget(self.btn_force_rescan, 0, 1)
        db_layout.addWidget(self.btn_db_stats, 1, 0)
        db_layout.addWidget(self.btn_clear_db, 1, 1)
        
        db_group.setLayout(db_layout)
        left_panel.addWidget(db_group)
        
        # Playlist group
        playlist_group = QGroupBox("Playlist")
        playlist_layout = QVBoxLayout()
        
        # Search box - REMOVED search button, using QLineEdit instead
        search_layout = QHBoxLayout()
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Type to search...")
        self.search_box.textChanged.connect(self.filter_playlist)  # Real-time filtering
        
        # Add clear button inside the search box
        clear_search_btn = QPushButton("✕")
        clear_search_btn.setFixedSize(20, 20)
        clear_search_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 10px;
                color: #888;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        clear_search_btn.clicked.connect(self.clear_search)
        clear_search_btn.setToolTip("Clear search")
        
        # Create a container for the search box with clear button
        search_container = QWidget()
        search_container_layout = QHBoxLayout(search_container)
        search_container_layout.setContentsMargins(5, 0, 5, 0)
        search_container_layout.setSpacing(0)
        search_container_layout.addWidget(self.search_box)
        search_container_layout.addWidget(clear_search_btn)
        
        search_layout.addWidget(search_container)
        playlist_layout.addLayout(search_layout)
        
        # Quick filters
        filter_layout = QHBoxLayout()
        self.btn_recent = QPushButton("Recently Played")
        self.btn_recent.clicked.connect(self.load_recently_played)
        
        self.btn_popular = QPushButton("Most Played")
        self.btn_popular.clicked.connect(self.load_most_played)
        
        filter_layout.addWidget(self.btn_recent)
        filter_layout.addWidget(self.btn_popular)
        playlist_layout.addLayout(filter_layout)
        
        # Table with additional columns
        self.table = QTableWidget(0, 4)  # Added columns for Artist and Album
        self.table.setHorizontalHeaderLabels(["💿 Track", "Duration", "Artist", "Album"])
        self.table.verticalHeader().setVisible(False)
        self.table.setShowGrid(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setColumnWidth(0, 180)  # Track
        self.table.setColumnWidth(1, 120)  # Duration
        self.table.setColumnWidth(2, 120)  # Artist
        self.table.setColumnWidth(3, 60)   # Album
        
        self.table.cellDoubleClicked.connect(self.play_selected)
        
        # Set table styles
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
            QTableWidget::item[playing="true"] {
                background-color: #404040;
                color: white;
                font-weight: bold;
            }
            QHeaderView::section {
                background-color: #2d2d2d;
                color: #00b4d8;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #00b4d8;
            }
            QTableWidget QScrollBar:vertical {
                background-color: #1a1a1a;
                width: 12px;
            }
            QTableWidget QScrollBar::handle:vertical {
                background-color: #444;
                border-radius: 6px;
                min-height: 20px;
            }
            QTableWidget QScrollBar::handle:vertical:hover {
                background-color: #555;
            }
        """)
        
        self.table.setAlternatingRowColors(True)
        playlist_layout.addWidget(self.table)
        
        # Clear playlist button
        self.btn_clear_playlist = QPushButton("🗑️ Clear Playlist")
        self.btn_clear_playlist.clicked.connect(self.clear_playlist)
        playlist_layout.addWidget(self.btn_clear_playlist)
        
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
        right_panel.addWidget(self.spectrum)
        
        # Visualizer controls (same as before)
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        mode_layout = QHBoxLayout()
        mode_layout.setSpacing(8)
        mode_label = QLabel("Visual Mode:")
        mode_label.setStyleSheet("font-weight: bold;")
        self.spectrum_mode = QComboBox()
        self.spectrum_mode.addItems(["Bars", "Wave", "Circle", "Disk"])
        self.spectrum_mode.currentTextChanged.connect(self.spectrum.set_mode)
        self.spectrum_mode.setFixedWidth(150)
        
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.spectrum_mode)
        mode_layout.addSpacing(20)
        
        effects_label = QLabel("FX:")
        effects_label.setStyleSheet("font-weight: bold;")
        self.effects_combo = QComboBox()
        self.effects_combo.addItems(["Flat", "Rock", "3D", "8D", "Dolby"])
        self.effects_combo.currentTextChanged.connect(lambda e: setattr(self.audio, 'effect', e))
        self.effects_combo.setFixedWidth(90)
        
        mode_layout.addWidget(effects_label)
        mode_layout.addWidget(self.effects_combo)
        mode_layout.addStretch()
        
        volume_label = QLabel("Vol:")
        volume_label.setStyleSheet("font-weight: bold;")
        
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(80)
        self.volume_slider.valueChanged.connect(lambda v: setattr(self.audio, 'volume', v/100))
        self.volume_slider.setFixedWidth(100)
        
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
                background-color: #1a1a1a;
                border-radius: 6px;
                padding: 2px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(10, 8, 10, 8)
        progress_layout.setSpacing(8)
        
        self.progress_bar = QSlider(Qt.Horizontal)
        self.progress_bar.setRange(0, 10000)
        self.progress_bar.setValue(0)
        
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
                color: #00b4d8;
                min-width: 55px;
            }
        """)
        self.current_time_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        
        self.duration_label = QLabel("00:00")
        self.duration_label.setStyleSheet("""
            QLabel {
                font-weight: bold;
                font-size: 14px;
                min-width: 55px;
            }
        """)
        self.duration_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        time_layout.addWidget(self.current_time_label)
        time_layout.addStretch()
        time_layout.addWidget(QLabel(""))
        time_layout.addWidget(self.duration_label)
        
        progress_layout.addWidget(time_container)
        
        # Transport controls
        transport_container = QFrame()
        transport_container.setFixedHeight(60)
        transport_container.setStyleSheet("background: transparent;")
        transport_layout = QHBoxLayout(transport_container)
        transport_layout.setContentsMargins(0, 5, 0, 5)
        transport_layout.setSpacing(15)
        
        self.btn_shuffle = QPushButton()
        self.btn_shuffle.setFixedSize(46, 46)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle_mode)
        self.update_shuffle_button_icon()
        
        self.btn_prev = QPushButton()
        self.btn_prev.setFixedSize(46, 46)
        self.btn_prev.clicked.connect(self.prev)
        
        self.btn_play = QPushButton()
        self.btn_play.setFixedSize(46, 46)
        self.btn_play.clicked.connect(self.toggle_play)
        
        self.btn_next = QPushButton()
        self.btn_next.setFixedSize(46, 46)
        self.btn_next.clicked.connect(self.next)
        
        # Set icons for transport buttons
        self.update_transport_buttons()
        
        transport_layout.addWidget(self.btn_shuffle)
        transport_layout.addStretch()
        transport_layout.addWidget(self.btn_prev)
        transport_layout.addWidget(self.btn_play)
        transport_layout.addWidget(self.btn_next)
        transport_layout.addStretch()
        
        progress_layout.addWidget(transport_container)
        
        # Connect progress bar signals
        self.progress_bar.sliderPressed.connect(self.start_seeking)
        self.progress_bar.sliderReleased.connect(self.end_seeking)
        self.progress_bar.sliderMoved.connect(self.update_seek_preview)
        
        right_panel.addWidget(progress_frame)
        
        content_layout.addLayout(right_panel, 2)
        main_layout.addLayout(content_layout)

    # ================= SEARCH/FILTERING FUNCTIONS =================
    
    # ================= SEARCH/FILTERING FUNCTIONS =================

    def filter_playlist(self, search_text):
        """Filter the playlist in real-time as user types"""
        search_text = search_text.strip().lower()
        
        if not search_text:
            # If search is empty, show all tracks
            self.restore_full_playlist()
            return
        
        # Clear current display (but don't clear self.all_tracks!)
        self.files.clear()
        self.durations.clear()
        self.table.setRowCount(0)
        
        # Filter tracks from self.all_tracks
        filtered_count = 0
        for track_data in self.all_tracks:
            # Unpack track data based on format
            if len(track_data) >= 7:  # From database: (file_path, file_name, duration, title, artist, album, genre)
                file_path, file_name, duration, title, artist, album, genre = track_data[:7]
            elif len(track_data) == 6:  # From database search: (file_path, file_name, artist, title, album, duration)
                file_path, file_name, artist, title, album, duration = track_data
                genre = ""
            elif len(track_data) == 3:  # Simple format: (file_path, file_name, duration)
                file_path, file_name, duration = track_data
                title = file_name
                artist = "Unknown Artist"
                album = "Unknown Album"
                genre = ""
            else:
                continue  # Skip if format is unexpected
            
            # Check if file exists
            if not os.path.exists(file_path):
                continue
            
            # Check if search text matches track title (simplified as requested)
            search_match = search_text in title.lower()
            
            if search_match:
                # Add to current display
                self.files.append(file_path)
                self.durations.append(duration)
                
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # Column 0: Track name
                filename_no_ext = os.path.splitext(file_name)[0]
                if title and title != file_name and title != filename_no_ext:
                    display_title = title
                else:
                    display_title = filename_no_ext
                
                track_item = QTableWidgetItem(f"💿 {display_title}")
                track_item.setData(Qt.UserRole, file_path)
                self.table.setItem(r, 0, track_item)
                
                # Column 1: Duration
                if duration > 0:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_text = f"{mins:02d}:{secs:02d}"
                else:
                    duration_text = "--:--"
                
                duration_item = QTableWidgetItem(duration_text)
                duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 1, duration_item)
                
                # Column 2: Artist
                artist_item = QTableWidgetItem(artist if artist else "Unknown Artist")
                self.table.setItem(r, 2, artist_item)
                
                # Column 3: Album
                album_item = QTableWidgetItem(album if album else "Unknown Album")
                self.table.setItem(r, 3, album_item)
                
                filtered_count += 1
        
        # Update status
        if filtered_count > 0:
            self.db_status_label.setText(f"DB: {filtered_count} tracks match '{search_text}'")
        else:
            self.db_status_label.setText(f"DB: No tracks match '{search_text}'")

    def restore_full_playlist(self):
        """Restore full playlist when search is cleared"""
        if not self.all_tracks:
            print("Warning: No tracks in all_tracks to restore")
            return
        
        print(f"Restoring full playlist with {len(self.all_tracks)} tracks")
        
        # Clear current display
        self.files.clear()
        self.durations.clear()
        self.table.setRowCount(0)
        
        # Restore all tracks from self.all_tracks
        track_count = 0
        for track_data in self.all_tracks:
            # Unpack track data based on format
            if len(track_data) >= 7:  # From database: (file_path, file_name, duration, title, artist, album, genre)
                file_path, file_name, duration, title, artist, album, genre = track_data[:7]
            elif len(track_data) == 6:  # From database search: (file_path, file_name, artist, title, album, duration)
                file_path, file_name, artist, title, album, duration = track_data
                genre = ""
            elif len(track_data) == 3:  # Simple format: (file_path, file_name, duration)
                file_path, file_name, duration = track_data
                title = file_name
                artist = "Unknown Artist"
                album = "Unknown Album"
                genre = ""
            else:
                print(f"Warning: Unexpected track_data format with {len(track_data)} elements")
                continue
            
            # Check if file exists
            if not os.path.exists(file_path):
                print(f"Warning: File not found: {file_path}")
                continue
            
            # Add to current display
            self.files.append(file_path)
            self.durations.append(duration)
            
            r = self.table.rowCount()
            self.table.insertRow(r)
            
            # Column 0: Track name
            filename_no_ext = os.path.splitext(file_name)[0]
            if title and title != file_name and title != filename_no_ext:
                display_title = title
            else:
                display_title = filename_no_ext
            
            track_item = QTableWidgetItem(f"💿 {display_title}")
            track_item.setData(Qt.UserRole, file_path)
            self.table.setItem(r, 0, track_item)
            
            # Column 1: Duration
            if duration > 0:
                mins = int(duration // 60)
                secs = int(duration % 60)
                duration_text = f"{mins:02d}:{secs:02d}"
            else:
                duration_text = "--:--"
            
            duration_item = QTableWidgetItem(duration_text)
            duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(r, 1, duration_item)
            
            # Column 2: Artist
            artist_item = QTableWidgetItem(artist if artist else "Unknown Artist")
            self.table.setItem(r, 2, artist_item)
            
            # Column 3: Album
            album_item = QTableWidgetItem(album if album else "Unknown Album")
            self.table.setItem(r, 3, album_item)
            
            track_count += 1
        
        # Update status
        self.db_status_label.setText(f"DB: {track_count} tracks")
        print(f"Restored {track_count} tracks")
        
    def clear_search(self):
        """Clear the search box"""
        self.search_box.clear()
        self.focus_search_box()
    
    # ================= NEW METHODS FOR AUTO-LOADING =================
    
    def load_last_folder_on_startup(self):
        """Load the last folder on program startup"""
        last_folder = self.db.get_last_folder()
        if last_folder and os.path.exists(last_folder):
            # Ask user if they want to reload the last folder
            reply = QMessageBox.question(
                self, 'Load Last Folder',
                f'Do you want to reload the last folder?\n\n{last_folder}',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.load_folder_from_path(last_folder)
    
    def load_folder_from_path(self, folder_path):
        """Load a folder from a given path (used for recent folders)"""
        if not os.path.exists(folder_path):
            QMessageBox.warning(self, "Folder Not Found", 
                              f"The folder does not exist:\n{folder_path}")
            return
        
        # Update database status
        self.db_status_label.setText("DB: Checking...")
        
        # Check if folder needs rescan
        if not self.db.folder_needs_rescan(folder_path):
            # Load from database (FAST)
            self.load_from_database(folder_path)
        else:
            # Rescan folder
            self.scan_folder_to_database(folder_path)
    
    def reload_current_folder(self):
        """Reload the current folder from database"""
        if not self.current_folder_path:
            QMessageBox.information(self, "No Folder", "No folder is currently loaded.")
            return
        
        self.load_from_database(self.current_folder_path)
    
    def update_recent_folders_menu(self):
        """Update the recent folders menu with latest folders"""
        self.recent_folders_menu.clear()
        
        recent_folders = self.db.get_recent_folders()
        
        if not recent_folders:
            no_items_action = self.recent_folders_menu.addAction("No recent folders")
            no_items_action.setEnabled(False)
            return
        
        for folder_path, last_accessed in recent_folders:
            if os.path.exists(folder_path):
                # Format the display text
                folder_name = os.path.basename(folder_path)
                if folder_name == "":
                    folder_name = folder_path
                
                # Truncate if too long
                if len(folder_name) > 50:
                    folder_name = folder_name[:47] + "..."
                
                action = self.recent_folders_menu.addAction(f"📁 {folder_name}")
                action.setToolTip(folder_path)
                
                # Use lambda with default argument to capture folder_path
                action.triggered.connect(
                    lambda checked, path=folder_path: self.load_folder_from_path(path)
                )
    
    def focus_search_box(self):
        """Set focus to the search box"""
        self.search_box.setFocus()
        self.search_box.selectAll()

    # ================= MODIFIED EXISTING METHODS =================
    
    def load_folder(self):
        """Load music folder - use database if available, otherwise scan"""
        folder = QFileDialog.getExistingDirectory(self, "Select Music Folder")
        if not folder:
            return
        
        self.load_folder_from_path(folder)
    
    def load_from_database(self, folder_path):
        """Load tracks from database (very fast) - FIXED"""
        print(f"Loading from database: {folder_path}")
        self.db_status_label.setText("DB: Loading...")
        
        # Store current folder
        self.current_folder_path = folder_path
        
        # Save to recent folders and last folder
        self.db.add_recent_folder(folder_path)
        self.db.save_last_folder(folder_path)
        
        # Clean up any missing files first
        self.db.cleanup_missing_files(folder_path)
        
        # Get tracks from database
        tracks = self.db.get_tracks_from_folder(folder_path)
        
        # Store all tracks for filtering - IMPORTANT: Make a copy
        self.all_tracks = list(tracks)  # This makes a copy of the list
        
        print(f"Stored {len(self.all_tracks)} tracks in all_tracks")
        
        # Clear current playlist display (but keep all_tracks!)
        self.files.clear()
        self.durations.clear()
        self.table.setRowCount(0)
        
        # Clear search box
        self.search_box.clear()
        
        # Update window title with folder name
        folder_name = os.path.basename(folder_path)
        if folder_name == "":
            folder_name = folder_path
        self.setWindowTitle(f"🎧 Professional DJ Music Player - {folder_name}")
        
        # Set table headers
        self.table.setHorizontalHeaderLabels(["💿 Track", "Duration", "Artist", "Album"])
        
        # Update column widths
        self.table.setColumnWidth(0, 250)   # Track (wider for names)
        self.table.setColumnWidth(1, 70)    # Duration
        self.table.setColumnWidth(2, 150)   # Artist
        self.table.setColumnWidth(3, 150)   # Album
        
        # Add tracks to playlist display
        track_count = 0
        for file_path, file_name, duration, title, artist, album, genre in tracks:
            if os.path.exists(file_path):
                self.files.append(file_path)
                self.durations.append(duration)
                
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # Column 0: Track name
                filename_no_ext = os.path.splitext(file_name)[0]
                if title and title != file_name:
                    display_title = title
                else:
                    display_title = filename_no_ext
                
                track_item = QTableWidgetItem(f"💿 {display_title}")
                track_item.setData(Qt.UserRole, file_path)
                self.table.setItem(r, 0, track_item)
                
                # Column 1: Duration
                if duration > 0:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_text = f"{mins:02d}:{secs:02d}"
                else:
                    duration_text = "--:--"
                
                duration_item = QTableWidgetItem(duration_text)
                duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 1, duration_item)
                
                # Column 2: Artist
                artist_item = QTableWidgetItem(artist if artist else "Unknown Artist")
                self.table.setItem(r, 2, artist_item)
                
                # Column 3: Album
                album_item = QTableWidgetItem(album if album else "Unknown Album")
                self.table.setItem(r, 3, album_item)
                
                track_count += 1
            else:
                print(f"Warning: File not found: {file_path}")
        
        self.db_status_label.setText(f"DB: Loaded {track_count} tracks")
        print(f"Loaded {track_count} tracks from database")
        
        # Update status in title bar
        QTimer.singleShot(1000, lambda: self.db_status_label.setText(f"DB: {track_count} tracks loaded"))
    
    def scan_folder_to_database(self, folder_path):
        """Scan folder and save to database (slow first time) - MODIFIED"""
        print(f"Scanning folder: {folder_path}")
        self.db_status_label.setText("DB: Scanning...")
        
        # Store current folder
        self.current_folder_path = folder_path
        
        # Save to recent folders and last folder
        self.db.add_recent_folder(folder_path)
        self.db.save_last_folder(folder_path)
        
        # Clear current playlist
        self.clear_playlist()
        
        # Clear search box
        self.search_box.clear()
        
        # Update window title with folder name
        folder_name = os.path.basename(folder_path)
        if folder_name == "":
            folder_name = folder_path
        self.setWindowTitle(f"🎧 Professional DJ Music Player - Scanning: {folder_name}")
        
        # Add folder to database
        folder_id = self.db.add_folder(folder_path)
        if not folder_id:
            self.db_status_label.setText("DB: Error adding folder")
            return
        
        # Scan all music files
        audio_extensions = (".mp3", ".wav", ".flac", ".ogg", ".m4a", ".aac", ".wma")
        file_count = 0
        start_time = datetime.now()
        
        # Create a progress dialog - make it non-modal
        progress = QMessageBox(self)
        progress.setWindowTitle("Scanning Folder")
        progress.setText(f"Scanning: {folder_path}\n\nPlease wait...")
        progress.setStandardButtons(QMessageBox.NoButton)
        progress.setModal(False)  # Make it non-modal so it doesn't block
        progress.show()
        QApplication.processEvents()
        
        # Temporary storage for tracks
        temp_tracks = []
        
        # Recursive scan
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                if f.lower().endswith(audio_extensions):
                    file_path = os.path.join(root, f)
                    file_count += 1
                    
                    # Update status periodically
                    if file_count % 10 == 0:
                        self.db_status_label.setText(f"DB: Scanning... {file_count} files")
                        progress.setText(f"Scanning: {folder_path}\n\nFound {file_count} audio files...")
                        QApplication.processEvents()
                    
                    # Get file info
                    try:
                        file_size = os.path.getsize(file_path)
                    except:
                        file_size = 0
                    
                    # Get duration (with multiple fallbacks)
                    duration = 0
                    metadata = {}
                    
                    try:
                        # Try to get duration
                        duration = get_audio_duration(file_path)
                        
                        # Try to extract metadata
                        metadata = extract_metadata(file_path)
                            
                    except Exception as e:
                        print(f"Error getting duration for {f}: {e}")
                    
                    # Get filename without extension for title fallback
                    filename_no_ext = os.path.splitext(f)[0]
                    if metadata.get('title', '') == '':
                        metadata['title'] = filename_no_ext
                    
                    # Add to database
                    track_id = self.db.add_track(
                        folder_id, file_path, f, file_size, duration, metadata
                    )
                    
                    # Store in temp tracks for filtering
                    temp_tracks.append((
                        file_path,  # file_path
                        f,          # file_name
                        duration,   # duration
                        metadata.get('title', filename_no_ext),  # title
                        metadata.get('artist', 'Unknown Artist'),  # artist
                        metadata.get('album', 'Unknown Album'),   # album
                        metadata.get('genre', 'Unknown')    # genre
                    ))
                    
                    # Add to playlist immediately
                    self.files.append(file_path)
                    self.durations.append(duration)
                    
                    r = self.table.rowCount()
                    self.table.insertRow(r)
                    
                    # Use title from metadata if available, otherwise filename
                    display_title = metadata.get('title', '')
                    if not display_title or display_title == f:
                        display_title = filename_no_ext
                    track_item = QTableWidgetItem(f"💿 {display_title}")
                    track_item.setData(Qt.UserRole, file_path)
                    self.table.setItem(r, 0, track_item)
                    
                    # Artist from metadata
                    artist_item = QTableWidgetItem(metadata.get('artist', 'Unknown Artist'))
                    self.table.setItem(r, 1, artist_item)
                    
                    # Album from metadata
                    album_item = QTableWidgetItem(metadata.get('album', 'Unknown Album'))
                    self.table.setItem(r, 2, album_item)
                    
                    # Duration
                    if duration > 0:
                        mins = int(duration // 60)
                        secs = int(duration % 60)
                        duration_text = f"{mins:02d}:{secs:02d}"
                    else:
                        duration_text = "--:--"
                    
                    duration_item = QTableWidgetItem(duration_text)
                    duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.table.setItem(r, 3, duration_item)
        
        # Store all tracks for filtering
        self.all_tracks = temp_tracks
        
        # Update folder scan time
        scan_duration = (datetime.now() - start_time).total_seconds()
        self.db.update_folder_scan_time(folder_path, scan_duration)
        
        # Update window title
        self.setWindowTitle(f"🎧 Professional DJ Music Player - {folder_name}")
        
        self.db_status_label.setText(f"DB: Scanned {file_count} files in {scan_duration:.1f}s")
        print(f"Scanned {file_count} files in {scan_duration:.1f} seconds")
        
        # IMPORTANT: Close the progress dialog BEFORE showing the completion message
        progress.close()
        progress.deleteLater()  # Ensure it's properly cleaned up
        
        # Process events to ensure dialog closes
        QApplication.processEvents()
        
        # Show completion message - this will be a new modal dialog
        if file_count > 0:
            QMessageBox.information(self, "Scan Complete", 
                                  f"Scanned {file_count} audio files in {scan_duration:.1f} seconds.\n\n"
                                  f"Next time, this folder will load instantly from the database.")
    # ================= MODIFIED EXISTING METHODS =================
    
    def search_in_database(self):
        """Search tracks in database - Now just focuses the search box"""
        self.focus_search_box()

    # ================= EXISTING METHODS (unchanged) =================
    
    def update_transport_buttons(self):
        """Set icons for transport buttons"""
        # Set button styles
        button_style = """
            QPushButton {
                border-radius: 23px;
                background-color: #222;
                border: 1px solid #444;
                font-size: 17px;
            }
            QPushButton:hover {
                background-color: #333;
                border: 1px solid #00b4d8;
            }
            QPushButton:pressed {
                background-color: #111;
            }
        """
        
        self.btn_prev.setStyleSheet(button_style)
        self.btn_play.setStyleSheet(button_style)
        self.btn_next.setStyleSheet(button_style)
        
        # Set text fallbacks
        self.btn_prev.setText("⏮")
        self.btn_play.setText("▶")
        self.btn_next.setText("⏭")
        
        # Try to load icons from files
        icons = {
            "prev": "icons/prev.png",
            "play": "icons/play.png",
            "pause": "icons/pause.png",
            "next": "icons/next.png"
        }
        
        for btn, icon_path in [("prev", icons["prev"]), ("next", icons["next"])]:
            if os.path.exists(icon_path):
                if btn == "prev":
                    self.btn_prev.setIcon(QIcon(icon_path))
                    self.btn_prev.setIconSize(QSize(24, 24))
                    self.btn_prev.setText("")
                else:
                    self.btn_next.setIcon(QIcon(icon_path))
                    self.btn_next.setIconSize(QSize(24, 24))
                    self.btn_next.setText("")
        
        # Store pause icon path for play button
        self.btn_play.pause_icon_path = icons["pause"]
        if os.path.exists(icons["play"]):
            self.btn_play.icon_path = icons["play"]

    def update_shuffle_button_icon(self):
        """Update shuffle button icon based on current mode"""
        # Clear any custom paint event
        self.btn_shuffle.paintEvent = None
        
        icon_size = QSize(24, 24)
        
        if self.play_mode == "shuffle":
            # Try to load shuffle icon
            icon_path = "icons/shuffle.png"  # Your shuffle icon
            if os.path.exists(icon_path):
                self.btn_shuffle.setIcon(QIcon(icon_path))
                self.btn_shuffle.setIconSize(icon_size)
                self.btn_shuffle.setText("")
                self.btn_shuffle.setToolTip("Shuffle: On (Random play)")
            else:
                # Fallback: use text
                self.btn_shuffle.setIcon(QIcon())
                self.btn_shuffle.setText("🔀")
                self.btn_shuffle.setToolTip("Shuffle: On (Random play)")
                
        elif self.play_mode == "repeat_one":
            # Try to load repeat_one icon
            icon_path = "icons/repeat_one.png"  # Your single repeat icon
            if os.path.exists(icon_path):
                self.btn_shuffle.setIcon(QIcon(icon_path))
                self.btn_shuffle.setIconSize(icon_size)
                self.btn_shuffle.setText("")
                self.btn_shuffle.setToolTip("Repeat: Current song")
            else:
                # Fallback: use text
                self.btn_shuffle.setIcon(QIcon())
                self.btn_shuffle.setText("🔂")
                self.btn_shuffle.setToolTip("Repeat: Current song")
                
        else:  # sequential
            # Try to load sequential/repeat icon
            icon_path = "icons/repeat.png"  # Your sequential/repeat icon
            if os.path.exists(icon_path):
                self.btn_shuffle.setIcon(QIcon(icon_path))
                self.btn_shuffle.setIconSize(icon_size)
                self.btn_shuffle.setText("")
                self.btn_shuffle.setToolTip("Play in order")
            else:
                # Fallback: use text
                self.btn_shuffle.setIcon(QIcon())
                self.btn_shuffle.setText("🔁")
                self.btn_shuffle.setToolTip("Play in order")

    def toggle_shuffle_mode(self):
        """Cycle through shuffle modes: sequential -> shuffle -> repeat_one -> sequential"""
        modes = ["sequential", "shuffle", "repeat_one"]
        current_index = modes.index(self.play_mode)
        next_index = (current_index + 1) % len(modes)
        self.play_mode = modes[next_index]
        
        # Update button icon and tooltip
        self.update_shuffle_button_icon()
        
        # Create shuffled list if needed
        if self.play_mode == "shuffle" and not self.shuffled_indices:
            self.create_shuffled_list()
        
        print(f"Play mode changed to: {self.play_mode}")

    def create_shuffled_list(self):
        """Create a shuffled version of the playlist (optional, can remove if not needed)"""
        if not self.files:
            return
        
        # Store original indices
        self.original_indices = list(range(len(self.files)))
        
        # For shuffle mode, we don't need a predetermined shuffled list
        # We'll pick random songs on each next() call
        # But we can still store a shuffled list for reference
        self.shuffled_indices = list(range(len(self.files)))
        random.shuffle(self.shuffled_indices)
        
        print(f"Shuffled playlist created: {self.shuffled_indices}")

    def next(self):
        """Handle next track based on current play mode"""
        if not self.files:
            return
        
        if self.play_mode == "repeat_one":
            # Repeat current song
            self.play_selected(self.current_file_index)
            return
        
        if self.play_mode == "shuffle":
            # TRULY RANDOM: Pick a random song different from current
            if len(self.files) == 1:
                next_index = 0  # Only one song
            else:
                available_indices = [i for i in range(len(self.files)) if i != self.current_file_index]
                next_index = random.choice(available_indices)
            
            print(f"Shuffle mode: Randomly selected index {next_index}")
        else:
            # Sequential play
            next_index = (self.current_file_index + 1) % len(self.files)
        
        self.table.selectRow(next_index)
        self.play_selected(next_index)

    def prev(self):
        """Handle previous track based on current play mode"""
        if not self.files:
            return
        
        if self.play_mode == "repeat_one":
            # Repeat current song
            self.play_selected(self.current_file_index)
            return
        
        if self.play_mode == "shuffle":
            # In shuffle mode, "previous" should also be random
            if len(self.files) == 1:
                prev_index = 0  # Only one song
            else:
                available_indices = [i for i in range(len(self.files)) if i != self.current_file_index]
                prev_index = random.choice(available_indices)
            
            print(f"Shuffle mode: Random previous (new random song) index {prev_index}")
        else:
            # Sequential play
            prev_index = (self.current_file_index - 1) % len(self.files)
        
        self.table.selectRow(prev_index)
        self.play_selected(prev_index)
        
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

    def update_progress_from_audio(self, position):
        """Handle track completion and auto-advance"""
        if not self.user_is_seeking and self.audio.mono is not None and self.audio.duration > 0:
            value = int((position / self.audio.duration) * 10000)
            self.progress_bar.setValue(value)
            
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            # Auto-advance to next track when current finishes
            # Use a more precise check with hysteresis to prevent multiple triggers
            if position >= self.audio.duration and not hasattr(self, '_track_completed'):
                self._track_completed = True
                
                if self.play_mode == "repeat_one":
                    # Repeat current track
                    self.play_selected(self.current_file_index)
                else:
                    # Go to next track
                    QTimer.singleShot(100, self.next)
                
                # Reset the flag after a delay
                QTimer.singleShot(2000, lambda: delattr(self, '_track_completed'))

    def show_loading(self, filename):
        self.loading_label.setText(f"Loading: {filename}...")
        self.loading_label.setVisible(True)

    def hide_loading(self, filename):
        self.loading_label.setText("")
        self.loading_label.setVisible(False)

    def force_rescan_current_folder(self):
        """Force rescan of the current folder (ignoring database)"""
        if not self.files:
            QMessageBox.information(self, "No Folder", "Please load a folder first.")
            return
        
        # Get folder path from first file
        first_file = self.files[0] if self.files else ""
        folder_path = os.path.dirname(first_file)
        
        if not folder_path:
            return
        
        # Clear existing tracks from database for this folder
        self.db.delete_folder_tracks(folder_path)
        
        # Rescan
        self.scan_folder_to_database(folder_path)
    
    def load_recently_played(self):
        """Load recently played tracks from database"""
        self.db_status_label.setText("DB: Loading recent...")
        
        results = self.db.get_recently_played()
        
        # Clear current playlist
        self.clear_playlist()
        
        # Clear search box
        self.search_box.clear()
        
        # Clear all tracks storage
        self.all_tracks = []
        
        # Set table headers for new column order
        self.table.setHorizontalHeaderLabels(["💿 Track", "Duration", "Artist", "Album"])
        
        # Add results
        for file_path, file_name, artist, title, play_count, last_played in results:
            if os.path.exists(file_path):
                self.files.append(file_path)
                
                # Get duration
                duration = 0
                try:
                    duration = librosa.get_duration(path=file_path)
                except:
                    pass
                
                self.durations.append(duration)
                
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                # Column 0: Track name
                display_title = title if title != file_name else file_name
                track_item = QTableWidgetItem(f"💿 {display_title}")
                track_item.setData(Qt.UserRole, file_path)
                self.table.setItem(r, 0, track_item)
                
                # Column 1: Duration
                if duration > 0:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_text = f"{mins:02d}:{secs:02d}"
                else:
                    duration_text = "--:--"
                
                duration_item = QTableWidgetItem(duration_text)
                duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 1, duration_item)
                
                # Column 2: Artist
                self.table.setItem(r, 2, QTableWidgetItem(artist))
                
                # Column 3: Album (showing play count instead)
                self.table.setItem(r, 3, QTableWidgetItem(f"Played {play_count} times"))
                
                # Store in all_tracks for filtering
                self.all_tracks.append((file_path, file_name, duration, display_title, artist, f"Played {play_count} times", ""))
        
        self.db_status_label.setText(f"DB: Loaded {len(results)} recent tracks")
    
    def load_most_played(self):
        """Load most played tracks from database"""
        self.db_status_label.setText("DB: Loading popular...")
        
        results = self.db.get_most_played()
        
        # Clear current playlist
        self.clear_playlist()
        
        # Clear search box
        self.search_box.clear()
        
        # Clear all tracks storage
        self.all_tracks = []
        self.all_files = []
        self.all_durations = []
        
        # Add results
        for file_path, file_name, artist, title, play_count, last_played in results:
            if os.path.exists(file_path):
                self.files.append(file_path)
                
                duration = 0
                try:
                    duration = librosa.get_duration(path=file_path)
                except:
                    pass
                
                self.durations.append(duration)
                
                r = self.table.rowCount()
                self.table.insertRow(r)
                
                display_title = title if title != file_name else file_name
                track_item = QTableWidgetItem(f"💿 {display_title}")
                track_item.setData(Qt.UserRole, file_path)
                self.table.setItem(r, 0, track_item)
                
                self.table.setItem(r, 1, QTableWidgetItem(artist))
                self.table.setItem(r, 2, QTableWidgetItem(f"Played {play_count} times"))
                
                if duration > 0:
                    mins = int(duration // 60)
                    secs = int(duration % 60)
                    duration_text = f"{mins:02d}:{secs:02d}"
                else:
                    duration_text = "--:--"
                
                duration_item = QTableWidgetItem(duration_text)
                duration_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 3, duration_item)
                
                # Store in all_tracks for filtering
                self.all_tracks.append((file_path, file_name, duration, display_title, artist, f"Played {play_count} times", ""))
        
        self.db_status_label.setText(f"DB: Loaded {len(results)} popular tracks")
    
    def show_database_stats(self):
        """Show database statistics"""
        conn = sqlite3.connect(self.db.db_path)
        cursor = conn.cursor()
        
        # Get stats
        cursor.execute('SELECT COUNT(*) FROM tracks')
        total_tracks = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM folders')
        total_folders = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(play_count) FROM tracks')
        total_plays = cursor.fetchone()[0] or 0
        
        cursor.execute('''
            SELECT COUNT(*) FROM tracks 
            WHERE last_played IS NOT NULL
        ''')
        played_tracks = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT artist) FROM tracks 
            WHERE artist != 'Unknown Artist'
        ''')
        unique_artists = cursor.fetchone()[0]
        
        cursor.execute('''
            SELECT COUNT(DISTINCT album) FROM tracks 
            WHERE album != 'Unknown Album'
        ''')
        unique_albums = cursor.fetchone()[0]
        
        conn.close()
        
        # Show stats in message box
        stats_text = f"""
        <b>Database Statistics:</b><br><br>
        Total Tracks: {total_tracks}<br>
        Total Folders: {total_folders}<br>
        Total Plays: {total_plays}<br>
        Played Tracks: {played_tracks}<br>
        Unique Artists: {unique_artists}<br>
        Unique Albums: {unique_albums}<br>
        <br>
        Database File: {os.path.abspath(self.db.db_path)}
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Database Statistics")
        msg.setText(stats_text)
        msg.setIcon(QMessageBox.Information)
        msg.exec_()
    
    def clear_database(self):
        """Clear all data from database"""
        reply = QMessageBox.question(
            self, 'Clear Database',
            'Are you sure you want to clear ALL data from the database? This cannot be undone.',
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Delete the database file
                if os.path.exists(self.db.db_path):
                    os.remove(self.db.db_path)
                
                # Reinitialize database
                self.db = MusicDatabase()
                self.db_status_label.setText("DB: Cleared and Reset")
                
                # Clear playlist
                self.clear_playlist()
                
                QMessageBox.information(self, "Database Cleared", 
                                      "Database has been cleared and reinitialized.")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Could not clear database: {str(e)}")
    
    def clear_playlist(self):
        """Clear playlist display but keep all_tracks for filtering"""
        self.files.clear()
        self.durations.clear()
        self.shuffled_indices.clear()
        self.original_indices.clear()
        self.current_shuffle_index = -1
        self.table.setRowCount(0)
        # Don't clear self.all_tracks here - it should persist for filtering
        self.stop()
    
    def toggle_play(self):
        print(f"toggle_play called. audio.mono: {self.audio.mono is not None}, audio.running: {self.audio.running}, audio.isRunning(): {self.audio.isRunning()}")
        
        if self.audio.mono is None and self.files:
            print("No audio loaded, loading first track")
            self.play_selected(0)
        elif self.audio.mono is not None:
            if self.audio.running:
                print("Pausing playback")
                self.audio.running = False
            else:
                print("Resuming playback")
                self.audio.running = True
                
                # Make sure the audio thread is actually running
                if not self.audio.isRunning():
                    print("Audio thread not running, starting it...")
                    self.audio.start()
                else:
                    print("Audio thread is already running")
            
            # Update button icon after changing state
            self.update_play_button_icon(playing=self.audio.running)

    def update_play_button_icon(self, playing):
        """Update play button icon based on playback state"""
        if playing:
            # Show pause icon
            if hasattr(self.btn_play, 'pause_icon_path') and os.path.exists(self.btn_play.pause_icon_path):
                self.btn_play.setIcon(QIcon(self.btn_play.pause_icon_path))
                self.btn_play.setToolTip("Pause")
                self.btn_play.setText("")  # Clear text when using pause icon
            else:
                # Fallback to text
                self.btn_play.setIcon(QIcon())
                self.btn_play.setText("⏸")
                self.btn_play.setToolTip("Pause")
        else:
            # Show play icon
            if hasattr(self.btn_play, 'icon_path') and os.path.exists(self.btn_play.icon_path):
                self.btn_play.setIcon(QIcon(self.btn_play.icon_path))
                self.btn_play.setToolTip("Play")
                self.btn_play.setText("")  # Clear text when using play icon
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
        
        # Reset all tracks to CD emoji
        if self.current_file_index >= 0:
            for i in range(self.table.rowCount()):
                track_item = self.table.item(i, 0)
                if track_item:
                    text = track_item.text()
                    # Replace any colorful disc with CD emoji
                    if "🔴" in text or "🟢" in text or "🔵" in text or "🟡" in text or "🟣" in text or "🟠" in text:
                        parts = text.split(" ", 1)
                        if len(parts) > 1:
                            track_item.setText(f"💿 {parts[1]}")
                    track_item.setData(Qt.UserRole + 1, None)  # Clear playing flag
                
                duration_item = self.table.item(i, 3)  # Changed from 1 to 3
                if duration_item:
                    duration_item.setData(Qt.UserRole + 1, None)  # Clear playing flag
        
        self.table.viewport().update()

    # ===== SEEKING LOGIC =====
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
            
            print(f"Seeking to position: {position:.2f} seconds")
            
            self.audio.seek(position)
            
            mins = int(position // 60)
            secs = int(position % 60)
            self.current_time_label.setText(f"{mins:02d}:{secs:02d}")
            
            if not self.audio.running:
                self.audio.running = True
                # Update to pause icon when resuming from seek
                self.update_play_button_icon(playing=True)
            
            self.user_is_seeking = False

    def update_visualizer(self):
        self.spectrum.update()

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