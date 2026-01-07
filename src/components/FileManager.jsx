import { useState, useEffect } from 'react'
import axios from 'axios'
import { motion, AnimatePresence } from 'framer-motion'
import { FolderOpen, FileText, Trash2, X, Image as ImageIcon } from 'lucide-react'

export default function FileManager() {
    const [files, setFiles] = useState([])
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchFiles()
    }, [])

    const fetchFiles = async () => {
        try {
            const res = await axios.get('/api/files')
            setFiles(res.data)
        } catch (err) {
            console.error("Failed to fetch files", err)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async (id) => {
        if (!confirm("Are you sure you want to delete this file? This cannot be undone.")) return
        try {
            await axios.delete('/api/files', { data: { id } })
            setFiles(prev => prev.filter(f => f.id !== id))
        } catch (err) {
            console.error("Failed to delete file", err)
        }
    }

    if (loading) return (
        <div className="flex-1 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-purple-500/30 border-t-purple-500 rounded-full animate-spin"></div>
        </div>
    )

    return (
        <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
            <div className="flex items-center gap-2 mb-4">
                <FolderOpen className="text-yellow-400" size={20} />
                <h2 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-yellow-400 to-orange-400">File Manager</h2>
            </div>

            {files.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-[50vh] text-white/30 space-y-4">
                    <FolderOpen size={48} />
                    <p>No files uploaded yet.</p>
                </div>
            ) : (
                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    <AnimatePresence>
                        {files.map(file => (
                            <motion.div
                                key={file.id}
                                layout
                                initial={{ opacity: 0, scale: 0.9 }}
                                animate={{ opacity: 1, scale: 1 }}
                                exit={{ opacity: 0, scale: 0.9 }}
                                className="bg-white/5 border border-white/10 rounded-xl overflow-hidden group hover:bg-white/10 transition-colors relative"
                            >
                                <div className="aspect-square bg-black/20 flex items-center justify-center relative overflow-hidden">
                                    {file.media_type && file.media_type.startsWith('image/') ? (
                                        <img src={file.file_path} alt={file.original_name} className="w-full h-full object-cover" />
                                    ) : (
                                        <FileText size={48} className="text-white/20" />
                                    )}
                                    <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
                                        <a
                                            href={file.file_path}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="p-2 bg-white/10 rounded-full text-white hover:bg-white/20"
                                            title="View"
                                        >
                                            <ImageIcon size={16} />
                                        </a>
                                        <button
                                            onClick={() => handleDelete(file.id)}
                                            className="p-2 bg-red-500/20 rounded-full text-red-400 hover:bg-red-500/30"
                                            title="Delete"
                                        >
                                            <Trash2 size={16} />
                                        </button>
                                    </div>
                                </div>
                                <div className="p-3">
                                    <p className="text-sm text-white/90 truncate font-medium" title={file.original_name}>{file.original_name}</p>
                                    <p className="text-xs text-white/40 mt-1">{new Date(file.timestamp).toLocaleDateString()}</p>
                                </div>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                </div>
            )}
        </div>
    )
}
