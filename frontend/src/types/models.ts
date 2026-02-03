export interface Artist {
  id: number
  name: string
  spotify_id?: string
  created_at: string
  updated_at: string
}

export interface Album {
  id: number
  title: string
  year?: number
  support?: string
  discogs_id?: string
  spotify_url?: string
  discogs_url?: string
  artists: string[]
  images: string[]
  ai_info?: string
  created_at: string
  updated_at: string
}

export interface AlbumDetail extends Album {
  resume?: string
  labels?: string[]
  film_title?: string
  film_year?: number
  film_director?: string
  artist_images?: Record<string, string>
}

export interface ListeningHistory {
  id: number
  timestamp: number
  date: string
  artist: string
  title: string
  album: string
  year?: number
  album_id?: number
  track_id?: number
  loved: boolean
  source: string
  artist_image?: string
  album_image?: string
  album_lastfm_image?: string
  spotify_url?: string
  discogs_url?: string
  ai_info?: string
}

export interface Playlist {
  id: number
  name: string
  algorithm: string
  ai_prompt?: string
  track_count: number
  created_at: string
}

export interface PlaylistTrack {
  track_id: number
  position: number
  title: string
  artist: string
  album: string
  duration_seconds?: number
}

export interface PlaylistDetail extends Playlist {
  tracks: PlaylistTrack[]
  total_duration_seconds?: number
  unique_artists: number
  unique_albums: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  pages: number
}

export interface Stats {
  total_tracks: number
  unique_artists: number
  unique_albums: number
  peak_hour?: number
  total_duration_seconds?: number
}
