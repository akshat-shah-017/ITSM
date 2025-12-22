// Components - Pagination

interface PaginationProps {
    /** Current page (1-indexed) */
    page: number;
    /** Items per page */
    pageSize: number;
    /** Total number of items */
    totalCount: number;
    /** Callback when page changes */
    onPageChange: (page: number) => void;
}

/**
 * Pagination component
 * Uses 1-indexed pages to match API
 */
export function Pagination({
    page,
    pageSize,
    totalCount,
    onPageChange,
}: PaginationProps) {
    const totalPages = Math.ceil(totalCount / pageSize);

    if (totalPages <= 1) {
        return null;
    }

    const canGoPrevious = page > 1;
    const canGoNext = page < totalPages;

    // Calculate visible page numbers
    const getVisiblePages = (): number[] => {
        const pages: number[] = [];
        const maxVisible = 5;

        let start = Math.max(1, page - Math.floor(maxVisible / 2));
        const end = Math.min(totalPages, start + maxVisible - 1);

        // Adjust start if we're near the end
        if (end - start + 1 < maxVisible) {
            start = Math.max(1, end - maxVisible + 1);
        }

        for (let i = start; i <= end; i++) {
            pages.push(i);
        }

        return pages;
    };

    const visiblePages = getVisiblePages();

    return (
        <nav className="pagination" aria-label="Pagination">
            <button
                className="pagination-button"
                onClick={() => onPageChange(page - 1)}
                disabled={!canGoPrevious}
                aria-label="Previous page"
            >
                ← Previous
            </button>

            <div className="pagination-pages">
                {visiblePages[0] > 1 && (
                    <>
                        <button
                            className="pagination-page"
                            onClick={() => onPageChange(1)}
                        >
                            1
                        </button>
                        {visiblePages[0] > 2 && <span className="pagination-ellipsis">...</span>}
                    </>
                )}

                {visiblePages.map((p) => (
                    <button
                        key={p}
                        className={`pagination-page ${p === page ? 'active' : ''}`}
                        onClick={() => onPageChange(p)}
                        aria-current={p === page ? 'page' : undefined}
                    >
                        {p}
                    </button>
                ))}

                {visiblePages[visiblePages.length - 1] < totalPages && (
                    <>
                        {visiblePages[visiblePages.length - 1] < totalPages - 1 && (
                            <span className="pagination-ellipsis">...</span>
                        )}
                        <button
                            className="pagination-page"
                            onClick={() => onPageChange(totalPages)}
                        >
                            {totalPages}
                        </button>
                    </>
                )}
            </div>

            <button
                className="pagination-button"
                onClick={() => onPageChange(page + 1)}
                disabled={!canGoNext}
                aria-label="Next page"
            >
                Next →
            </button>

            <span className="pagination-info">
                Page {page} of {totalPages} ({totalCount} items)
            </span>
        </nav>
    );
}
