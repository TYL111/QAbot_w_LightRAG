import { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { FileText, Loader } from 'lucide-react'
import { fetchDocuments } from '../hooks/useQuery'

interface Document {
  id: string
  title: string
  url: string
  content_length: number
  chunks: number
  timestamp: string
}

export function DocumentBrowser() {
  const { t } = useTranslation()
  const [documents, setDocuments] = useState<Document[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadDocuments = async () => {
      try {
        const data = await fetchDocuments()
        setDocuments(data.documents || [])
      } catch (err: any) {
        setError(err.message || t('errors.apiError'))
      } finally {
        setLoading(false)
      }
    }

    loadDocuments()
  }, [t])

  return (
    <div className="max-w-6xl mx-auto p-4">
      <div className="mb-6">
        <div className="flex items-center gap-2 mb-2">
          <FileText className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold text-gray-900">{t('documents.title')}</h2>
        </div>
        <p className="text-gray-600">
          {t('documents.total')}: <span className="font-semibold">{documents.length}</span>
        </p>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Loader className="w-6 h-6 animate-spin text-gray-400" />
        </div>
      ) : documents.length === 0 ? (
        <div className="bg-gray-50 rounded-lg p-8 text-center">
          <p className="text-gray-600">{t('documents.noDocs')}</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr className="bg-gray-100 border-b border-gray-300">
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">{t('documents.column.title')}</th>
                <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">{t('documents.column.url')}</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">{t('documents.column.length')}</th>
                <th className="px-4 py-3 text-right text-sm font-semibold text-gray-900">{t('documents.column.chunks')}</th>
              </tr>
            </thead>
            <tbody>
              {documents.map((doc) => (
                <tr key={doc.id} className="border-b border-gray-200 hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm text-gray-900 truncate max-w-xs">{doc.title}</td>
                  <td className="px-4 py-3 text-sm">
                    <a
                      href={doc.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline truncate block max-w-xs"
                    >
                      {doc.url}
                    </a>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 text-right">{doc.content_length}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 text-right">{doc.chunks}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
