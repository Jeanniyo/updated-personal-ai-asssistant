import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion } from 'framer-motion'
import { Lightbulb, RefreshCw } from 'lucide-react'
import { auth } from '../utils/auth'

export default function DailyTip() {
    const [tip, setTip] = useState(null)
    const [loading, setLoading] = useState(true)
    const [refreshing, setRefreshing] = useState(false)

    useEffect(() => {
        fetchTip()
    }, [])

    const fetchTip = async () => {
        try {
            const res = await axios.get('/api/daily-tip', {
                headers: auth.getAuthHeader()
            })
            setTip(res.data)
        } catch (err) {
            console.error("Failed to fetch daily tip", err)
            // Don't crash the app if tip fails to load
            setTip(null)
        } finally {
            setLoading(false)
        }
    }

    const generateNewTip = async () => {
        setRefreshing(true)
        try {
            const res = await axios.post('/api/daily-tip/generate', {}, {
                headers: auth.getAuthHeader()
            })
            setTip(res.data)
        } catch (err) {
            console.error("Failed to generate tip", err)
            alert("Failed to generate tip. Please try again.")
        } finally {
            setRefreshing(false)
        }
    }

    if (loading) return null
    if (!tip) return null // Don't render if no tip available

    return (
        <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mt-6 p-4 bg-gradient-to-br from-purple-500/20 to-blue-500/20 rounded-xl border border-white/10 backdrop-blur-sm"
        >
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Lightbulb size={16} className="text-yellow-400" />
                    <h4 className="text-sm font-semibold text-white">Daily Tip</h4>
                </div>
                <button
                    onClick={generateNewTip}
                    disabled={refreshing}
                    className="p-1 hover:bg-white/10 rounded-full transition-colors disabled:opacity-50"
                    title="Get new tip"
                >
                    <RefreshCw size={14} className={`text-white/70 ${refreshing ? 'animate-spin' : ''}`} />
                </button>
            </div>

            {tip && (
                <div>
                    <p className="text-xs text-purple-300/80 mb-1 font-medium">{tip.category}</p>
                    <p className="text-sm text-white/90 leading-relaxed">{tip.content}</p>
                </div>
            )}
        </motion.div>
    )
}
