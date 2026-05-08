// Global state
let currentPage = 1;
let isLoading = false;
let currentRating = 0;

const agentListUrl = "/agents";

// Utility functions
const utils = {
    getCSRFToken() {
        return document.querySelector('meta[name="csrf-token"]')?.content;
    },

    showToast(message, type = 'success') {
        const toast = document.createElement('div');
        toast.className = `fixed bottom-4 right-4 p-4 rounded-lg shadow-lg ${type === 'success' ? 'bg-green-500' : 'bg-red-500'
            } text-white z-50`;
        toast.textContent = message;

        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    },

    highlightStars(count) {
        const stars = document.querySelectorAll('.review-star');
        stars?.forEach((star, index) => {
            if (index < count) {
                star.classList.remove('far');
                star.classList.add('fas', 'text-yellow-400');
            } else {
                star.classList.remove('fas', 'text-yellow-400');
                star.classList.add('far');
            }
        });
    },

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }
};

// Modal functionality
const modal = {
    show(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            modalElement.classList.remove('hidden');
            document.body.style.overflow = 'hidden';

            // Focus first focusable element
            const focusable = modalElement.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
            if (focusable.length) focusable[0].focus();

            // Add escape key listener
            document.addEventListener('keydown', this.handleEscapeKey);
        }
    },

    close(modalId) {
        const modalElement = document.getElementById(modalId);
        if (modalElement) {
            modalElement.classList.add('hidden');
            document.body.style.overflow = 'auto';
            document.removeEventListener('keydown', this.handleEscapeKey);
        }
    },

    handleEscapeKey(e) {
        if (e.key === 'Escape') {
            const visibleModal = document.querySelector('.modal:not(.hidden)');
            if (visibleModal) modal.close(visibleModal.id);
        }
    }
};

// Review functionality
const reviews = {
    async submit(event) {
        event?.preventDefault();
        
        console.log('Submit handler called'); // Debug log
        
        const reviewText = document.getElementById('review-text').value.trim();
        const form = document.getElementById('review-form');
        const reviewId = form.getAttribute('data-review-id');
        const ratingInput = document.getElementById('rating-input');
        const rating = parseInt(ratingInput.value);

        if (!rating || rating < 1 || rating > 5) {
            utils.showToast('Please select a rating', 'error');
            return;
        }

        if (!reviewText) {
            utils.showToast('Please write a review', 'error');
            return;
        }

        try {
            console.log('window.AGENT_ID:', window.AGENT_ID); // Debug log
            
            const url = `/submit/${window.AGENT_ID}`; // Let's see what URL is actually being used
            console.log('Submitting to URL:', url); // Debug log

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': utils.getCSRFToken()
                },
                body: JSON.stringify({
                    rating: rating,
                    review_text: reviewText
                })
            });

            console.log('Response:', response); // Debug log

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Failed to submit review');
            }

            utils.showToast('Review submitted successfully!');
            modal.close('review-modal');
            location.reload();

        } catch (error) {
            console.error('Error:', error);
            utils.showToast(error.message || 'Error submitting review', 'error');
        }
    },

    async edit(reviewId) {
        try {
            const response = await fetch(`/review/${reviewId}`, {  // Changed from /review/${reviewId}/edit
                method: 'GET'
            });
            const data = await response.json();

            if (response.ok) {
                // Set the current rating
                currentRating = data.review.rating;

                // Update form fields
                const form = document.getElementById('review-form');
                form.setAttribute('data-review-id', reviewId);
                document.getElementById('review-text').value = data.review.content;

                // Update star display
                utils.highlightStars(currentRating);

                // Update modal title and button
                document.querySelector('#review-modal h3').textContent = 'Edit Review';
                document.querySelector('#review-modal button[type="submit"]').textContent = 'Update Review';

                modal.show('review-modal');
            }
        } catch (error) {
            console.error('Error:', error);
            utils.showToast('Error loading review', 'error');
        }
    },

    async delete(reviewId) {
        if (!confirm('Are you sure you want to delete this review?')) {
            return;
        }

        try {
            const response = await fetch(`/review/${reviewId}`, {
                method: 'DELETE',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': utils.getCSRFToken()
                }
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.message || 'Failed to delete review');
            }

            utils.showToast('Review deleted successfully');
            location.reload();

        } catch (error) {
            console.error('Error:', error);
            utils.showToast(error.message || 'Error deleting review', 'error');
        }
    },

    async vote(reviewId, voteType) {
        try {
            const response = await fetch(`/review/${reviewId}/vote`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRF-Token': utils.getCSRFToken()
                },
                body: JSON.stringify({ vote_type: voteType }),
                credentials: 'same-origin'
            });

            if (!response.ok) {
                throw new Error('Failed to record vote');
            }

            const data = await response.json();
            if (data.success) {
                // Update the UI without page reload
                const reviewElement = document.querySelector(`#review-${reviewId}`);
                const helpfulBtn = reviewElement.querySelector('.helpful-btn');
                const unhelpfulBtn = reviewElement.querySelector('.unhelpful-btn');

                // Update vote counts
                helpfulBtn.querySelector('.count').textContent = `(${data.helpful_votes})`;
                unhelpfulBtn.querySelector('.count').textContent = `(${data.unhelpful_votes})`;

                // Update icons based on user's vote
                helpfulBtn.querySelector('i').className =
                    voteType === 'helpful' ? 'fas fa-thumbs-up mr-1' : 'far fa-thumbs-up mr-1';
                unhelpfulBtn.querySelector('i').className =
                    voteType === 'unhelpful' ? 'fas fa-thumbs-down mr-1' : 'far fa-thumbs-down mr-1';

                // Update button colors
                helpfulBtn.classList.toggle('text-blue-600', voteType === 'helpful');
                unhelpfulBtn.classList.toggle('text-blue-600', voteType === 'unhelpful');

                utils.showToast('Vote recorded successfully!');
            } else {
                throw new Error(data.message || 'Failed to record vote');
            }
        } catch (error) {
            console.error('Error:', error);
            utils.showToast(error.message || 'Error recording vote', 'error');
        }
    },

    reset() {
        const form = document.getElementById('review-form');
        form.removeAttribute('data-review-id');
        form.reset();
        currentRating = 0;
        utils.highlightStars(0);
        document.querySelector('#review-modal h3').textContent = 'Write a Review';
        document.querySelector('#review-modal button[type="submit"]').textContent = 'Submit Review';
    }
};

