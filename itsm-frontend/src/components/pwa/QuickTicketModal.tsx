// Components - PWA Quick Ticket Modal
// Minimal ticket creation form with camera integration

import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { X, Camera, Upload, Trash2, Send, Loader2 } from 'lucide-react';
import type { Category, Subcategory } from '../../types/mutations';
import { getCategories, getSubcategories, createTicket } from '../../api/mutations';

interface QuickTicketModalProps {
    onClose: () => void;
}

interface AttachmentPreview {
    file: File;
    preview: string;
    isImage: boolean;
}

export function QuickTicketModal({ onClose }: QuickTicketModalProps) {
    const navigate = useNavigate();
    const fileInputRef = useRef<HTMLInputElement>(null);
    const cameraInputRef = useRef<HTMLInputElement>(null);

    // Form state
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [categoryId, setCategoryId] = useState('');
    const [subcategoryId, setSubcategoryId] = useState('');
    const [attachments, setAttachments] = useState<AttachmentPreview[]>([]);

    // Data state
    const [categories, setCategories] = useState<Category[]>([]);
    const [subcategories, setSubcategories] = useState<Subcategory[]>([]);
    const [isLoadingCategories, setIsLoadingCategories] = useState(true);
    const [isLoadingSubcats, setIsLoadingSubcats] = useState(false);
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState('');

    // Load categories on mount
    useEffect(() => {
        async function loadCategories() {
            try {
                const cats = await getCategories();
                setCategories(cats);
            } catch (err) {
                setError('Failed to load categories');
            } finally {
                setIsLoadingCategories(false);
            }
        }
        loadCategories();
    }, []);

    // Load subcategories when category changes
    useEffect(() => {
        if (!categoryId) {
            setSubcategories([]);
            setSubcategoryId('');
            return;
        }

        async function loadSubcats() {
            setIsLoadingSubcats(true);
            try {
                const subs = await getSubcategories(categoryId);
                setSubcategories(subs);
                setSubcategoryId('');
            } catch (err) {
                setError('Failed to load subcategories');
            } finally {
                setIsLoadingSubcats(false);
            }
        }
        loadSubcats();
    }, [categoryId]);

    // Handle file selection (from gallery or camera)
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files) return;

        const newAttachments: AttachmentPreview[] = [];
        const maxFiles = 5 - attachments.length;

        for (let i = 0; i < Math.min(files.length, maxFiles); i++) {
            const file = files[i];
            // Compress if image and > 1MB
            const isImage = file.type.startsWith('image/');

            newAttachments.push({
                file,
                preview: isImage ? URL.createObjectURL(file) : '',
                isImage
            });
        }

        setAttachments(prev => [...prev, ...newAttachments]);
        e.target.value = ''; // Reset input
    };

    // Remove attachment
    const removeAttachment = (index: number) => {
        setAttachments(prev => {
            const newList = [...prev];
            if (newList[index].preview) {
                URL.revokeObjectURL(newList[index].preview);
            }
            newList.splice(index, 1);
            return newList;
        });
    };

    // Submit form
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim() || !categoryId || !subcategoryId) {
            setError('Please fill in all required fields');
            return;
        }

        setIsSubmitting(true);
        setError('');

        try {
            const files = attachments.map(a => a.file);
            // Backend requires description, use title as fallback if empty
            const ticketDescription = description.trim() || title.trim();
            const result = await createTicket(
                {
                    title: title.trim(),
                    description: ticketDescription,
                    category_id: categoryId,
                    subcategory_id: subcategoryId
                },
                files.length > 0 ? files : undefined
            );

            // Navigate to the created ticket
            onClose();
            navigate(`/tickets/${result.id}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create ticket');
        } finally {
            setIsSubmitting(false);
        }
    };

    const isFormValid = title.trim() && categoryId && subcategoryId;

    return (
        <div className="fixed inset-0 z-50 flex items-end sm:items-center justify-center">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-md max-h-[90vh] m-4 overflow-hidden rounded-2xl glass-panel animate-slide-up">
                {/* Header */}
                <div className="flex items-center justify-between p-4 border-b border-surface-200 dark:border-surface-700">
                    <h2 className="text-lg font-semibold text-surface-900 dark:text-white">
                        Quick Ticket
                    </h2>
                    <button
                        onClick={onClose}
                        className="p-2 rounded-full hover:bg-surface-100 dark:hover:bg-surface-800 transition-colors"
                    >
                        <X className="w-5 h-5 text-surface-500" />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="p-4 space-y-4 overflow-y-auto max-h-[70vh]">
                    {/* Error */}
                    {error && (
                        <div className="p-3 text-sm text-red-600 bg-red-50 dark:bg-red-900/20 dark:text-red-400 rounded-lg">
                            {error}
                        </div>
                    )}

                    {/* Title */}
                    <div>
                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
                            Title <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            placeholder="Brief description of the issue"
                            className="input"
                            autoFocus
                        />
                    </div>

                    {/* Category */}
                    <div className="relative">
                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
                            Category <span className="text-red-500">*</span>
                        </label>
                        <select
                            value={categoryId}
                            onChange={(e) => setCategoryId(e.target.value)}
                            className="input appearance-none w-full"
                            disabled={isLoadingCategories}
                            style={{ WebkitAppearance: 'menulist-button' }}
                        >
                            <option value="">Select category...</option>
                            {categories.map(cat => (
                                <option key={cat.id} value={cat.id}>{cat.name}</option>
                            ))}
                        </select>
                    </div>

                    {/* Subcategory */}
                    <div className="relative">
                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
                            Subcategory <span className="text-red-500">*</span>
                        </label>
                        <select
                            value={subcategoryId}
                            onChange={(e) => setSubcategoryId(e.target.value)}
                            className="input appearance-none w-full"
                            disabled={!categoryId || isLoadingSubcats}
                            style={{ WebkitAppearance: 'menulist-button' }}
                        >
                            <option value="">Select subcategory...</option>
                            {subcategories.map(sub => (
                                <option key={sub.id} value={sub.id}>{sub.name}</option>
                            ))}
                        </select>
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-1">
                            Description
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Detailed explanation (optional)"
                            rows={3}
                            className="input resize-none"
                        />
                    </div>

                    {/* Attachments */}
                    <div>
                        <label className="block text-sm font-medium text-surface-700 dark:text-surface-300 mb-2">
                            Attachments ({attachments.length}/5)
                        </label>

                        {/* Attachment previews */}
                        {attachments.length > 0 && (
                            <div className="flex flex-wrap gap-2 mb-3">
                                {attachments.map((att, idx) => (
                                    <div key={idx} className="relative group">
                                        {att.isImage ? (
                                            <img
                                                src={att.preview}
                                                alt={att.file.name}
                                                className="w-16 h-16 object-cover rounded-lg border border-surface-200 dark:border-surface-700"
                                            />
                                        ) : (
                                            <div className="w-16 h-16 flex items-center justify-center bg-surface-100 dark:bg-surface-800 rounded-lg border border-surface-200 dark:border-surface-700">
                                                <span className="text-xs text-surface-500 text-center px-1 truncate">
                                                    {att.file.name.split('.').pop()?.toUpperCase()}
                                                </span>
                                            </div>
                                        )}
                                        <button
                                            type="button"
                                            onClick={() => removeAttachment(idx)}
                                            className="absolute -top-1 -right-1 p-1 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
                                        >
                                            <Trash2 className="w-3 h-3" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}

                        {/* Attachment buttons */}
                        {attachments.length < 5 && (
                            <div className="flex gap-2">
                                {/* Camera button */}
                                <button
                                    type="button"
                                    onClick={() => cameraInputRef.current?.click()}
                                    className="flex-1 flex items-center justify-center gap-2 p-3 border-2 border-dashed border-surface-300 dark:border-surface-600 rounded-lg hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors"
                                >
                                    <Camera className="w-5 h-5 text-surface-500" />
                                    <span className="text-sm text-surface-600 dark:text-surface-400">Camera</span>
                                </button>
                                <input
                                    ref={cameraInputRef}
                                    type="file"
                                    accept="image/*"
                                    capture="environment"
                                    onChange={handleFileChange}
                                    className="hidden"
                                />

                                {/* Upload button */}
                                <button
                                    type="button"
                                    onClick={() => fileInputRef.current?.click()}
                                    className="flex-1 flex items-center justify-center gap-2 p-3 border-2 border-dashed border-surface-300 dark:border-surface-600 rounded-lg hover:border-primary-500 hover:bg-primary-50 dark:hover:bg-primary-900/10 transition-colors"
                                >
                                    <Upload className="w-5 h-5 text-surface-500" />
                                    <span className="text-sm text-surface-600 dark:text-surface-400">Upload</span>
                                </button>
                                <input
                                    ref={fileInputRef}
                                    type="file"
                                    accept="image/*,.pdf,.doc,.docx,.xls,.xlsx,.txt"
                                    multiple
                                    onChange={handleFileChange}
                                    className="hidden"
                                />
                            </div>
                        )}
                    </div>

                    {/* Submit */}
                    <button
                        type="submit"
                        disabled={!isFormValid || isSubmitting}
                        className="w-full btn btn-accent py-3"
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                Creating...
                            </>
                        ) : (
                            <>
                                <Send className="w-5 h-5" />
                                Create Ticket
                            </>
                        )}
                    </button>
                </form>
            </div>
        </div>
    );
}
