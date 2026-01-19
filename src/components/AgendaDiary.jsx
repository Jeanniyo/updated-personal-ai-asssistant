import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { Calendar, Book, Trash2, Edit2, Save, X, Paperclip, FileText } from 'lucide-react'
import FileUploader from './FileUploader'
import { auth } from '../utils/auth'

export default function AgendaDiary() {
    const [agenda, setAgenda] = useState([])
    const [diary, setDiary] = useState([])
    const [loading, setLoading] = useState(true)
    const [editingItem, setEditingItem] = useState(null) // { type: 'agenda'|'diary', id: ... }
    const [editContent, setEditContent] = useState('')
    const [editDate, setEditDate] = useState('')

    useEffect(() => {
        fetchData()
    }, [])

    const fetchData = async () => {
        try {
            const [agendaRes, diaryRes] = await Promise.all([
                axios.get('/api/agenda', { headers: auth.getAuthHeader() }),
                axios.get('/api/diary', { headers: auth.getAuthHeader() })
            ])
            setAgenda(agendaRes.data)
            setDiary(diaryRes.data)
        } catch (err) {
            console.error("Failed to fetch data", err)
        } finally {
            setLoading(false)
        }
    }

    const startEdit = (type, item) => {
        setEditingItem({ type, id: item.id })
        setEditContent(item.content)
        setEditDate(item.date || '')
    }

    const cancelEdit = () => {
        setEditingItem(null)
        setEditContent('')
        setEditDate('')
    }

    const handleUpdate = async () => {
        try {
            if (editingItem.type === 'agenda') {
                await axios.put('/api/agenda', { id: editingItem.id, content: editContent, date: editDate }, {
                    headers: auth.getAuthHeader()
                })
            } else {
                await axios.put('/api/diary', { id: editingItem.id, content: editContent }, {
                    headers: auth.getAuthHeader()
                })
            }
            await fetchData() // Refresh to get updated data
            cancelEdit()
        } catch (err) {
            console.error("Update failed", err)
        }
    }

    const handleDelete = async (type, id) => {
        if (!confirm("Are you sure you want to delete this item?")) return
        try {
            if (type === 'agenda') {
                await axios.delete('/api/agenda', {
                    data: { id },
                    headers: auth.getAuthHeader()
                })
                setAgenda(prev => prev.filter(item => item.id !== id))
            } else {
                await axios.delete('/api/diary', {
                    data: { id },
                    headers: auth.getAuthHeader()
                })
                setDiary(prev => prev.filter(item => item.id !== id))
            }
        } catch (err) {
            console.error("Delete failed", err)
        }
    }

    const handleAttachmentUpload = async (fileInfo, type, id) => {
        try {
            await axios.post('/api/attachment', {
                parent_type: type,
                parent_id: id,
                file_path: fileInfo.path,
                original_name: fileInfo.originalName,
                media_type: fileInfo.type
            }, {
                headers: auth.getAuthHeader()
            })
            fetchData() // Refresh to show new attachment
        } catch (err) {
            console.error("Attachment failed", err)
        }
    }

    const handleRemoveAttachment = async (attachId) => {
        try {
            await axios.delete('/api/files', {
                data: { id: attachId },
                headers: auth.getAuthHeader()
            })
            fetchData()
        } catch (err) {
            console.error("Delete attachment failed", err)
        }
    }

    if (loading) return (
        <div className="flex-1 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
        </div>
    )

    const itemVariants = {
        hidden: { opacity: 0, y: 10 },
        show: { opacity: 1, y: 0, transition: { duration: 0.2 } },
        exit: { opacity: 0, height: 0, marginBottom: 0, transition: { duration: 0.2 } }
    }

    const renderAttachments = (attachments, type, parentId) => (
        <div className="mt-3 flex flex-wrap gap-2">
            {attachments && attachments.map(att => (
                <div key={att.id} className="relative group/att">
                    {att.media_type && att.media_type.startsWith('image/') ? (
                        <div className="w-16 h-16 rounded overflow-hidden border border-white/20">
                            <img src={att.file_path} className="w-full h-full object-cover" alt="attachment" />
                        </div>
                    ) : (
                        <div className="flex items-center gap-1 bg-white/10 px-2 py-1 rounded text-xs border border-white/20">
                            <FileText size={12} />
                            <span className="max-w-[100px] truncate">{att.original_name}</span>
                        </div>
                    )}
                    <button
                        onClick={() => handleRemoveAttachment(att.id)}
                        className="absolute -top-1 -right-1 bg-red-500 rounded-full p-0.5 opacity-0 group-hover/att:opacity-100 transition-opacity"
                    >
                        <X size={10} className="text-white" />
                    </button>
                    <a href={att.file_path} target="_blank" rel="noopener noreferrer" className="absolute inset-0 bg-transparent" />
                </div>
            ))}
            <div className="relative">
                <FileUploader
                    label={<div className="p-1 hover:bg-white/10 rounded text-white/50 hover:text-white cursor-pointer"><Paperclip size={14} /></div>}
                    onUploadSuccess={(info) => handleAttachmentUpload(info, type, parentId)}
                />
            </div>
        </div>
    )

    return (
        <div className="flex-1 overflow-y-auto p-6 space-y-8 custom-scrollbar">
            <motion.section initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.1 } } }}>
                <div className="flex items-center gap-2 mb-4">
                    <Calendar className="text-purple-400" size={20} />
                    <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-purple-400 to-pink-400">Agenda</h2>
                </div>
                <div className="space-y-3">
                    <AnimatePresence>
                        {agenda.length === 0 ? <p className="text-white/30 italic">No agenda items yet.</p> : agenda.map((item) => (
                            <motion.div variants={itemVariants} initial="hidden" animate="show" exit="exit" key={item.id} className="bg-white/5 border border-white/10 p-4 rounded-xl backdrop-blur-sm hover:bg-white/10 transition-colors group relative">
                                {editingItem?.type === 'agenda' && editingItem.id === item.id ? (
                                    <div className="space-y-2">
                                        <textarea
                                            value={editContent}
                                            onChange={e => setEditContent(e.target.value)}
                                            className="w-full bg-black/20 border border-white/20 rounded p-2 text-white/90 focus:outline-none focus:border-purple-500"
                                        />
                                        <input
                                            type="text"
                                            value={editDate}
                                            onChange={e => setEditDate(e.target.value)}
                                            className="w-full bg-black/20 border border-white/20 rounded p-2 text-white/90 focus:outline-none focus:border-purple-500 text-sm"
                                            placeholder="Date/Time"
                                        />
                                        <div className="flex justify-end gap-2">
                                            <button onClick={handleUpdate} className="p-1 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30"><Save size={16} /></button>
                                            <button onClick={cancelEdit} className="p-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30"><X size={16} /></button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <div className="flex justify-between items-start pr-16">
                                            <span className="text-lg font-medium text-white/90 group-hover:text-white transition-colors">{item.content}</span>
                                            {item.date && <span className="text-xs bg-purple-500/20 text-purple-200 border border-purple-500/30 px-2 py-1 rounded-full whitespace-nowrap ml-2">{item.date}</span>}
                                        </div>

                                        {renderAttachments(item.attachments, 'agenda', item.id)}

                                        {item.timestamp && <div className="text-xs text-white/30 mt-2">{new Date(item.timestamp).toLocaleString()}</div>}

                                        <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => startEdit('agenda', item)} className="p-1.5 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-colors">
                                                <Edit2 size={16} />
                                            </button>
                                            <button onClick={() => handleDelete('agenda', item.id)} className="p-1.5 hover:bg-red-500/20 rounded-lg text-red-400/60 hover:text-red-400 transition-colors">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </motion.section>

            <motion.section initial="hidden" animate="show" variants={{ show: { transition: { staggerChildren: 0.1, delayChildren: 0.2 } } }}>
                <div className="flex items-center gap-2 mb-4">
                    <Book className="text-blue-400" size={20} />
                    <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-cyan-400">Diary</h2>
                </div>
                <div className="space-y-3">
                    <AnimatePresence>
                        {diary.length === 0 ? <p className="text-white/30 italic">No diary entries yet.</p> : diary.map((entry) => (
                            <motion.div variants={itemVariants} initial="hidden" animate="show" exit="exit" key={entry.id} className="bg-white/5 border border-white/10 p-4 rounded-xl backdrop-blur-sm hover:bg-white/10 transition-colors group relative">
                                {editingItem?.type === 'diary' && editingItem.id === entry.id ? (
                                    <div className="space-y-2">
                                        <textarea
                                            value={editContent}
                                            onChange={e => setEditContent(e.target.value)}
                                            className="w-full bg-black/20 border border-white/20 rounded p-2 text-white/90 focus:outline-none focus:border-purple-500 h-24"
                                        />
                                        <div className="flex justify-end gap-2">
                                            <button onClick={handleUpdate} className="p-1 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30"><Save size={16} /></button>
                                            <button onClick={cancelEdit} className="p-1 bg-red-500/20 text-red-400 rounded hover:bg-red-500/30"><X size={16} /></button>
                                        </div>
                                    </div>
                                ) : (
                                    <>
                                        <p className="text-white/80 leading-relaxed font-serif pr-16">{entry.content}</p>

                                        {renderAttachments(entry.attachments, 'diary', entry.id)}

                                        {entry.timestamp && <div className="text-xs text-white/30 mt-3 text-right italic">{new Date(entry.timestamp).toLocaleString()}</div>}

                                        <div className="absolute top-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                            <button onClick={() => startEdit('diary', entry)} className="p-1.5 hover:bg-white/10 rounded-lg text-white/60 hover:text-white transition-colors">
                                                <Edit2 size={16} />
                                            </button>
                                            <button onClick={() => handleDelete('diary', entry.id)} className="p-1.5 hover:bg-red-500/20 rounded-lg text-red-400/60 hover:text-red-400 transition-colors">
                                                <Trash2 size={16} />
                                            </button>
                                        </div>
                                    </>
                                )}
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            </motion.section>
        </div>
    )
}