// Favorite functionality
async function toggleFavorite(agentId) {
    try {
        const response = await fetch(`/agent/${agentId}/favorite`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRF-Token': utils.getCSRFToken()
            },
            credentials: 'same-origin'
        });

        const data = await response.json();

        if (data.success) {
            // Handle favorite button updates
            const btn = document.getElementById('favorite-btn');
            if (btn) {
                const icon = btn.querySelector('i');
                const text = btn.querySelector('span');

                if (data.is_favorite) {
                    icon.classList.add('text-red-500');
                    text && (text.textContent = 'Favorited');
                } else {
                    icon.classList.remove('text-red-500');
                    text && (text.textContent = 'Favorite');
                }
            }

            // Handle favorite card in profile page
            const favoriteCard = document.querySelector(`.favorite-agents [data-agent-id="${agentId}"]`);
            if (favoriteCard && !data.is_favorite) {
                favoriteCard.remove();

                // Check if there are any favorites left
                const favoritesContainer = document.querySelector('.favorite-agents');
                const remainingFavorites = favoritesContainer.querySelectorAll('[data-agent-id]');

                if (remainingFavorites.length === 0) {
                    favoritesContainer.innerHTML = `
                        <div class="text-center py-12">
                            <div class="w-16 h-16 bg-pink-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                <i class="fas fa-heart text-2xl text-pink-500"></i>
                            </div>
                            <h3 class="text-lg font-medium text-gray-900 mb-2">Your Favorites List is Empty</h3>
                            <p class="text-gray-500 mb-4">Find and favorite AI agents that catch your interest. They'll appear here for easy access.</p>
                            <a href="${agentListUrl}" 
                               class="inline-flex items-center px-4 py-2 bg-pink-500 text-white rounded-lg hover:bg-pink-600 transition">
                                <i class="fas fa-compass mr-2"></i>Explore Agents
                            </a>
                        </div>`;
                }
            }

            utils.showToast(data.message || (data.is_favorite ? 'Added to favorites!' : 'Removed from favorites'));
        } else {
            utils.showToast(data.message || 'Error updating favorite status', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        utils.showToast('Error updating favorite status', 'error');
    }
}

// Search functionality with debouncing
const searchInput = document.getElementById('search-input');
const searchResults = document.getElementById('search-results');

