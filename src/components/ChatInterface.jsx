import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, Mic, MicOff, Volume2, VolumeX } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import axios from 'axios'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { auth } from '../utils/auth'

export default function ChatInterface() {
    const [messages, setMessages] = useState([
        { role: 'assistant', content: 'Hello! I am your personal assistant. How can I help you today?' }
    ])
    const [input, setInput] = useState('')
    const [loading, setLoading] = useState(false)
    const [isListening, setIsListening] = useState(false)
    const [isMuted, setIsMuted] = useState(false)
    const messagesEndRef = useRef(null)
    const recognitionRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
    }


    // --- Voice Setup ---
    useEffect(() => {
        // Load voices when they become available
        const loadVoices = () => {
            const voices = window.speechSynthesis.getVoices()
            if (voices.length > 0) {
                console.log('Available voices:', voices.map(v => v.name))
            }
        }

        if ('speechSynthesis' in window) {
            loadVoices()
            window.speechSynthesis.onvoiceschanged = loadVoices
        }

        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
            recognitionRef.current = new SpeechRecognition()
            recognitionRef.current.continuous = false
            recognitionRef.current.interimResults = true
            recognitionRef.current.lang = 'en-US'
            recognitionRef.current.maxAlternatives = 1

            recognitionRef.current.onresult = (event) => {
                const transcript = event.results[event.results.length - 1][0].transcript

                // Update input field with interim results
                if (event.results[event.results.length - 1].isFinal) {
                    setInput(transcript)
                    // Don't auto-send, let user review and send manually
                } else {
                    setInput(transcript)
                }
            }

            recognitionRef.current.onerror = (event) => {
                console.error('Speech recognition error:', event.error)
                setIsListening(false)

                if (event.error === 'no-speech') {
                    console.log('No speech detected, try again')
                } else if (event.error === 'network') {
                    alert('Network error. Please check your connection.')
                }
            }

            recognitionRef.current.onend = () => {
                setIsListening(false)
            }
        }
    }, [])

    const toggleListening = () => {
        if (isListening) {
            recognitionRef.current?.stop()
            setIsListening(false)
        } else {
            try {
                recognitionRef.current?.start()
                setIsListening(true)
            } catch (error) {
                console.error('Failed to start recognition:', error)
                alert('Microphone access denied or unavailable')
            }
        }
    }

    const speak = (text) => {
        if (isMuted || !('speechSynthesis' in window)) return

        // Cancel any current speech
        window.speechSynthesis.cancel()

        const utterance = new SpeechSynthesisUtterance(text)

        // Select the best natural-sounding voice
        const voices = window.speechSynthesis.getVoices()

        // Priority order for natural voices
        const preferredVoices = [
            'Google US English',
            'Microsoft Zira - English (United States)',
            'Samantha',
            'Karen',
            'Google UK English Female',
            'Microsoft David - English (United States)',
            'Alex'
        ]

        let selectedVoice = null
        for (const preferred of preferredVoices) {
            selectedVoice = voices.find(v => v.name === preferred)
            if (selectedVoice) break
        }

        // Fallback to any English female voice
        if (!selectedVoice) {
            selectedVoice = voices.find(v =>
                v.lang.startsWith('en') && v.name.toLowerCase().includes('female')
            )
        }

        // Final fallback to any English voice
        if (!selectedVoice) {
            selectedVoice = voices.find(v => v.lang.startsWith('en'))
        }

        if (selectedVoice) {
            utterance.voice = selectedVoice
        }

        // Natural speech settings
        utterance.pitch = 1.0
        utterance.rate = 0.95  // Slightly slower for clarity
        utterance.volume = 1.0

        window.speechSynthesis.speak(utterance)
    }
    // -------------------

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const res = await axios.get('/api/chat/history', {
                    headers: auth.getAuthHeader()
                })
                if (res.data && res.data.length > 0) {
                    setMessages(res.data)
                }
            } catch (error) {
                console.error("Failed to fetch history", error)
            }
        }
        fetchHistory()
    }, [])

    useEffect(() => {
        scrollToBottom()
    }, [messages])

    const handleSend = async (e, forcedInput = null) => {
        if (e) e.preventDefault()
        const messageContent = forcedInput || input
        if (!messageContent.trim()) return

        const userMsg = { role: 'user', content: messageContent }
        setMessages(prev => [...prev, userMsg])
        setInput('')
        setLoading(true)

        try {
            const res = await axios.post('/api/chat', { message: userMsg.content }, {
                headers: auth.getAuthHeader()
            })
            const botMsg = { role: 'assistant', content: res.data.reply }
            setMessages(prev => [...prev, botMsg])
            speak(botMsg.content) // Speak the response
        } catch (error) {
            console.error(error)
            setMessages(prev => [...prev, { role: 'assistant', content: 'Sorry, I encountered an error.' }])
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex-1 flex flex-col h-full relative">
            {/* Volume Toggle */}
            <div className="absolute top-4 right-6 z-10">
                <button
                    onClick={() => setIsMuted(!isMuted)}
                    className="p-2 text-white/50 hover:text-white transition-colors"
                >
                    {isMuted ? <VolumeX size={20} /> : <Volume2 size={20} />}
                </button>
            </div>

            <div className="flex-1 overflow-y-auto p-6 space-y-4">
                <AnimatePresence>
                    {messages.map((msg, idx) => (
                        <motion.div
                            key={idx}
                            initial={{ opacity: 0, y: 20 }}
                            animate={{ opacity: 1, y: 0 }}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div className={`max-w-[85%] p-4 rounded-2xl flex items-start gap-3 ${msg.role === 'user' ? 'bg-purple-600/50 rounded-tr-none text-white' : 'bg-white/10 rounded-tl-none text-white/90'
                                } backdrop-blur-sm border border-white/5 shadow-xl`}>
                                <div className={`p-2 rounded-full shrink-0 ${msg.role === 'user' ? 'bg-purple-400/20' : 'bg-blue-400/20'}`}>
                                    {msg.role === 'user' ? <User size={16} /> : <Bot size={16} />}
                                </div>
                                <div className="min-w-0 flex-1 overflow-hidden">
                                    <ReactMarkdown
                                        remarkPlugins={[remarkGfm]}
                                        className="prose prose-invert prose-sm max-w-none break-words"
                                        components={{
                                            code({ node, inline, className, children, ...props }) {
                                                const match = /language-(\w+)/.exec(className || '')
                                                return !inline && match ? (
                                                    <div className="rounded-md overflow-hidden my-2 border border-white/10">
                                                        <div className="bg-white/10 px-3 py-1 text-xs text-white/50 flex justify-between items-center bg-black/30">
                                                            <span>{match[1]}</span>
                                                        </div>
                                                        <SyntaxHighlighter
                                                            style={vscDarkPlus}
                                                            language={match[1]}
                                                            PreTag="div"
                                                            customStyle={{ margin: 0, borderRadius: 0, background: 'rgba(0,0,0,0.3)' }}
                                                            {...props}
                                                        >
                                                            {String(children).replace(/\n$/, '')}
                                                        </SyntaxHighlighter>
                                                    </div>
                                                ) : (
                                                    <code className={`${className} bg-white/10 rounded px-1 py-0.5 before:content-[''] after:content-['']`} {...props}>
                                                        {children}
                                                    </code>
                                                )
                                            }
                                        }}
                                    >
                                        {msg.content}
                                    </ReactMarkdown>
                                </div>
                            </div>
                        </motion.div>
                    ))}
                    {loading && (
                        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="flex justify-start">
                            <div className="bg-white/10 p-4 rounded-2xl rounded-tl-none flex items-center gap-2">
                                <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce"></div>
                                <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce delay-100"></div>
                                <div className="w-2 h-2 bg-white/50 rounded-full animate-bounce delay-200"></div>
                            </div>
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={messagesEndRef} />
            </div>

            <form onSubmit={(e) => handleSend(e)} className="p-4 border-t border-white/10 flex gap-2 items-center">
                <button
                    type="button"
                    onClick={toggleListening}
                    className={`glass-button transition-all duration-300 ${isListening ? 'bg-red-500/50 border-red-400 text-white animate-pulse' : ''}`}
                >
                    {isListening ? <MicOff size={20} /> : <Mic size={20} />}
                </button>

                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder={isListening ? "Listening..." : "Type a message..."}
                    className="glass-input flex-1"
                />

                <button type="submit" className="glass-button" disabled={loading}>
                    <Send size={20} />
                </button>
            </form>
        </div>
    )
}
