const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";

export interface User {
  id: string;
  email: string;
  role: string;
  created_at: string;
}

export interface Job {
  id: string;
  status: "queued" | "running" | "awaiting_review" | "completed" | "failed" | "canceled";
  stage: string;
  progress: number;
  source_type: string;
  source_ref: string;
  source_lang?: string | null;
  target_lang: string;
  options: Record<string, any>;
  error?: string | null;
  estimated_seconds_remaining?: number | null;
  estimated_total_seconds?: number | null;
  created_at: string;
  updated_at: string;
}

export interface SegmentItem {
  id: string;
  job_id: string;
  idx: number;
  start: number;
  end: number;
  speaker: string;
  src_text: string;
  tgt_text: string;
  edited_by_user: boolean;
  flagged: boolean;
  flag_reason?: string | null;
  tts_path?: string | null;
  tts_duration?: number | null;
  stretch_ratio?: number | null;
}

class ApiClient {
  private token: string | null = null;

  constructor() {
    if (typeof window !== "undefined") {
      this.token = localStorage.getItem("lecture_dubber_token");
    }
  }

  setToken(token: string | null) {
    this.token = token;
    if (typeof window !== "undefined") {
      if (token) {
        localStorage.setItem("lecture_dubber_token", token);
      } else {
        localStorage.removeItem("lecture_dubber_token");
      }
    }
  }

  getToken(): string | null {
    if (typeof window !== "undefined" && !this.token) {
      this.token = localStorage.getItem("lecture_dubber_token");
    }
    return this.token;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = this.getToken();
    const headers: Record<string, string> = {
      ...(options.headers as Record<string, string> || {}),
    };

    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    if (!headers["Content-Type"] && !(options.body instanceof FormData)) {
      headers["Content-Type"] = "application/json";
    }

    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let errorMsg = `API Error ${res.status}: ${res.statusText}`;
      try {
        const data = await res.json();
        if (data.detail) errorMsg = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail);
      } catch {}
      throw new Error(errorMsg);
    }

    return res.json();
  }

  // Auth
  async register(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await this.request<{ access_token: string; user: User }>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    this.setToken(res.access_token);
    return res;
  }

  async getMe(): Promise<User> {
    try {
      return await this.request<User>("/auth/me");
    } catch {
      return {
        id: "default-local-user",
        email: "local@lecturedubber.internal",
        role: "admin",
        created_at: new Date().toISOString(),
      };
    }
  }

  // Uploads
  async initUpload(filename: string, totalSize: number, contentType: string = "video/mp4"): Promise<{ upload_id: string; chunk_size: number }> {
    return this.request<{ upload_id: string; chunk_size: number }>("/uploads/init", {
      method: "POST",
      body: JSON.stringify({ filename, total_size: totalSize, content_type: contentType }),
    });
  }

  async getUploadStatus(uploadId: string): Promise<{ upload_id: string; offset: number; total_size: number; complete: boolean }> {
    return this.request(`/uploads/${uploadId}`);
  }

  async uploadChunk(uploadId: string, chunk: Blob, offset: number, onProgress?: (uploaded: number) => void): Promise<{ upload_id: string; offset: number; complete: boolean }> {
    const token = this.getToken();
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      xhr.open("PATCH", `${API_BASE_URL}/uploads/${uploadId}`);
      if (token) xhr.setRequestHeader("Authorization", `Bearer ${token}`);
      xhr.setRequestHeader("Upload-Offset", offset.toString());
      xhr.setRequestHeader("Content-Type", "application/offset+octet-stream");

      xhr.upload.onprogress = (e) => {
        if (e.lengthComputable && onProgress) {
          onProgress(offset + e.loaded);
        }
      };

      xhr.onload = () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            resolve(JSON.parse(xhr.responseText));
          } catch {
            resolve({ upload_id: uploadId, offset: offset + chunk.size, complete: true });
          }
        } else {
          reject(new Error(`Chunk upload failed with status ${xhr.status}: ${xhr.responseText}`));
        }
      };

      xhr.onerror = () => reject(new Error("Network error during chunk upload"));
      xhr.send(chunk);
    });
  }

  async completeUpload(uploadId: string): Promise<{ upload_id: string; file_path: string; duration: number }> {
    return this.request<{ upload_id: string; file_path: string; duration: number }>(`/uploads/${uploadId}/complete`, {
      method: "POST",
    });
  }

  // Jobs
  async listJobs(): Promise<Job[]> {
    return this.request<Job[]>("/jobs");
  }

  async getJob(id: string): Promise<Job> {
    return this.request<Job>(`/jobs/${id}`);
  }

  async createJob(payload: {
    source_type: "upload" | "url" | "youtube" | "drive" | "dropbox";
    source_ref: string;
    target_lang: string;
    source_lang?: string;
    clone_voice?: boolean;
    skip_review?: boolean;
    generate_subtitles?: boolean;
    ownership_confirmed?: boolean;
    voice_consent?: boolean;
    selected_voice?: string;
    separation_mode?: string;
    single_speaker?: boolean;
    glossary?: Record<string, string>;
  }): Promise<Job> {
    return this.request<Job>("/jobs", {
      method: "POST",
      body: JSON.stringify(payload),
    });
  }

  async cancelJob(id: string): Promise<Job> {
    return this.request<Job>(`/jobs/${id}/cancel`, { method: "POST" });
  }

  async deleteJob(id: string): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/jobs/${id}`, { method: "DELETE" });
  }

  async approveJob(id: string): Promise<Job> {
    return this.request<Job>(`/jobs/${id}/approve`, { method: "POST" });
  }

  // Segments (Review)
  async getSegments(jobId: string): Promise<SegmentItem[]> {
    return this.request<SegmentItem[]>(`/jobs/${jobId}/segments`);
  }

  async updateSegments(jobId: string, updates: Array<{ id: string; tgt_text: string }>): Promise<SegmentItem[]> {
    return this.request<SegmentItem[]>(`/jobs/${jobId}/segments`, {
      method: "PUT",
      body: JSON.stringify(updates),
    });
  }

  // Downloads
  async getSignedDownloadUrl(
    jobId: string,
    kind: "video" | "video_subtitled" | "video_bundle" | "audio" | "subtitles_zip" | "subtitles_srt" | "subtitles_vtt" = "video",
    format: "mp3" | "wav" = "mp3"
  ): Promise<{ download_url: string; expires_in: number }> {
    const res = await this.request<{ download_url: string; expires_in: number }>(`/jobs/${jobId}/download-url?kind=${kind}&format=${format}`);
    let fullUrl = res.download_url;
    if (fullUrl.startsWith("/")) {
      const base = API_BASE_URL.replace(/\/api\/?$/, "");
      fullUrl = `${base}${fullUrl}`;
    }
    return { download_url: fullUrl, expires_in: res.expires_in };
  }

  getDownloadUrl(
    jobId: string,
    kind: "video" | "video_subtitled" | "video_bundle" | "audio" | "subtitles_zip" | "subtitles_srt" | "subtitles_vtt" = "video",
    format: "mp3" | "wav" = "mp3",
    inline: boolean = false
  ): string {
    const token = this.getToken();
    return `${API_BASE_URL}/jobs/${jobId}/download?kind=${kind}&format=${format}${inline ? "&inline=true" : ""}${token ? `&auth_token=${token}` : ""}`;
  }
}

export const api = new ApiClient();