if (searchInput && searchResults) {
    const performSearch = utils.debounce(async (query) => {
        try {
            const response = await fetch(`/agent/api/suggest?q=${encodeURIComponent(query)}`);
            const data = await response.json();

            searchResults.innerHTML = '';
            searchResults.classList.remove('hidden');

            if (data.length === 0) {
                searchResults.innerHTML = `
                    <div class="p-4 text-gray-500 text-center">
                        No results found
                    </div>
                `;
                return;
            }

            data.forEach(agent => {
                const div = document.createElement('div');
                div.className = 'p-4 hover:bg-gray-50 cursor-pointer';
                div.setAttribute('role', 'option');
                div.innerHTML = `
                    <div class="flex items-center">
                        <img src="${agent.logo_url || '/static/img/default-agent.png'}" 
                             alt="${agent.name}"
                             class="w-8 h-8 rounded-lg mr-3">
                        <div>
                            <div class="font-medium">${agent.name}</div>
                            <div class="text-sm text-gray-500">${agent.provider}</div>
                        </div>
                    </div>
                `;
                div.addEventListener('click', () => {
                    window.location.href = `/agent/${agent.slug}`;
                });
                searchResults.appendChild(div);
            });
        } catch (error) {
            console.error('Error:', error);
            utils.showToast('Error searching agents', 'error');
        }
    }, 300);

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value;

        if (query.length < 2) {
            searchResults.classList.add('hidden');
            return;
        }

        performSearch(query);
    });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    // Initialize rating system with accessibility
    const stars = document.querySelectorAll('.review-star');
    stars?.forEach((star, index) => {
        star.setAttribute('role', 'button');
        star.setAttribute('aria-label', `Rate ${index + 1} stars`);
        star.setAttribute('tabindex', '0');

        const handleRating = () => {
            currentRating = index + 1;
            utils.highlightStars(currentRating);
            stars.forEach((s, i) => {
                s.setAttribute('aria-pressed', i < currentRating ? 'true' : 'false');
            });
        };

        star.addEventListener('click', handleRating);
        star.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                handleRating();
            }
        });

        star.addEventListener('mouseover', () => {
            utils.highlightStars(index + 1);
        });

        star.addEventListener('mouseout', () => {
            utils.highlightStars(currentRating);
        });
    });

    // Initialize modal star rating
    const starButtons = document.querySelectorAll('.star-btn');
    const ratingInput = document.getElementById('rating-input');

    if (starButtons.length && ratingInput) {
        starButtons.forEach(star => {
            star.addEventListener('click', function () {
                const rating = this.getAttribute('data-rating');
                ratingInput.value = rating;
                currentRating = parseInt(rating);

                // Update star colors
                starButtons.forEach(s => {
                    const value = s.getAttribute('data-rating');
                    if (value <= rating) {
                        s.classList.remove('text-gray-300');
                        s.classList.add('text-yellow-400');
                    } else {
                        s.classList.remove('text-yellow-400');
                        s.classList.add('text-gray-300');
                    }
                });
            });

            // Hover effects
            star.addEventListener('mouseenter', function () {
                const rating = this.getAttribute('data-rating');
                starButtons.forEach(s => {
                    const value = s.getAttribute('data-rating');
                    if (value <= rating) {
                        s.classList.add('text-yellow-400');
                        s.classList.remove('text-gray-300');
                    }
                });
            });

            star.addEventListener('mouseleave', function () {
                const selectedRating = ratingInput.value;
                starButtons.forEach(s => {
                    const value = s.getAttribute('data-rating');
                    if (value <= selectedRating) {
                        s.classList.add('text-yellow-400');
                        s.classList.remove('text-gray-300');
                    } else {
                        s.classList.remove('text-yellow-400');
                        s.classList.add('text-gray-300');
                    }
                });
            });
        });
    }

    // Initialize review form submission
    const modalReviewForm = document.getElementById('review-form');
    if (modalReviewForm) {
        modalReviewForm.addEventListener('submit', reviews.submit);
    }

    // Initialize close buttons
    document.querySelectorAll('.close-alert').forEach(button => {
        button.addEventListener('click', function () {
            this.parentElement.remove();
        });
    });

    // Initialize modal close on outside click
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('modal')) {
            modal.close(e.target.id);
        }
    });

    // Open source repository field toggle
    const openSourceCheckbox = document.querySelector('#is_open_source');
    const sourceRepoField = document.querySelector('#source-repo-field');

    if (openSourceCheckbox && sourceRepoField) {
        openSourceCheckbox.addEventListener('change', function () {
            sourceRepoField.classList.toggle('hidden', !this.checked);
        });
    }
});

// Export functions for use in HTML
window.showModal = modal.show;
window.closeModal = modal.close;
window.editReview = reviews.edit;
window.deleteReview = reviews.delete;
window.resetReviewForm = reviews.reset;
window.voteReview = reviews.vote;
window.toggleFavorite = toggleFavorite;