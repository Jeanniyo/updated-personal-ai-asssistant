import { useState, useEffect } from 'react'
import ChatInterface from './components/ChatInterface'
import UserProfile from './components/UserProfile'
import AgendaDiary from './components/AgendaDiary'
import FileManager from './components/FileManager'
import DailyTip from './components/DailyTip'
import AuthForm from './components/AuthForm'
import { auth } from './utils/auth'
import './index.css'

function App() {
  const [activeTab, setActiveTab] = useState('chat')
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Check if user is already authenticated
    const checkAuth = async () => {
      if (auth.isAuthenticated()) {
        const isValid = await auth.verifyToken()
        if (isValid) {
          setIsAuthenticated(true)
          setCurrentUser(auth.getUser())
        } else {
          auth.logout()
        }
      }
      setLoading(false)
    }
    checkAuth()
  }, [])

  const handleAuthSuccess = (user) => {
    setIsAuthenticated(true)
    setCurrentUser(user)
  }

  const handleLogout = () => {
    auth.logout()
    setIsAuthenticated(false)
    setCurrentUser(null)
    setActiveTab('chat')
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-black">
        <div className="text-white text-xl">Loading...</div>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <AuthForm onAuthSuccess={handleAuthSuccess} />
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-4 md:p-8 bg-black">
      {/* Background blobs for visual interest */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-0 w-[500px] h-[500px] bg-purple-600 rounded-full mix-blend-screen filter blur-[100px] opacity-20 animate-blob"></div>
        <div className="absolute bottom-0 right-0 w-[500px] h-[500px] bg-blue-600 rounded-full mix-blend-screen filter blur-[100px] opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-32 left-32 w-[400px] h-[400px] bg-pink-600 rounded-full mix-blend-screen filter blur-[100px] opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="container max-w-6xl w-full h-[85vh] glass-panel flex overflow-hidden relative z-10 text-white">

        {/* Sidebar */}
        <div className="w-1/3 min-w-[250px] border-r border-white/10 p-6 flex flex-col glass-sidebar bg-white/5">
          <UserProfile currentUser={currentUser} />
          <DailyTip />
          <nav className="mt-8 flex-1 space-y-2">
            <button onClick={() => setActiveTab('chat')} className={`w-full text-left p-3 rounded-lg transition-all ${activeTab === 'chat' ? 'bg-white/10 text-white font-medium' : 'hover:bg-white/5 text-white/70'}`}>
              Chat Assistant
            </button>
            <button onClick={() => setActiveTab('agenda')} className={`w-full text-left p-3 rounded-lg transition-all ${activeTab === 'agenda' ? 'bg-white/10 text-white font-medium' : 'hover:bg-white/5 text-white/70'}`}>
              Agenda & Diary
            </button>
            <button onClick={() => setActiveTab('files')} className={`w-full text-left p-3 rounded-lg transition-all ${activeTab === 'files' ? 'bg-white/10 text-white font-medium' : 'hover:bg-white/5 text-white/70'}`}>
              File Manager
            </button>
          </nav>

          {/* Logout button */}
          <button
            onClick={handleLogout}
            className="mt-4 w-full p-3 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-200 transition-all border border-red-500/30"
          >
            Logout
          </button>
        </div>

        {/* Main Content */}
        <div className="flex-1 flex flex-col relative bg-black/20">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'agenda' && <AgendaDiary />}
          {activeTab === 'files' && <FileManager />}
        </div>
      </div>
    </div>
  )
}

export default App
