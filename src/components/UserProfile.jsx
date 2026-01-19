import { useState, useEffect } from 'react'
import { User, Upload, Edit2, Check, X } from 'lucide-react'
import axios from 'axios'
import FileUploader from './FileUploader'
import { auth } from '../utils/auth'

export default function UserProfile({ currentUser }) {
    const [profile, setProfile] = useState({ name: 'User', photo_path: null })
    const [isEditing, setIsEditing] = useState(false)
    const [editName, setEditName] = useState('')
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchProfile()
    }, [])

    const fetchProfile = async () => {
        try {
            const res = await axios.get('/api/profile', {
                headers: auth.getAuthHeader()
            })
            setProfile(res.data)
            setEditName(res.data.name)
        } catch (err) {
            console.error("Failed to fetch profile", err)
        } finally {
            setLoading(false)
        }
    }

    const handleSaveProfile = async () => {
        try {
            await axios.post('/api/profile', {
                name: editName,
                photo_path: profile.photo_path
            }, {
                headers: auth.getAuthHeader()
            })
            setProfile(prev => ({ ...prev, name: editName }))
            setIsEditing(false)
        } catch (err) {
            console.error("Failed to update profile", err)
        }
    }

    const handlePhotoUpload = async (fileInfo) => {
        try {
            await axios.post('/api/profile', {
                name: profile.name,
                photo_path: fileInfo.path
            }, {
                headers: auth.getAuthHeader()
            })
            setProfile(prev => ({ ...prev, photo_path: fileInfo.path }))
        } catch (err) {
            console.error("Failed to update profile photo", err)
        }
    }

    if (loading) return null

    return (
        <div className="flex flex-col items-center space-y-4">
            <div className="relative group cursor-pointer">
                <div className="w-24 h-24 rounded-full bg-gradient-to-tr from-purple-500 to-blue-500 p-1 shadow-lg shadow-purple-500/20">
                    <div className="w-full h-full rounded-full bg-black/40 overflow-hidden flex items-center justify-center backdrop-blur-md relative">
                        {profile.photo_path ? (
                            <img src={profile.photo_path} alt="Profile" className="w-full h-full object-cover" />
                        ) : (
                            <User size={48} className="text-white/80" />
                        )}

                        {/* Overlay for upload */}
                        <div className="absolute inset-0 bg-black/60 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity backdrop-blur-sm">
                            <div className="pointer-events-auto">
                                <FileUploader
                                    label={<Upload size={24} className="text-white" />}
                                    onUploadSuccess={handlePhotoUpload}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <div className="text-center w-full relative">
                {isEditing ? (
                    <div className="flex items-center justify-center gap-2">
                        <input
                            type="text"
                            value={editName}
                            onChange={(e) => setEditName(e.target.value)}
                            className="bg-white/10 border border-white/20 rounded px-2 py-1 text-white text-center w-32 focus:outline-none focus:border-purple-500"
                            autoFocus
                        />
                        <button onClick={handleSaveProfile} className="p-1 hover:bg-green-500/20 rounded-full text-green-400">
                            <Check size={16} />
                        </button>
                        <button onClick={() => { setIsEditing(false); setEditName(profile.name); }} className="p-1 hover:bg-red-500/20 rounded-full text-red-400">
                            <X size={16} />
                        </button>
                    </div>
                ) : (
                    <div className="flex items-center justify-center gap-2 group/name">
                        <h3 className="text-xl font-bold text-white tracking-wide">{profile.name}</h3>
                        <button
                            onClick={() => setIsEditing(true)}
                            className="opacity-0 group-hover/name:opacity-100 transition-opacity p-1 hover:bg-white/10 rounded-full text-white/50 hover:text-white"
                        >
                            <Edit2 size={12} />
                        </button>
                    </div>
                )}
                <p className="text-xs text-purple-300/70 font-medium uppercase tracking-wider mt-1">Personal Assistant</p>
            </div>
        </div>
    )
}
