import { useState, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Send, MessageCircle, Loader } from 'lucide-react'
import { useQuery, Message } from '../hooks/useQuery'

export function ChatInterface() {
  const { t } = useTranslation()
  const { messages, loading, error, query } = useQuery()
  const [input, setInput] = useState('')
  const [mode, setMode] = useState('hybrid')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      await query(input, mode)
      setInput('')
    }
  }

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b border-gray-200 p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center gap-3 mb-4">
            <MessageCircle className="w-6 h-6 text-blue-600" />
            <div>
              <h1 className="text-xl font-bold text-gray-900">{t('app.title')}</h1>
              <p className="text-sm text-gray-600">{t('app.subtitle')}</p>
            </div>
          </div>
          <div className="flex gap-2">
            <select
              value={mode}
              onChange={(e) => setMode(e.target.value)}
              className="px-3 py-2 bg-gray-100 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="hybrid">{t('settings.queryMode')}: Hybrid</option>
              <option value="local">Local</option>
              <option value="global">Global</option>
              <option value="mix">Mix</option>
              <option value="naive">Naive</option>
            </select>
          </div>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto max-w-4xl mx-auto w-full p-4">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center text-gray-400">
            <div className="text-center">
              <MessageCircle className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>{t('chat.noResults')}</p>
            </div>
          </div>
        ) : (
          messages.map((msg: Message) => (
            <div key={msg.id} className="mb-6">
              {/* Question */}
              <div className="flex justify-end mb-4">
                <div className="bg-blue-600 text-white rounded-lg px-4 py-3 max-w-md">
                  <p className="text-sm">{msg.question}</p>
                  <p className="text-xs text-blue-100 mt-1">
                    {new Date(msg.timestamp).toLocaleTimeString('zh-TW')}
                  </p>
                </div>
              </div>

              {/* Answer */}
              <div className="flex justify-start mb-4">
                <div className="bg-white border border-gray-200 rounded-lg px-4 py-3 max-w-2xl">
                  <p className="text-sm text-gray-900 whitespace-pre-wrap">{msg.answer}</p>

                  {/* Sources */}
                  {msg.sources && msg.sources.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-gray-200">
                      <p className="text-xs font-semibold text-gray-600 mb-2">{t('chat.sources')}:</p>
                      <div className="space-y-1">
                        {msg.sources.map((source, idx) => (
                          <a
                            key={idx}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-xs text-blue-600 hover:underline block truncate"
                            title={source.title}
                          >
                            {source.title}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-red-800">{error}</p>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="bg-white border-t border-gray-200 p-4">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('chat.placeholder')}
            disabled={loading}
            className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
          />
          <button
            type="submit"
            disabled={loading}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg flex items-center gap-2 transition-colors"
          >
            {loading ? (
              <Loader className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
            {t('buttons.submit')}
          </button>
        </form>
      </div>
    </div>
  )
}
