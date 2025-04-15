// Leaderboard page functionality
document.addEventListener('DOMContentLoaded', () => {
    // Add any leaderboard-specific functionality here
    
    // Example: Highlight the current user's row
    const playerName = document.querySelector('.user-info p')?.textContent.split(',')[0].replace('Welcome, ', '');
    if (playerName) {
        const rows = document.querySelectorAll('.leaderboard-table tbody tr');
        rows.forEach(row => {
            const nameCell = row.querySelector('td:nth-child(2)');
            if (nameCell && nameCell.textContent === playerName) {
                row.classList.add('highlight');
            }
        });
    }
}); 