import React, { useEffect, useState } from 'react';
import {
  X,
  UploadCloud,
  FileText,
  Trash2,
  RefreshCw,
  AlertTriangle,
  CheckCircle2,
  Database,
  Download,
  Loader2,
} from 'lucide-react';
import {
  deleteAllDocuments,
  deleteDocument,
  deleteVectorstore,
  fetchDocuments,
  fetchEnvTemplate,
  rebuildVectorstore,
  uploadDocuments,
} from '../services/api';
import type { DocumentStatus } from '../types';

interface DataManagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onStatusChange?: () => void;
}

export const DataManagementModal: React.FC<DataManagementModalProps> = ({
  isOpen,
  onClose,
  onStatusChange,
}) => {
  const [docStatus, setDocStatus] = useState<DocumentStatus | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [isRebuilding, setIsRebuilding] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadDocs = async () => {
    try {
      setIsLoading(true);
      const data = await fetchDocuments();
      setDocStatus(data);
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message || 'Failed to load documents' });
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      loadDocs();
      setFeedback(null);
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleFileUpload = async (files: FileList | null) => {
    if (!files || files.length === 0) return;
    try {
      setIsUploading(true);
      setFeedback(null);
      const res = await uploadDocuments(files);
      if (res.errors.length > 0) {
        setFeedback({
          type: 'error',
          message: `Uploaded ${res.total_uploaded} files with errors: ${res.errors.join(', ')}`,
        });
      } else {
        setFeedback({
          type: 'success',
          message: `Successfully uploaded ${res.total_uploaded} document(s). Click "Rebuild Vectorstore" to index them.`,
        });
      }
      await loadDocs();
      onStatusChange?.();
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message || 'Upload failed' });
    } finally {
      setIsUploading(false);
    }
  };

  const handleRebuild = async () => {
    try {
      setIsRebuilding(true);
      setFeedback(null);
      const res = await rebuildVectorstore();
      if (res.success) {
        setFeedback({
          type: 'success',
          message: `Vectorstore rebuilt successfully! (${res.docs} docs, ${res.chunks} chunks indexed)`,
        });
      } else {
        setFeedback({ type: 'error', message: res.message });
      }
      await loadDocs();
      onStatusChange?.();
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message || 'Failed to rebuild vectorstore' });
    } finally {
      setIsRebuilding(false);
    }
  };

  const handleDeleteVectorstore = async () => {
    if (!confirm('Are you sure you want to delete the vectorstore database?')) return;
    try {
      setIsLoading(true);
      const res = await deleteVectorstore();
      if (res.success) {
        setFeedback({ type: 'success', message: 'Vectorstore deleted successfully.' });
      }
      await loadDocs();
      onStatusChange?.();
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteAllDocs = async () => {
    if (!confirm('Are you sure you want to delete all files in ./data/?')) return;
    try {
      setIsLoading(true);
      const res = await deleteAllDocuments();
      setFeedback({
        type: 'success',
        message: `Deleted ${res.deleted_count} files from ./data/.`,
      });
      await loadDocs();
      onStatusChange?.();
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message });
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeleteSingle = async (name: string) => {
    try {
      await deleteDocument(name);
      await loadDocs();
      onStatusChange?.();
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message });
    }
  };

  const handleDownloadTemplate = async () => {
    try {
      const template = await fetchEnvTemplate();
      const blob = new Blob([template], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = '.env.template';
      a.click();
      URL.revokeObjectURL(url);
    } catch (e: any) {
      setFeedback({ type: 'error', message: e.message });
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm select-none">
      <div className="bg-white dark:bg-[#141210] border border-[#e5e7eb] dark:border-[#2b2723] rounded-3xl w-full max-w-2xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="p-6 border-b border-[#e5e7eb] dark:border-[#2b2723] flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-tr from-[#009bff] to-[#ff882b] p-0.5 flex items-center justify-center">
              <div className="w-full h-full bg-white dark:bg-[#141210] rounded-[14px] flex items-center justify-center">
                <Database className="w-5 h-5 text-[#009bff]" />
              </div>
            </div>
            <div>
              <h2 className="font-semibold text-lg text-[#0f172a] dark:text-[#f8fafc]">
                Document & Vectorstore Management
              </h2>
              <p className="text-xs text-[#64748b] dark:text-[#94a3b8]">
                Manage local knowledge base and ChromaDB vector embeddings
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl text-[#94a3b8] hover:text-[#0f172a] dark:hover:text-white hover:bg-[#f1f5f9] dark:hover:bg-[#201d1a] transition-colors cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Feedback Toast */}
          {feedback && (
            <div
              className={`p-3.5 rounded-2xl border flex items-center space-x-2.5 text-xs ${
                feedback.type === 'success'
                  ? 'bg-[#081b0c] border-[#155d28] text-[#22e877]'
                  : 'bg-[#290d0b] border-[#5d1a15] text-[#f87171]'
              }`}
            >
              {feedback.type === 'success' ? (
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
              ) : (
                <AlertTriangle className="w-4 h-4 flex-shrink-0" />
              )}
              <span>{feedback.message}</span>
            </div>
          )}

          {/* Vectorstore Status & Actions */}
          <div className="p-4 rounded-2xl bg-[#f8fafc] dark:bg-[#1a1715] border border-[#e2e8f0] dark:border-[#2b2723] space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <span className="text-xs font-semibold text-[#0f172a] dark:text-[#f8fafc] block">
                  ChromaDB Index Status
                </span>
                <span className="text-[11px] text-[#64748b] dark:text-[#a1a1aa]">
                  Path: {docStatus?.chroma_path || './chroma_db'}
                </span>
              </div>
              <span
                className={`inline-flex items-center space-x-1.5 px-3 py-1 rounded-full text-xs font-medium ${
                  docStatus?.vectorstore_exists
                    ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20'
                    : 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    docStatus?.vectorstore_exists ? 'bg-emerald-500' : 'bg-amber-500'
                  }`}
                />
                <span>{docStatus?.vectorstore_exists ? 'Active Database' : 'Standby / Not Built'}</span>
              </span>
            </div>

            <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[#e2e8f0] dark:border-[#2b2723]">
              <button
                onClick={handleRebuild}
                disabled={isRebuilding || (docStatus?.count ?? 0) === 0}
                className="flex items-center space-x-1.5 px-4 py-2 rounded-xl bg-gradient-to-r from-[#009bff] to-[#ff882b] text-white text-xs font-semibold shadow-md disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-opacity cursor-pointer"
              >
                {isRebuilding ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <RefreshCw className="w-3.5 h-3.5" />
                )}
                <span>Rebuild Vectorstore</span>
              </button>

              <button
                onClick={handleDeleteVectorstore}
                disabled={isLoading || !docStatus?.vectorstore_exists}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-rose-50 dark:bg-rose-950/20 border border-rose-200 dark:border-rose-900/40 text-rose-600 dark:text-rose-400 text-xs font-medium hover:bg-rose-100 transition-colors disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>Delete Vectorstore</span>
              </button>

              <button
                onClick={handleDownloadTemplate}
                className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-[#f1f5f9] dark:bg-[#221f1c] border border-[#cbd5e1] dark:border-[#38332c] text-[#0f172a] dark:text-[#f8fafc] text-xs font-medium hover:bg-[#e2e8f0] transition-colors ml-auto cursor-pointer"
              >
                <Download className="w-3.5 h-3.5" />
                <span>.env Template</span>
              </button>
            </div>
          </div>

          {/* Drag & Drop Upload Zone */}
          <div className="space-y-2">
            <label className="text-xs font-semibold text-[#0f172a] dark:text-[#f8fafc]">
              Upload Knowledge Documents (PDF, TXT)
            </label>
            <label
              className={`border-2 border-dashed border-[#cbd5e1] dark:border-[#38332c] hover:border-[#ff882b] rounded-2xl p-6 flex flex-col items-center justify-center text-center cursor-pointer transition-colors ${
                isUploading ? 'opacity-50 pointer-events-none' : ''
              }`}
            >
              <input
                type="file"
                multiple
                accept=".pdf,.txt"
                onChange={(e) => handleFileUpload(e.target.files)}
                className="hidden"
              />
              <UploadCloud className="w-8 h-8 text-[#009bff] mb-2" />
              <p className="text-xs font-medium text-[#0f172a] dark:text-[#f8fafc]">
                Click or drag & drop files here to upload
              </p>
              <p className="text-[11px] text-[#64748b] dark:text-[#94a3b8] mt-1">
                Supports PDF and TXT files. Files will be saved into ./data/
              </p>
            </label>
          </div>

          {/* Uploaded Documents List */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h3 className="text-xs font-semibold text-[#0f172a] dark:text-[#f8fafc]">
                Uploaded Data Files ({docStatus?.count ?? 0})
              </h3>
              {(docStatus?.count ?? 0) > 0 && (
                <button
                  onClick={handleDeleteAllDocs}
                  className="text-xs text-rose-500 hover:underline font-medium cursor-pointer"
                >
                  Delete All Files
                </button>
              )}
            </div>

            {docStatus?.files && docStatus.files.length > 0 ? (
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {docStatus.files.map((file) => (
                  <div
                    key={file.name}
                    className="flex items-center justify-between p-3 rounded-xl bg-[#f8fafc] dark:bg-[#1a1715] border border-[#e2e8f0] dark:border-[#2b2723] text-xs"
                  >
                    <div className="flex items-center space-x-2.5 truncate pr-2">
                      <FileText className="w-4 h-4 text-[#009bff] flex-shrink-0" />
                      <span className="font-medium text-[#0f172a] dark:text-[#f8fafc] truncate">
                        {file.name}
                      </span>
                      <span className="text-[10px] text-[#64748b] dark:text-[#94a3b8] flex-shrink-0">
                        ({file.size_formatted})
                      </span>
                    </div>
                    <button
                      onClick={() => handleDeleteSingle(file.name)}
                      className="p-1 text-[#94a3b8] hover:text-rose-500 transition-colors cursor-pointer"
                      title="Delete document"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-xs text-[#64748b] dark:text-[#94a3b8] italic">
                No documents found in ./data/. Upload documents to enable vectorstore retrieval.
              </p>
            )}
          </div>
        </div>

        {/* Modal Footer */}
        <div className="p-4 border-t border-[#e5e7eb] dark:border-[#2b2723] flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2 rounded-xl bg-[#0f172a] dark:bg-white text-white dark:text-[#0f172a] text-xs font-semibold hover:opacity-90 transition-opacity cursor-pointer"
          >
            Done
          </button>
        </div>
      </div>
    </div>
  );
};
