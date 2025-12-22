// Components - Create Ticket Form

import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import type { Category, Subcategory } from '../../types/mutations';
import { getCategories, getSubcategories, createTicket } from '../../api/mutations';
import { getErrorCode, getErrorMessage } from '../../types/api';
import { LoadingSpinner } from '../common';
import { Upload, X, AlertCircle } from 'lucide-react';

interface CreateTicketFormProps {
    /** Called after successful creation */
    onSuccess?: (ticketId: string) => void;
}

/**
 * Create Ticket Form Component
 * Allows users to create new tickets with optional attachments
 */
export function CreateTicketForm({ onSuccess }: CreateTicketFormProps) {
    const navigate = useNavigate();

    // Form state
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [categoryId, setCategoryId] = useState('');
    const [subcategoryId, setSubcategoryId] = useState('');
    const [attachments, setAttachments] = useState<File[]>([]);

    // Data state
    const [categories, setCategories] = useState<Category[]>([]);
    const [subcategories, setSubcategories] = useState<Subcategory[]>([]);
    const [loadingCategories, setLoadingCategories] = useState(true);
    const [loadingSubcategories, setLoadingSubcategories] = useState(false);

    // Submission state
    const [isSubmitting, setIsSubmitting] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    // Load categories on mount
    useEffect(() => {
        const loadCategories = async () => {
            setLoadingCategories(true);
            try {
                const cats = await getCategories();
                // Backend already filters for is_active=True
                setCategories(cats);
                if (cats.length > 0) {
                    setCategoryId(cats[0].id);
                }
            } catch (err) {
                setError(err instanceof Error ? err : new Error('Failed to load categories'));
            } finally {
                setLoadingCategories(false);
            }
        };
        loadCategories();
    }, []);

    // Load subcategories when category changes
    useEffect(() => {
        if (!categoryId) {
            setSubcategories([]);
            setSubcategoryId('');
            return;
        }

        const loadSubcats = async () => {
            setLoadingSubcategories(true);
            try {
                const subcats = await getSubcategories(categoryId);
                // Backend already filters for is_active=True
                setSubcategories(subcats);
                if (subcats.length > 0) {
                    setSubcategoryId(subcats[0].id);
                } else {
                    setSubcategoryId('');
                }
            } catch (err) {
                setError(err instanceof Error ? err : new Error('Failed to load subcategories'));
            } finally {
                setLoadingSubcategories(false);
            }
        };
        loadSubcats();
    }, [categoryId]);

    // Form validation
    const isValid =
        title.trim().length > 0 &&
        title.trim().length <= 255 &&
        description.trim().length > 0 &&
        categoryId.length > 0 &&
        subcategoryId.length > 0;

    // Handle file selection
    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = Array.from(e.target.files || []);

        // Validate each file
        const validFiles: File[] = [];
        for (const file of files) {
            if (file.size > 25 * 1024 * 1024) {
                setError(new Error(`File "${file.name}" exceeds 25MB limit`));
                return;
            }
            validFiles.push(file);
        }

        // Check total count
        if (attachments.length + validFiles.length > 5) {
            setError(new Error('Maximum 5 attachments allowed'));
            return;
        }

        setError(null);
        setAttachments([...attachments, ...validFiles]);
    };

    // Remove attachment
    const handleRemoveAttachment = (index: number) => {
        setAttachments(attachments.filter((_, i) => i !== index));
    };

    // Submit form
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!isValid || isSubmitting) return;

        setIsSubmitting(true);
        setError(null);

        try {
            const result = await createTicket(
                {
                    title: title.trim(),
                    description: description.trim(),
                    category_id: categoryId,
                    subcategory_id: subcategoryId,
                },
                attachments.length > 0 ? attachments : undefined
            );

            // Success - navigate to the new ticket
            if (onSuccess) {
                onSuccess(result.id);
            } else {
                navigate(`/tickets/${result.id}`);
            }
        } catch (err) {
            setError(err instanceof Error ? err : new Error('Failed to create ticket'));
        } finally {
            setIsSubmitting(false);
        }
    };

    if (loadingCategories) {
        return <LoadingSpinner message="Loading form..." />;
    }

    return (
        <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="flex items-center justify-between">
                <h2 className="text-xl font-bold text-surface-900 dark:text-white">Create New Ticket</h2>
            </div>

            {/* Error display */}
            {error && (
                <div className="bg-red-50 dark:bg-red-900/10 border border-red-100 dark:border-red-900/20 rounded-xl p-4 flex items-center gap-3 text-red-600 dark:text-red-400 text-sm" role="alert">
                    <AlertCircle size={18} />
                    <div>
                        <strong>Error ({getErrorCode(error)}):</strong>{' '}
                        {getErrorMessage(error)}
                    </div>
                </div>
            )}

            {/* Title */}
            <div className="space-y-2">
                <label className="block text-sm font-medium text-surface-700 dark:text-surface-300" htmlFor="title">
                    Title<span className="text-red-500 ml-1">*</span>
                </label>
                <div className="relative">
                    <input
                        type="text"
                        id="title"
                        className="input w-full"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        placeholder="Brief summary of the issue"
                        maxLength={255}
                        required
                        disabled={isSubmitting}
                    />
                </div>
                <span className="text-xs text-surface-500 text-right block">{title.length}/255 characters</span>
            </div>

            {/* Description */}
            <div className="space-y-2">
                <label className="block text-sm font-medium text-surface-700 dark:text-surface-300" htmlFor="description">
                    Description<span className="text-red-500 ml-1">*</span>
                </label>
                <textarea
                    id="description"
                    className="input w-full min-h-[150px] py-3"
                    value={description}
                    onChange={(e) => setDescription(e.target.value)}
                    placeholder="Detailed description of the issue"
                    rows={6}
                    required
                    disabled={isSubmitting}
                />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Category */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-surface-700 dark:text-surface-300" htmlFor="category">
                        Category<span className="text-red-500 ml-1">*</span>
                    </label>
                    <select
                        id="category"
                        className="input w-full"
                        value={categoryId}
                        onChange={(e) => setCategoryId(e.target.value)}
                        required
                        disabled={isSubmitting}
                    >
                        {categories.map((cat) => (
                            <option key={cat.id} value={cat.id}>
                                {cat.name}
                            </option>
                        ))}
                    </select>
                </div>

                {/* Subcategory */}
                <div className="space-y-2">
                    <label className="block text-sm font-medium text-surface-700 dark:text-surface-300" htmlFor="subcategory">
                        Subcategory<span className="text-red-500 ml-1">*</span>
                    </label>
                    <select
                        id="subcategory"
                        className="input w-full"
                        value={subcategoryId}
                        onChange={(e) => setSubcategoryId(e.target.value)}
                        required
                        disabled={isSubmitting || loadingSubcategories}
                    >
                        {loadingSubcategories ? (
                            <option>Loading...</option>
                        ) : subcategories.length === 0 ? (
                            <option value="">No subcategories available</option>
                        ) : (
                            subcategories.map((subcat) => (
                                <option key={subcat.id} value={subcat.id}>
                                    {subcat.name}
                                </option>
                            ))
                        )}
                    </select>
                </div>
            </div>

            {/* Attachments */}
            <div className="space-y-4">
                <label className="block text-sm font-medium text-surface-700 dark:text-surface-300">
                    Attachments (optional)
                </label>

                <div className="border-2 border-dashed border-surface-200 dark:border-surface-700 rounded-xl p-6 text-center hover:border-primary-500/50 transition-colors bg-surface-50/50 dark:bg-surface-800/10">
                    <input
                        type="file"
                        id="file-upload"
                        className="hidden"
                        onChange={handleFileChange}
                        disabled={isSubmitting || attachments.length >= 5}
                        multiple
                    />
                    <label htmlFor="file-upload" className="cursor-pointer flex flex-col items-center gap-2">
                        <div className="w-10 h-10 rounded-full bg-surface-100 dark:bg-surface-800 flex items-center justify-center text-surface-500 group-hover:text-primary-500">
                            <Upload size={20} />
                        </div>
                        <span className="text-sm font-medium text-primary-600 dark:text-primary-400">Click to upload</span>
                        <span className="text-xs text-surface-500">Maximum 5 files, 25MB each</span>
                    </label>
                </div>

                {attachments.length > 0 && (
                    <ul className="space-y-2">
                        {attachments.map((file, index) => (
                            <li key={index} className="flex items-center justify-between p-3 bg-surface-50 dark:bg-surface-800 rounded-lg border border-surface-200 dark:border-surface-700">
                                <span className="text-sm text-surface-700 dark:text-surface-300 flex items-center gap-2">
                                    <span className="w-2 h-2 rounded-full bg-primary-500" />
                                    {file.name} <span className="text-surface-400">({(file.size / 1024).toFixed(1)} KB)</span>
                                </span>
                                <button
                                    type="button"
                                    className="p-1 hover:bg-surface-200 dark:hover:bg-surface-700 rounded-lg text-surface-500 hover:text-red-500 transition-colors"
                                    onClick={() => handleRemoveAttachment(index)}
                                    disabled={isSubmitting}
                                >
                                    <X size={16} />
                                </button>
                            </li>
                        ))}
                    </ul>
                )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-end gap-3 pt-4 border-t border-surface-200 dark:border-surface-700">
                <button
                    type="button"
                    className="btn btn-secondary"
                    onClick={() => navigate(-1)}
                    disabled={isSubmitting}
                >
                    Cancel
                </button>
                <button
                    type="submit"
                    className="btn btn-primary"
                    disabled={!isValid || isSubmitting}
                >
                    {isSubmitting ? 'Creating...' : 'Create Ticket'}
                </button>
            </div>
        </form>
    );
}
