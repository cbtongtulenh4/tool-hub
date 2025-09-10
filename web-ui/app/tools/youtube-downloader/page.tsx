"use client"

import type React from "react"

import { useState } from "react"
import { ArrowLeft, Download, RefreshCw, Play, Clock, Eye, ThumbsUp, Link, AlertCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface VideoInfo {
  title: string
  thumbnail: string
  duration: string
  views: string
  likes: string
  channel: string
  uploadDate: string
  description: string
}

export default function YouTubeDownloader() {
  const [url, setUrl] = useState("")
  const [videoInfo, setVideoInfo] = useState<VideoInfo | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  // Mock function to simulate fetching video info
  const fetchVideoInfo = async (videoUrl: string) => {
    setLoading(true)
    setError("")

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 2000))

    // Mock validation
    if (!videoUrl.includes("youtube.com") && !videoUrl.includes("youtu.be")) {
      setError("Please enter a valid YouTube URL")
      setLoading(false)
      return
    }

    // Mock video data
    const mockVideoInfo: VideoInfo = {
      title: "Amazing Nature Documentary - Wildlife in 4K",
      thumbnail: "/wildlife-docu-thumbnail.png",
      duration: "15:42",
      views: "2.5M views",
      likes: "45K",
      channel: "Nature Explorer",
      uploadDate: "2 days ago",
      description:
        "Explore the breathtaking beauty of wildlife in stunning 4K resolution. This documentary takes you on a journey through diverse ecosystems...",
    }

    setVideoInfo(mockVideoInfo)
    setLoading(false)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (url.trim()) {
      fetchVideoInfo(url)
    }
  }

  const handleRefresh = () => {
    setUrl("")
    setVideoInfo(null)
    setError("")
  }

  const handleDownload = () => {
    // Mock download functionality
    alert("Download started! (This is a demo)")
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center h-16">
            <Button variant="ghost" size="sm" className="mr-4" onClick={() => window.history.back()}>
              <ArrowLeft className="w-4 h-4 mr-2" />
              Back to Tools
            </Button>
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-red-500 rounded-lg flex items-center justify-center text-white text-lg">
                🎥
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">YouTube Downloader</h1>
                <p className="text-sm text-gray-600">Download videos from YouTube</p>
              </div>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* URL Input Section */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Link className="w-5 h-5" />
              Enter YouTube URL
            </CardTitle>
            <CardDescription>Paste the YouTube video URL you want to download</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="flex gap-2">
                <Input
                  type="url"
                  placeholder="https://www.youtube.com/watch?v=..."
                  value={url}
                  onChange={(e) => setUrl(e.target.value)}
                  className="flex-1"
                  disabled={loading}
                />
                <Button type="submit" disabled={loading || !url.trim()}>
                  {loading ? (
                    <>
                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                      Loading...
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Get Video
                    </>
                  )}
                </Button>
                <Button type="button" variant="outline" onClick={handleRefresh}>
                  <RefreshCw className="w-4 h-4" />
                </Button>
              </div>
            </form>

            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Video Preview Section */}
        {videoInfo && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Video Preview</CardTitle>
              <CardDescription>Review the video details before downloading</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Video Thumbnail */}
                <div className="space-y-4">
                  <div className="relative rounded-lg overflow-hidden bg-gray-100">
                    <img
                      src={videoInfo.thumbnail || "/placeholder.svg"}
                      alt={videoInfo.title}
                      className="w-full h-auto aspect-video object-cover"
                    />
                    <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white px-2 py-1 rounded text-sm">
                      {videoInfo.duration}
                    </div>
                  </div>

                  {/* Download Button */}
                  <Button onClick={handleDownload} className="w-full bg-red-600 hover:bg-red-700">
                    <Download className="w-4 h-4 mr-2" />
                    Download Video
                  </Button>
                </div>

                {/* Video Info */}
                <div className="space-y-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">{videoInfo.title}</h3>
                    <div className="flex items-center gap-4 text-sm text-gray-600 mb-3">
                      <div className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        {videoInfo.views}
                      </div>
                      <div className="flex items-center gap-1">
                        <ThumbsUp className="w-4 h-4" />
                        {videoInfo.likes}
                      </div>
                      <div className="flex items-center gap-1">
                        <Clock className="w-4 h-4" />
                        {videoInfo.uploadDate}
                      </div>
                    </div>
                    <Badge variant="secondary" className="mb-3">
                      {videoInfo.channel}
                    </Badge>
                  </div>

                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">Description</h4>
                    <p className="text-sm text-gray-600 line-clamp-4">{videoInfo.description}</p>
                  </div>

                  {/* Download Options */}
                  <div className="space-y-3">
                    <h4 className="font-medium text-gray-900">Download Options</h4>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <span className="font-medium">MP4 - 1080p</span>
                          <p className="text-sm text-gray-600">High quality video</p>
                        </div>
                        <Badge>Recommended</Badge>
                      </div>
                      <div className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <span className="font-medium">MP4 - 720p</span>
                          <p className="text-sm text-gray-600">Standard quality</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between p-3 border rounded-lg">
                        <div>
                          <span className="font-medium">MP3 - Audio Only</span>
                          <p className="text-sm text-gray-600">Extract audio track</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Instructions */}
        <Card>
          <CardHeader>
            <CardTitle>How to Use</CardTitle>
          </CardHeader>
          <CardContent>
            <ol className="list-decimal list-inside space-y-2 text-gray-700">
              <li>Copy the YouTube video URL from your browser</li>
              <li>Paste the URL in the input field above</li>
              <li>Click "Get Video" to fetch video information</li>
              <li>Review the video details and select your preferred quality</li>
              <li>Click "Download Video" to start the download</li>
              <li>Use the refresh button to start over with a new URL</li>
            </ol>

            <Alert className="mt-4">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>
                This is a demo interface. In a real implementation, you would integrate with a YouTube download API or
                service.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
