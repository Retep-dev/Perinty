import React, { useState, useRef, useEffect } from 'react'
import { Upload, FileText, CheckCircle, AlertCircle, RefreshCw, Trash2 } from 'lucide-react'

export default function DocumentUploader({
  backendUrl,
  userId,
  activeDocument,
  onSelectDocument,
  onUploadSuccess,
  onClearAll,
}) {
  const [dragActive, setDragActive] = useState(false)
  const [file, setFile] = useState(null)
  const [status, setStatus] = useState('idle') // idle, uploading, success, error
  const [message, setMessage] = useState('')
  const [documents, setDocuments] = useState([])
  const [loadingDocs, setLoadingDocs] = useState(false)
  const fileInputRef = useRef(null)

  const validExtensions = ['.txt', '.md', '.json', '.pdf', '.docx', '.html', '.htm', '.csv']

  useEffect(() => {
    fetchDocuments()
  }, [backendUrl, userId])

  const fetchDocuments = async () => {
    setLoadingDocs(true)
    try {
      const url = userId
        ? `${backendUrl}/documents?user_id=${encodeURIComponent(userId)}`
        : `${backendUrl}/documents`

      const response = await fetch(url, {
        headers: {
          'X-User-ID': userId || '',
        },
      })
      if (response.ok) {
        const data = await response.json()
        const fetchedDocs = data.documents || []
        setDocuments(fetchedDocs)
        // Automatically select the latest uploaded document if none selected
        if (!activeDocument && fetchedDocs.length > 0 && onSelectDocument) {
          onSelectDocument(fetchedDocs[0].file_name)
        }
      }
    } catch (err) {
      console.error('Failed to fetch documents', err)
    } finally {
      setLoadingDocs(false)
    }
  }

  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = async (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      uploadFile(e.dataTransfer.files[0])
    }
  }

  const handleFileInput = (e) => {
    if (e.target.files && e.target.files[0]) {
      uploadFile(e.target.files[0])
    }
  }

  const uploadFile = async (selectedFile) => {
    const fileExtension = selectedFile.name.substring(selectedFile.name.lastIndexOf('.')).toLowerCase()

    if (!validExtensions.includes(fileExtension)) {
      setStatus('error')
      setMessage(`Unsupported file type. Please upload: ${validExtensions.join(', ')}`)
      return
    }

    setFile(selectedFile)
    setStatus('uploading')
    setMessage('Parsing & indexing document...')

    const formData = new FormData()
    formData.append('file', selectedFile)
    if (userId) {
      formData.append('user_id', userId)
    }

    try {
      const response = await fetch(`${backendUrl}/upload`, {
        method: 'POST',
        headers: {
          'X-User-ID': userId || '',
        },
        body: formData,
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setMessage(`Success! Created ${data.chunks_created} context chunks in ${data.storage}.`)
        if (onSelectDocument) onSelectDocument(selectedFile.name)
        if (onUploadSuccess) onUploadSuccess(selectedFile.name)
        await fetchDocuments()
      } else {
        setStatus('error')
        setMessage(data.detail || 'Upload failed.')
      }
    } catch (err) {
      console.error(err)
      setStatus('error')
      setMessage('Failed to reach backend server. Make sure it is running.')
    }
  }

  const handleDeleteDocument = async (e, fileName) => {
    e.stopPropagation()
    if (!confirm(`Delete "${fileName}" and all its chunks?`)) return

    try {
      const url = userId
        ? `${backendUrl}/documents/${encodeURIComponent(fileName)}?user_id=${encodeURIComponent(userId)}`
        : `${backendUrl}/documents/${encodeURIComponent(fileName)}`

      const response = await fetch(url, {
        method: 'DELETE',
        headers: {
          'X-User-ID': userId || '',
        },
      })
      const data = await response.json()
      if (response.ok) {
        if (activeDocument === fileName && onSelectDocument) {
          onSelectDocument(null)
        }
        await fetchDocuments()
      } else {
        alert(data.detail || 'Failed to delete document.')
      }
    } catch (err) {
      console.error(err)
      alert('Error connecting to backend server.')
    }
  }

  const triggerFileInput = () => {
    fileInputRef.current.click()
  }

  return (
    <div className="glass p-5 sm:p-6 flex flex-col gap-4 min-w-0">
      <div className="flex justify-between items-center min-w-0 gap-2">
        <h2 className="text-base sm:text-lg font-semibold font-outfit text-slate-100 flex items-center gap-2 truncate">
          <FileText size={20} className="text-indigo-400 shrink-0" />
          Knowledge Source
        </h2>

        <button
          onClick={onClearAll}
          id="btn-clear-db"
          className="text-xs text-slate-400 hover:text-rose-400 border border-slate-700 hover:border-rose-950 px-2 py-1 rounded transition-all duration-200 bg-slate-900/50 shrink-0"
        >
          Reset Store
        </button>
      </div>

      <div
        className={`border-2 border-dashed rounded-xl p-8 text-center flex flex-col items-center justify-center gap-3 cursor-pointer transition-all duration-300 ${
          dragActive
            ? 'border-indigo-400 bg-indigo-500/10'
            : 'border-slate-800 hover:border-slate-700 bg-slate-950/20'
        }`}
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={triggerFileInput}
        id="uploader-dropzone"
      >
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          onChange={handleFileInput}
          accept={validExtensions.join(',')}
        />

        {status === 'uploading' ? (
          <div className="flex flex-col items-center gap-2">
            <RefreshCw className="animate-spin text-indigo-400" size={36} />
            <p className="text-slate-300 font-medium text-sm mt-2">{message}</p>
          </div>
        ) : status === 'success' ? (
          <div className="flex flex-col items-center gap-2">
            <CheckCircle className="text-emerald-400" size={36} />
            <p className="text-slate-200 font-semibold text-sm">{file?.name}</p>
            <p className="text-slate-400 text-xs mt-1">{message}</p>
          </div>
        ) : status === 'error' ? (
          <div className="flex flex-col items-center gap-2">
            <AlertCircle className="text-rose-400" size={36} />
            <p className="text-rose-300 font-medium text-sm">{message}</p>
            <p className="text-slate-500 text-xs mt-1">Click or drag another file to retry</p>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <div className="p-3 rounded-full bg-indigo-500/10 text-indigo-400 mb-1">
              <Upload size={24} />
            </div>
            <p className="text-slate-200 font-medium text-sm">Drag & drop files here</p>
            <p className="text-slate-400 text-xs">Supports {validExtensions.join(', ')}</p>
          </div>
        )}
      </div>

      {/* Document List */}
      <div className="flex flex-col gap-2">
        <div className="flex items-center justify-between">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Indexed Documents
          </h3>
          <span className="text-[10px] text-indigo-400 font-medium">Select to Query</span>
        </div>

        {loadingDocs ? (
          <p className="text-slate-500 text-xs">Loading documents...</p>
        ) : documents.length === 0 ? (
          <p className="text-slate-500 text-xs">No documents indexed yet.</p>
        ) : (
          <div className="flex flex-col gap-2 max-h-52 overflow-y-auto">
            {/* Global Search Option */}
            <div
              onClick={() => onSelectDocument && onSelectDocument(null)}
              className={`flex items-center justify-between gap-2 text-xs p-2.5 rounded-lg border cursor-pointer transition-all ${
                !activeDocument
                  ? 'bg-indigo-950/40 border-indigo-500/60 text-indigo-300 font-semibold shadow-md shadow-indigo-950/40'
                  : 'bg-slate-900/60 border-slate-800 text-slate-400 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <div className={`w-2 h-2 rounded-full ${!activeDocument ? 'bg-indigo-400 animate-pulse' : 'bg-slate-600'}`}></div>
                <span className="truncate font-medium">All Documents (Global Search)</span>
              </div>
              <span className="text-[10px] uppercase text-indigo-400 bg-indigo-500/10 px-1.5 py-0.5 rounded border border-indigo-500/20">
                All
              </span>
            </div>

            {/* Individual Source Files */}
            {documents.map((doc) => {
              const isSelected = activeDocument === doc.file_name
              return (
                <div
                  key={doc.file_name}
                  onClick={() => onSelectDocument && onSelectDocument(doc.file_name)}
                  className={`flex items-center justify-between gap-2 text-xs p-2.5 rounded-lg border cursor-pointer transition-all ${
                    isSelected
                      ? 'bg-indigo-950/40 border-indigo-500/60 text-indigo-300 font-semibold shadow-md shadow-indigo-950/40'
                      : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText size={14} className={isSelected ? 'text-indigo-400 shrink-0' : 'text-slate-500 shrink-0'} />
                    <span className="truncate" title={doc.file_name}>
                      {doc.file_name}
                    </span>
                    <span className="text-[10px] uppercase text-slate-500 border border-slate-700 px-1 rounded shrink-0">
                      {doc.file_type}
                    </span>
                  </div>
                  <button
                    onClick={(e) => handleDeleteDocument(e, doc.file_name)}
                    className="text-slate-500 hover:text-rose-400 p-1 rounded transition-colors shrink-0"
                    title="Delete document"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
