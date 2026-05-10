import { useState, useCallback } from 'react'
import axios from 'axios'

const API_BASE = '/api'

export interface Message {
  id: string
  question: string
  answer: string
  timestamp: string
  sources: Array<{ title: string; url: string; excerpt: string }>
}

export interface UseQueryReturn {
  messages: Message[]
  loading: boolean
  error: string | null
  query: (question: string, mode?: string) => Promise<void>
  clearMessages: () => void
}

export function useQuery(): UseQueryReturn {
  const [messages, setMessages] = useState<Message[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const query = useCallback(async (question: string, mode: string = 'hybrid') => {
    if (!question.trim()) {
      setError('請輸入問題')
      return
    }

    setLoading(true)
    setError(null)

    try {
      const response = await axios.post(`${API_BASE}/query`, {
        question,
        mode
      })

      const newMessage: Message = {
        id: Date.now().toString(),
        question,
        answer: response.data.answer,
        timestamp: response.data.timestamp,
        sources: response.data.sources || []
      }

      setMessages(prev => [...prev, newMessage])
    } catch (err: any) {
      const errorMsg = err.response?.data?.detail || err.message || '查詢失敗'
      setError(errorMsg)
      console.error('Query error:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const clearMessages = useCallback(() => {
    setMessages([])
    setError(null)
  }, [])

  return { messages, loading, error, query, clearMessages }
}

export async function fetchDocuments() {
  try {
    const response = await axios.get(`${API_BASE}/documents`)
    return response.data
  } catch (err) {
    console.error('Error fetching documents:', err)
    throw err
  }
}

export async function fetchStatus() {
  try {
    const response = await axios.get(`${API_BASE}/status`)
    return response.data
  } catch (err) {
    console.error('Error fetching status:', err)
    throw err
  }
}

export async function triggerScrape(maxPages: number = 100) {
  try {
    const response = await axios.post(`${API_BASE}/scrape`, {
      max_pages: maxPages,
      delay_seconds: 2.0
    })
    return response.data
  } catch (err) {
    console.error('Error triggering scrape:', err)
    throw err
  }
}

export async function triggerRefresh() {
  try {
    const response = await axios.post(`${API_BASE}/refresh`, {})
    return response.data
  } catch (err) {
    console.error('Error triggering refresh:', err)
    throw err
  }
}
