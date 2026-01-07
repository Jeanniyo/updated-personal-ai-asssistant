import { useState, useRef } from 'react';

const FileUploader = ({ onUploadSuccess, label = "Upload File" }) => {
    const [uploading, setUploading] = useState(false);
    const fileInputRef = useRef(null);

    const handleFileChange = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setUploading(true);
        const reader = new FileReader();
        reader.onloadend = async () => {
            const base64String = reader.result;

            try {
                const response = await fetch('/api/upload', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        name: file.name,
                        file_data: base64String
                    }),
                });

                if (response.ok) {
                    const data = await response.json();
                    onUploadSuccess({
                        path: data.path,
                        originalName: file.name,
                        type: file.type
                    });
                } else {
                    console.error('Upload failed');
                    alert('Upload failed');
                }
            } catch (error) {
                console.error('Error uploading:', error);
                alert('Error uploading file');
            } finally {
                setUploading(false);
                if (fileInputRef.current) {
                    fileInputRef.current.value = '';
                }
            }
        };
        reader.readAsDataURL(file);
    };

    return (
        <div>
            <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileChange}
                style={{ display: 'none' }}
                id="file-upload"
            />
            <label htmlFor="file-upload" className={`cursor-pointer inline-flex items-center px-4 py-2 bg-white/10 hover:bg-white/20 rounded-lg transition-colors text-sm ${uploading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <span className="mr-2">📎</span>
                {uploading ? 'Uploading...' : label}
            </label>
        </div>
    );
};

export default FileUploader;
