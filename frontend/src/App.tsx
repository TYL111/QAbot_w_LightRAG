import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { MessageCircle, FileText, Settings as SettingsIcon } from 'lucide-react'
import { ChatInterface } from './components/ChatInterface'
import { DocumentBrowser } from './components/DocumentBrowser'
import { Settings } from './components/Settings'

type Tab = 'chat' | 'documents' | 'settings'

function App() {
  const { t } = useTranslation()
  const [activeTab, setActiveTab] = useState<Tab>('chat')

  const tabs: Array<{ id: Tab; label: string; icon: React.ReactNode }> = [
    { id: 'chat', label: t('nav.chat'), icon: <MessageCircle className="w-5 h-5" /> },
    { id: 'documents', label: t('nav.documents'), icon: <FileText className="w-5 h-5" /> },
    { id: 'settings', label: t('nav.settings'), icon: <SettingsIcon className="w-5 h-5" /> },
  ]

  return (
    <div className="h-screen bg-gray-50 flex flex-col">
      {/* Navigation */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto">
          <div className="flex">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-6 py-4 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.id
                    ? 'text-blue-600 border-blue-600'
                    : 'text-gray-600 border-transparent hover:text-gray-900 hover:border-gray-300'
                }`}
              >
                {tab.icon}
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {activeTab === 'chat' && <ChatInterface />}
        {activeTab === 'documents' && <DocumentBrowser />}
        {activeTab === 'settings' && <Settings />}
      </div>
    </div>
  )
}

export default App
