"use client"

import { useState } from "react"
import { Search, Menu, X, Download, Video, ImageIcon, Music, Share2, Star, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

// Mock data for tools
const toolsData = [
  {
    id: 1,
    name: "YouTube Downloader",
    description: "Download videos from YouTube in various formats and qualities",
    platform: "YouTube",
    category: "Video Downloaders",
    icon: "🎥",
    featured: true,
    color: "bg-red-500",
  },
  {
    id: 2,
    name: "Instagram Downloader",
    description: "Save Instagram photos, videos, stories, and reels",
    platform: "Instagram",
    category: "Video Downloaders",
    icon: "📷",
    featured: true,
    color: "bg-pink-500",
  },
  {
    id: 3,
    name: "TikTok Downloader",
    description: "Download TikTok videos without watermark",
    platform: "TikTok",
    category: "Video Downloaders",
    icon: "🎵",
    featured: true,
    color: "bg-black",
  },
  {
    id: 4,
    name: "Douyin Downloader",
    description: "Download videos from Douyin (Chinese TikTok)",
    platform: "Douyin",
    category: "Video Downloaders",
    icon: "🎭",
    featured: false,
    color: "bg-blue-500",
  },
  {
    id: 5,
    name: "Facebook Downloader",
    description: "Save Facebook videos and photos to your device",
    platform: "Facebook",
    category: "Video Downloaders",
    icon: "👥",
    featured: false,
    color: "bg-blue-600",
  },
  {
    id: 6,
    name: "Twitter Downloader",
    description: "Download Twitter videos and GIFs easily",
    platform: "Twitter",
    category: "Video Downloaders",
    icon: "🐦",
    featured: false,
    color: "bg-sky-500",
  },
  {
    id: 7,
    name: "Image Compressor",
    description: "Compress images without losing quality",
    platform: "Universal",
    category: "Image Tools",
    icon: "🖼️",
    featured: false,
    color: "bg-green-500",
  },
  {
    id: 8,
    name: "Audio Converter",
    description: "Convert audio files between different formats",
    platform: "Universal",
    category: "Audio Tools",
    icon: "🎧",
    featured: false,
    color: "bg-purple-500",
  },
]

const categories = [
  { name: "All Tools", icon: Star, count: toolsData.length },
  { name: "Video Downloaders", icon: Video, count: toolsData.filter((t) => t.category === "Video Downloaders").length },
  { name: "Image Tools", icon: ImageIcon, count: toolsData.filter((t) => t.category === "Image Tools").length },
  { name: "Audio Tools", icon: Music, count: toolsData.filter((t) => t.category === "Audio Tools").length },
  {
    name: "Social Media Tools",
    icon: Share2,
    count: toolsData.filter((t) => t.category === "Social Media Tools").length,
  },
]

export default function ToolHub() {
  const [searchQuery, setSearchQuery] = useState("")
  const [selectedCategory, setSelectedCategory] = useState("All Tools")
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  const filteredTools = toolsData.filter((tool) => {
    const matchesSearch =
      tool.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
      tool.platform.toLowerCase().includes(searchQuery.toLowerCase())
    const matchesCategory = selectedCategory === "All Tools" || tool.category === selectedCategory
    return matchesSearch && matchesCategory
  })

  const featuredTools = toolsData.filter((tool) => tool.featured)

  const handleLaunchTool = (toolId: number) => {
    const tool = toolsData.find((t) => t.id === toolId)
    if (tool?.name === "YouTube Downloader") {
      window.location.href = "/tools/youtube-downloader"
    } else {
      // For other tools, show coming soon message
      alert(`${tool?.name} is coming soon!`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                <Download className="w-5 h-5 text-white" />
              </div>
              <span className="text-xl font-bold text-gray-900">ToolHub</span>
            </div>

            {/* Desktop Navigation */}
            <nav className="hidden md:flex space-x-8">
              <a href="#" className="text-gray-900 hover:text-blue-600 font-medium">
                Home
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 font-medium">
                Categories
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 font-medium">
                About
              </a>
              <a href="#" className="text-gray-600 hover:text-blue-600 font-medium">
                Contact
              </a>
            </nav>

            {/* Mobile Menu Button */}
            <button className="md:hidden p-2" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>

          {/* Mobile Navigation */}
          {mobileMenuOpen && (
            <div className="md:hidden py-4 border-t">
              <nav className="flex flex-col space-y-2">
                <a href="#" className="text-gray-900 hover:text-blue-600 font-medium py-2">
                  Home
                </a>
                <a href="#" className="text-gray-600 hover:text-blue-600 font-medium py-2">
                  Categories
                </a>
                <a href="#" className="text-gray-600 hover:text-blue-600 font-medium py-2">
                  About
                </a>
                <a href="#" className="text-gray-600 hover:text-blue-600 font-medium py-2">
                  Contact
                </a>
              </nav>
            </div>
          )}
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section with Search */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Multi-Platform Tool Hub</h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Discover and use powerful tools for downloading content from your favorite platforms
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
            <Input
              type="text"
              placeholder="Search for tools by name or platform..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-12 text-lg"
            />
          </div>
        </div>

        {/* Featured Tools Section */}
        {featuredTools.length > 0 && selectedCategory === "All Tools" && !searchQuery && (
          <section className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-6 flex items-center gap-2">
              <Star className="w-6 h-6 text-yellow-500" />
              Featured Tools
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {featuredTools.map((tool) => (
                <Card
                  key={tool.id}
                  className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1 border-2 border-yellow-200"
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                      <div className={`w-12 h-12 ${tool.color} rounded-lg flex items-center justify-center text-2xl`}>
                        {tool.icon}
                      </div>
                      <Badge variant="secondary" className="bg-yellow-100 text-yellow-800">
                        Featured
                      </Badge>
                    </div>
                    <CardTitle className="text-lg">{tool.name}</CardTitle>
                    <CardDescription className="text-sm">{tool.description}</CardDescription>
                  </CardHeader>
                  <CardContent className="pt-0">
                    <Button
                      className="w-full group-hover:bg-blue-600 transition-colors"
                      onClick={() => handleLaunchTool(tool.id)}
                    >
                      <ExternalLink className="w-4 h-4 mr-2" />
                      Launch Tool
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </section>
        )}

        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar - Categories */}
          <aside className="lg:w-64 flex-shrink-0">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Categories</h3>
              <nav className="space-y-2">
                {categories.map((category) => {
                  const Icon = category.icon
                  return (
                    <button
                      key={category.name}
                      onClick={() => setSelectedCategory(category.name)}
                      className={`w-full flex items-center justify-between p-3 rounded-lg text-left transition-colors ${
                        selectedCategory === category.name
                          ? "bg-blue-50 text-blue-700 border border-blue-200"
                          : "hover:bg-gray-50 text-gray-700"
                      }`}
                    >
                      <div className="flex items-center space-x-3">
                        <Icon className="w-5 h-5" />
                        <span className="font-medium">{category.name}</span>
                      </div>
                      <Badge variant="secondary" className="text-xs">
                        {category.count}
                      </Badge>
                    </button>
                  )
                })}
              </nav>
            </div>
          </aside>

          {/* Main Content - Tools Grid */}
          <main className="flex-1">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                {selectedCategory} {searchQuery && `- "${searchQuery}"`}
              </h2>
              <p className="text-gray-600">
                {filteredTools.length} tool{filteredTools.length !== 1 ? "s" : ""} found
              </p>
            </div>

            {filteredTools.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <Search className="w-12 h-12 text-gray-400" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">No tools found</h3>
                <p className="text-gray-600">Try adjusting your search or category filter</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {filteredTools.map((tool) => (
                  <Card
                    key={tool.id}
                    className="group hover:shadow-lg transition-all duration-300 hover:-translate-y-1"
                  >
                    <CardHeader className="pb-3">
                      <div
                        className={`w-12 h-12 ${tool.color} rounded-lg flex items-center justify-center text-2xl mb-3`}
                      >
                        {tool.icon}
                      </div>
                      <CardTitle className="text-lg">{tool.name}</CardTitle>
                      <CardDescription className="text-sm">{tool.description}</CardDescription>
                    </CardHeader>
                    <CardContent className="pt-0">
                      <div className="flex items-center justify-between mb-3">
                        <Badge variant="outline" className="text-xs">
                          {tool.platform}
                        </Badge>
                        <span className="text-xs text-gray-500">{tool.category}</span>
                      </div>
                      <Button
                        className="w-full group-hover:bg-blue-600 transition-colors"
                        onClick={() => handleLaunchTool(tool.id)}
                      >
                        <ExternalLink className="w-4 h-4 mr-2" />
                        Launch Tool
                      </Button>
                    </CardContent>
                  </Card>
                ))}
              </div>
            )}
          </main>
        </div>
      </div>

      {/* Footer */}
      <footer className="bg-white border-t mt-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="col-span-1 md:col-span-2">
              <div className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-600 to-purple-600 rounded-lg flex items-center justify-center">
                  <Download className="w-5 h-5 text-white" />
                </div>
                <span className="text-xl font-bold text-gray-900">ToolHub</span>
              </div>
              <p className="text-gray-600 mb-4 max-w-md">
                Your one-stop destination for powerful tools to download and manage content from various platforms.
              </p>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Quick Links</h4>
              <ul className="space-y-2 text-gray-600">
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Home
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Categories
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    About
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Contact
                  </a>
                </li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-gray-900 mb-4">Support</h4>
              <ul className="space-y-2 text-gray-600">
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Help Center
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a href="#" className="hover:text-blue-600">
                    FAQ
                  </a>
                </li>
              </ul>
            </div>
          </div>

          <div className="border-t pt-8 mt-8 text-center text-gray-600">
            <p>&copy; 2025 ToolHub. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}
