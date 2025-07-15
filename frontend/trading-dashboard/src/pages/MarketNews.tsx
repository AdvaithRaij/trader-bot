import React, { useState, useEffect } from 'react'
import { 
  Newspaper, 
  TrendingUp, 
  TrendingDown, 
  Clock, 
  ExternalLink, 
  RefreshCw,
  Filter,
  Search,
  Calendar
} from 'lucide-react'
import { cn, formatDateTime } from '../lib/utils'
import type { NewsItem } from '../data/mockData'
import { mockNews } from '../data/mockData'

export function MarketNews() {
  const [news, setNews] = useState<NewsItem[]>(mockNews)
  const [filteredNews, setFilteredNews] = useState<NewsItem[]>(mockNews)
  const [searchTerm, setSearchTerm] = useState('')
  const [sentimentFilter, setSentimentFilter] = useState('all')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [sourceFilter, setSourceFilter] = useState('all')
  const [isLoading, setIsLoading] = useState(false)

  const sentiments = ['all', 'positive', 'negative', 'neutral']
  const categories = ['all', ...Array.from(new Set(news.map(item => item.category)))]
  const sources = ['all', ...Array.from(new Set(news.map(item => item.source)))]

  useEffect(() => {
    let filtered = news

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(item => 
        item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.summary.toLowerCase().includes(searchTerm.toLowerCase()) ||
        (item.symbols && item.symbols.some(symbol => symbol.toLowerCase().includes(searchTerm.toLowerCase())))
      )
    }

    // Filter by sentiment
    if (sentimentFilter !== 'all') {
      filtered = filtered.filter(item => item.sentiment === sentimentFilter)
    }

    // Filter by category
    if (categoryFilter !== 'all') {
      filtered = filtered.filter(item => item.category === categoryFilter)
    }

    // Filter by source
    if (sourceFilter !== 'all') {
      filtered = filtered.filter(item => item.source === sourceFilter)
    }

    setFilteredNews(filtered)
  }, [news, searchTerm, sentimentFilter, categoryFilter, sourceFilter])

  const handleRefresh = async () => {
    setIsLoading(true)
    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 1500))
    setIsLoading(false)
  }

  const getSentimentIcon = (sentiment: string) => {
    switch (sentiment) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-green-400" />
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-red-400" />
      default:
        return <div className="w-4 h-4 rounded-full bg-gray-400" />
    }
  }

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case 'positive': return 'text-green-400 bg-green-500/20'
      case 'negative': return 'text-red-400 bg-red-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  const getCategoryColor = (category: string) => {
    switch (category) {
      case 'market': return 'text-blue-400 bg-blue-500/20'
      case 'company': return 'text-purple-400 bg-purple-500/20'
      case 'economy': return 'text-yellow-400 bg-yellow-500/20'
      case 'technology': return 'text-cyan-400 bg-cyan-500/20'
      case 'policy': return 'text-orange-400 bg-orange-500/20'
      default: return 'text-gray-400 bg-gray-500/20'
    }
  }

  // Calculate sentiment summary
  const sentimentSummary = {
    positive: filteredNews.filter(n => n.sentiment === 'positive').length,
    negative: filteredNews.filter(n => n.sentiment === 'negative').length,
    neutral: filteredNews.filter(n => n.sentiment === 'neutral').length
  }

  const averageSentiment = filteredNews.length > 0 
    ? filteredNews.reduce((sum, item) => sum + item.sentimentScore, 0) / filteredNews.length 
    : 0

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mobile-stack">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl sm:text-3xl font-bold gradient-text">Market News</h1>
          <p className="text-gray-400 mt-1 text-sm sm:text-base">Stay updated with latest market developments and sentiment analysis</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={isLoading}
          className="flex items-center space-x-2 px-3 sm:px-4 py-2 glass rounded-lg hover:bg-white/10 transition-colors disabled:opacity-50 touch-friendly self-start sm:self-auto"
        >
          <RefreshCw className={cn("w-4 h-4", isLoading && "animate-spin")} />
          <span className="text-sm sm:text-base">Refresh News</span>
        </button>
      </div>

      {/* Sentiment Overview */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="glass-card p-4 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="min-w-0 flex-1">
              <p className="text-xs sm:text-sm font-medium text-gray-400 truncate">Overall Sentiment</p>
              <p className={cn(
                "text-lg sm:text-2xl font-bold mt-1",
                averageSentiment > 0.2 ? "text-green-400" :
                averageSentiment < -0.2 ? "text-red-400" : "text-gray-400"
              )}>
                {averageSentiment > 0.2 ? 'Positive' :
                 averageSentiment < -0.2 ? 'Negative' : 'Neutral'}
              </p>
              <p className="text-xs sm:text-sm text-gray-400">Score: {averageSentiment.toFixed(2)}</p>
            </div>
            <div className={cn(
              "p-2 sm:p-3 rounded-lg flex-shrink-0 ml-2",
              averageSentiment > 0.2 ? "bg-green-500/20 text-green-400" :
              averageSentiment < -0.2 ? "bg-red-500/20 text-red-400" : "bg-gray-500/20 text-gray-400"
            )}>
              {averageSentiment > 0.2 ? <TrendingUp className="w-5 h-5 sm:w-6 sm:h-6" /> :
               averageSentiment < -0.2 ? <TrendingDown className="w-5 h-5 sm:w-6 sm:h-6" /> : 
               <div className="w-5 h-5 sm:w-6 sm:h-6 rounded-full bg-current opacity-60" />}
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Positive News</p>
              <p className="text-2xl font-bold text-green-400 mt-1">{sentimentSummary.positive}</p>
              <p className="text-sm text-gray-400">
                {filteredNews.length > 0 ? Math.round((sentimentSummary.positive / filteredNews.length) * 100) : 0}% of total
              </p>
            </div>
            <div className="p-3 rounded-lg bg-green-500/20 text-green-400">
              <TrendingUp className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Negative News</p>
              <p className="text-2xl font-bold text-red-400 mt-1">{sentimentSummary.negative}</p>
              <p className="text-sm text-gray-400">
                {filteredNews.length > 0 ? Math.round((sentimentSummary.negative / filteredNews.length) * 100) : 0}% of total
              </p>
            </div>
            <div className="p-3 rounded-lg bg-red-500/20 text-red-400">
              <TrendingDown className="w-6 h-6" />
            </div>
          </div>
        </div>

        <div className="glass-card p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-400">Total Articles</p>
              <p className="text-2xl font-bold text-white mt-1">{filteredNews.length}</p>
              <p className="text-sm text-gray-400">Last updated: now</p>
            </div>
            <div className="p-3 rounded-lg bg-blue-500/20 text-blue-400">
              <Newspaper className="w-6 h-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="glass-card p-4 sm:p-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 min-w-0">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search news, stocks, or topics..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50 touch-friendly"
              />
            </div>
          </div>

          {/* Mobile Filter Row */}
          <div className="flex flex-col sm:flex-row gap-2 sm:gap-4">
            {/* Sentiment Filter */}
            <div className="flex items-center space-x-2 min-w-0">
              <TrendingUp className="w-4 h-4 text-gray-400 hidden sm:block" />
              <select
                value={sentimentFilter}
                onChange={(e) => setSentimentFilter(e.target.value)}
                className="w-full sm:w-auto px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly text-sm"
              >
                {sentiments.map(sentiment => (
                  <option key={sentiment} value={sentiment} className="bg-gray-800">
                    {sentiment === 'all' ? 'All Sentiments' : sentiment.charAt(0).toUpperCase() + sentiment.slice(1)}
                  </option>
                ))}
              </select>
            </div>

            {/* Category Filter */}
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="w-full sm:w-auto px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly text-sm"
            >
              {categories.map(category => (
                <option key={category} value={category} className="bg-gray-800">
                  {category === 'all' ? 'All Categories' : category.charAt(0).toUpperCase() + category.slice(1)}
                </option>
              ))}
            </select>

            {/* Source Filter */}
            <select
              value={sourceFilter}
              onChange={(e) => setSourceFilter(e.target.value)}
              className="w-full sm:w-auto px-3 py-2 bg-white/5 border border-white/10 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 touch-friendly text-sm"
            >
              {sources.map(source => (
              <option key={source} value={source} className="bg-gray-800">
                {source === 'all' ? 'All Sources' : source}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* News Feed */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center space-x-3">
              <RefreshCw className="w-6 h-6 text-blue-400 animate-spin" />
              <span className="text-lg text-gray-300">Loading latest news...</span>
            </div>
          </div>
        ) : (
          filteredNews.map((item) => (
            <div key={item.id} className="glass-card p-4 sm:p-6 hover:bg-white/5 transition-colors">
              <div className="flex flex-col space-y-4">
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 sm:gap-3 mb-3">
                    {getSentimentIcon(item.sentiment)}
                    <span className={cn(
                      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                      getSentimentColor(item.sentiment)
                    )}>
                      {item.sentiment.toUpperCase()}
                    </span>
                    <span className={cn(
                      "inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium",
                      getCategoryColor(item.category)
                    )}>
                      {item.category.toUpperCase()}
                    </span>
                    <span className="text-xs text-gray-400">
                      Confidence: {item.confidence}%
                    </span>
                  </div>

                  <h3 className="text-lg sm:text-xl font-semibold text-white mb-2 leading-tight">
                    {item.title}
                  </h3>

                  <p className="text-gray-300 mb-4 leading-relaxed text-sm sm:text-base">
                    {item.summary}
                  </p>

                  {/* Meta Information */}
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 sm:gap-4">
                    <div className="flex flex-wrap items-center gap-2 sm:gap-4 text-xs sm:text-sm text-gray-400">
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3 sm:w-4 sm:h-4" />
                        <span>{formatDateTime(new Date(item.publishedAt))}</span>
                      </div>
                      <span className="hidden sm:inline">•</span>
                      <span>{item.source}</span>
                      {item.author && (
                        <>
                          <span className="hidden sm:inline">•</span>
                          <span className="hidden sm:inline">{item.author}</span>
                        </>
                      )}
                      <span className="hidden sm:inline">•</span>
                      <span>{item.readTime} min read</span>
                    </div>

                    {item.url && (
                      <a
                        href={item.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center space-x-1 text-blue-400 hover:text-blue-300 transition-colors touch-friendly self-start sm:self-auto"
                      >
                        <span className="text-sm">Read full article</span>
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>

                  {item.symbols && item.symbols.length > 0 && (
                    <div className="mt-4 pt-4 border-t border-white/10">
                      <div className="flex flex-col sm:flex-row sm:items-center space-y-2 sm:space-y-0 sm:space-x-2">
                        <span className="text-sm text-gray-400 flex-shrink-0">Related stocks:</span>
                        <div className="flex flex-wrap gap-1">
                          {item.symbols.map((symbol, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-blue-500/20 text-blue-400"
                            >
                              {symbol}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {filteredNews.length === 0 && !isLoading && (
          <div className="text-center py-12">
            <p className="text-gray-400">No news articles found matching your criteria</p>
          </div>
        )}
      </div>
    </div>
    </div>
  )
}
