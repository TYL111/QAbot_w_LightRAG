import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Settings as SettingsIcon, Loader, CheckCircle, AlertCircle } from 'lucide-react'
import { fetchStatus, fetchRefreshStatus, fetchScrapeStatus, pauseScrape, resumeScrape, triggerScrape, triggerRefresh } from '../hooks/useQuery'

interface Status {
  initialized: boolean
  working_dir: string
  workspace: string
}

export function Settings() {
  const { t } = useTranslation()
  const [status, setStatus] = useState<Status | null>(null)
  const [loading, setLoading] = useState(true)
  const [scrapeLoading, setScrapeLoading] = useState(false)
  const [refreshLoading, setRefreshLoading] = useState(false)
  const [scrapeProgress, setScrapeProgress] = useState<{ running: boolean; paused: boolean; progress: number | null; processed: number; saved: number; pending: number; max_pages: number | null }>({
    running: false,
    paused: false,
    progress: 0,
    processed: 0,
    saved: 0,
    pending: 0,
    max_pages: null,
  })
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    const loadStatus = async () => {
      try {
        const data = await fetchStatus()
        setStatus(data)
      } catch (err) {
        setMessage({ type: 'error', text: t('errors.apiError') })
      } finally {
        setLoading(false)
      }
    }

    loadStatus()
  }, [t])

  useEffect(() => {
    if (!scrapeLoading) return

    const poll = async () => {
      try {
        const data = await fetchScrapeStatus()
        setScrapeProgress(data)
        if (!data.running) {
          setScrapeLoading(false)
          setMessage(data.error
            ? { type: 'error', text: data.error }
            : { type: 'success', text: `爬取完成，共儲存 ${data.saved} 頁` })
        }
      } catch (err) {
        setScrapeLoading(false)
        setMessage({ type: 'error', text: '無法取得爬蟲進度' })
      }
    }

    poll()
    const timer = window.setInterval(poll, 1000)
    return () => window.clearInterval(timer)
  }, [scrapeLoading])

  useEffect(() => {
    if (!refreshLoading) return

    const poll = async () => {
      try {
        const data = await fetchRefreshStatus()
        if (!data.running) {
          setRefreshLoading(false)
          setMessage(data.error
            ? { type: 'error', text: data.error }
            : { type: 'success', text: '資料重新整理完成' })
        }
      } catch (err) {
        setRefreshLoading(false)
        setMessage({ type: 'error', text: '無法取得重新整理狀態' })
      }
    }

    poll()
    const timer = window.setInterval(poll, 1000)
    return () => window.clearInterval(timer)
  }, [refreshLoading])

  const handleScrape = async () => {
    setScrapeLoading(true)
    try {
      await triggerScrape()
      setMessage({ type: 'success', text: '開始爬取網站...' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '爬取失敗' })
    }
  }

  const handleRefresh = async () => {
    setRefreshLoading(true)
    try {
      await triggerRefresh()
      setMessage({ type: 'success', text: '開始重新整理數據...' })
    } catch (err: any) {
      setMessage({ type: 'error', text: err.message || '重新整理失敗' })
    }
  }

  const handlePauseToggle = async () => {
    try {
      if (scrapeProgress.paused) {
        await resumeScrape()
      } else {
        await pauseScrape()
      }
      const data = await fetchScrapeStatus()
      setScrapeProgress(data)
    } catch (err: any) {
      setMessage({ type: 'error', text: err.response?.data?.detail || err.message || '無法切換爬取狀態' })
    }
  }

  return (
    <div className="max-w-2xl mx-auto p-4">
      <div className="flex items-center gap-2 mb-6">
        <SettingsIcon className="w-6 h-6 text-blue-600" />
        <h2 className="text-2xl font-bold text-gray-900">{t('settings.title')}</h2>
      </div>

      {message && (
        <div className={`rounded-lg p-4 mb-6 flex items-center gap-2 ${
          message.type === 'success'
            ? 'bg-green-50 border border-green-200 text-green-800'
            : 'bg-red-50 border border-red-200 text-red-800'
        }`}>
          {message.type === 'success' ? (
            <CheckCircle className="w-5 h-5" />
          ) : (
            <AlertCircle className="w-5 h-5" />
          )}
          <p className="text-sm">{message.text}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : status ? (
        <div className="space-y-6">
          {/* Status */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('settings.status')}</h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">初始化狀態</span>
                <span className="flex items-center gap-2">
                  {status.initialized ? (
                    <CheckCircle className="w-5 h-5 text-green-600" />
                  ) : (
                    <AlertCircle className="w-5 h-5 text-red-600" />
                  )}
                  <span className="font-semibold">
                    {status.initialized ? t('status.initialized') : t('status.notInitialized')}
                  </span>
                </span>
              </div>
              <div>
                <span className="text-gray-600">工作目錄</span>
                <p className="font-mono text-sm text-gray-700 mt-1 bg-gray-50 p-2 rounded">
                  {status.working_dir}
                </p>
              </div>
              <div>
                <span className="text-gray-600">工作區</span>
                <p className="font-mono text-sm text-gray-700 mt-1 bg-gray-50 p-2 rounded">
                  {status.workspace}
                </p>
              </div>
            </div>
          </div>

          {/* Data Management */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">數據管理</h3>
            <div className="space-y-3">
              <button
                onClick={handleScrape}
                disabled={scrapeLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                {scrapeLoading ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : null}
                {t('buttons.scrape')}
              </button>

              {scrapeLoading && (
                <div className="space-y-2" aria-live="polite">
                  <button
                    onClick={handlePauseToggle}
                    className="w-full border border-blue-600 text-blue-700 px-4 py-2 rounded-lg hover:bg-blue-50"
                  >
                    {scrapeProgress.paused ? '繼續爬取' : '暫停爬取'}
                  </button>
                  <div className="flex justify-between text-sm text-gray-600">
                    <span>爬取進度</span>
                    <span>
                      {scrapeProgress.progress === null
                        ? `${scrapeProgress.saved} 頁已完成`
                        : `${scrapeProgress.progress}%`}
                    </span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className={`h-full bg-blue-600 transition-all duration-500 ${scrapeProgress.progress === null ? 'animate-pulse w-1/2' : ''}`}
                      style={scrapeProgress.progress === null ? undefined : { width: `${scrapeProgress.progress}%` }}
                    />
                  </div>
                  <p className="text-xs text-gray-500">
                    已處理 {scrapeProgress.processed} 頁，佇列中 {scrapeProgress.pending} 頁
                  </p>
                </div>
              )}

              <button
                onClick={handleRefresh}
                disabled={refreshLoading}
                className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white px-6 py-3 rounded-lg flex items-center justify-center gap-2 transition-colors"
              >
                {refreshLoading ? (
                  <Loader className="w-4 h-4 animate-spin" />
                ) : null}
                {t('buttons.refresh')}
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-red-800">
          {message?.text || '無法載入設定狀態'}
        </div>
      )}
    </div>
  )
}
