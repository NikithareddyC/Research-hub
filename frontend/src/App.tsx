import { useState } from 'react'
import axios from 'axios'
import './App.css'

interface Paper {
  id: string
  title: string
  authors: string[]
  published_date: string | null
  summary: string
  relevance_score: number
  source: string
  url: string
  citations_count: number
}

export default function App() {
  const [query, setQuery] = useState('')
  const [papers, setPapers] = useState<Paper[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [sources, setSources] = useState(['arxiv', 'crossref', 'openalex'])
  const [sortBy, setSortBy] = useState('relevance')

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!query.trim()) {
      setError('Please enter a search query')
      return
    }

    setLoading(true)
    setError('')
    setPapers([])

    try {
      const response = await axios.post('/api/v1/search', {
        query,
        sources,
        limit: 100,
        sort_by: sortBy
      })

      setPapers(response.data.papers)
      if (response.data.papers.length === 0) {
        setError('No papers found for your query')
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Error searching papers. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const toggleSource = (source: string) => {
    setSources(prev =>
      prev.includes(source)
        ? prev.filter(s => s !== source)
        : [...prev, source]
    )
  }

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <h1>📚 Research Paper Intelligence Hub</h1>
          <p>Search, summarize, and analyze academic papers from global databases</p>
        </div>
      </header>

      <main className="main">
        <div className="container">
          <form onSubmit={handleSearch} className="search-form">
            <div className="search-input-group">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter your research keywords..."
                className="search-input"
              />
              <button type="submit" disabled={loading} className="search-button">
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>

            <div className="filters">
              <div className="filter-group">
                <label>Sources:</label>
                <div className="checkbox-group">
                  {['arxiv', 'crossref', 'openalex', 'core', 'pubmed'].map(source => (
                    <label key={source} className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={sources.includes(source)}
                        onChange={() => toggleSource(source)}
                      />
                      {source.charAt(0).toUpperCase() + source.slice(1)}
                    </label>
                  ))}
                </div>
              </div>

              <div className="filter-group">
                <label>Sort by:</label>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value)} className="select">
                  <option value="relevance">Relevance</option>
                  <option value="date">Date (Newest)</option>
                  <option value="citations">Citations</option>
                </select>
              </div>
            </div>
          </form>

          {error && <div className="error-message">{error}</div>}

          <div className="results">
            {papers.length > 0 && (
              <div className="results-header">
                <h2>Found {papers.length} papers</h2>
              </div>
            )}

            <div className="papers-grid">
              {papers.map((paper) => (
                <div key={paper.id} className="paper-card">
                  <div className="paper-header">
                    <h3>{paper.title}</h3>
                    <span className="source-badge">{paper.source}</span>
                  </div>

                  <div className="paper-meta">
                    <span className="relevance">Relevance: {(paper.relevance_score * 100).toFixed(0)}%</span>
                    {paper.citations_count > 0 && (
                      <span className="citations">Citations: {paper.citations_count}</span>
                    )}
                  </div>

                  <p className="authors">
                    {paper.authors.slice(0, 3).join(', ')}
                    {paper.authors.length > 3 && ` +${paper.authors.length - 3}`}
                  </p>

                  <p className="summary">{paper.summary}</p>

                  {paper.published_date && (
                    <p className="date">{new Date(paper.published_date).toLocaleDateString()}</p>
                  )}

                  <a href={paper.url} target="_blank" rel="noopener noreferrer" className="read-button">
                    Read Full Paper →
                  </a>
                </div>
              ))}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}
