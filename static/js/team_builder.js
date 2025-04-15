// Global variables
let selectedPlayers = [];
let playerPool = {};
let currentRecord = { wins: 0, losses: 0 };
let remainingBudget = 10;
let hasSubmitted = false;
let playerName = '';

// Initialize the team builder
function initializeTeamBuilder() {
    // Load player pool
    fetch('/api/player_pool')
        .then(response => response.json())
        .then(data => {
            playerPool = data;
            displayPlayerOptions();
        })
        .catch(error => {
            console.error('Error loading player pool:', error);
            showError('Error loading player pool. Please refresh the page.');
        });

    // Add event listener for player name input
    const nameInput = document.getElementById('player-name');
    const inputHint = document.querySelector('.input-hint');
    
    nameInput.addEventListener('input', function(e) {
        playerName = e.target.value.trim();
        updateSubmitButton();
        
        // Show/hide input hint
        if (playerName === '') {
            inputHint.classList.add('show');
        } else {
            inputHint.classList.remove('show');
        }
    });

    // Show hint initially if input is empty
    if (nameInput.value.trim() === '') {
        inputHint.classList.add('show');
    }
}

// Check if a player is already selected
function isPlayerSelected(playerName) {
    return selectedPlayers.some(player => player.name === playerName);
}

// Get player cost from category
function getPlayerCost(category) {
    return parseInt(category.replace('$', ''));
}

// Display player options by cost category
function displayPlayerOptions() {
    const playerSection = document.querySelector('.player-section');
    playerSection.innerHTML = '';

    const categories = ['$3', '$2', '$1', '$0'];
    categories.forEach(category => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'category';
        categoryDiv.innerHTML = `<h3>${category} Players</h3>`;

        const playerList = document.createElement('div');
        playerList.className = 'player-list';

        if (playerPool[category]) {
            playerPool[category].forEach(player => {
                const button = document.createElement('button');
                button.className = 'player-button';
                button.textContent = `${player.name} (${category})`;
                button.onclick = () => selectPlayer(player, category);
                button.disabled = isPlayerSelected(player.name) || hasSubmitted;
                playerList.appendChild(button);
            });
        }

        categoryDiv.appendChild(playerList);
        playerSection.appendChild(categoryDiv);
    });

    // Update budget display
    updateBudgetDisplay();
}

// Select a player and add to team
function selectPlayer(player, category) {
    if (hasSubmitted) {
        showError('You have already submitted your team. Cannot make changes.');
        return;
    }
    
    const cost = getPlayerCost(category);
    
    if (selectedPlayers.length >= 5) {
        showError('You can only select 5 players!');
        return;
    }

    if (cost > remainingBudget) {
        showError(`Not enough budget! You need $${cost} but only have $${remainingBudget} remaining.`);
        return;
    }

    player.cost = category;
    selectedPlayers.push(player);
    remainingBudget -= cost;
    
    updateTeamDisplay();
    displayPlayerOptions();
    updateSubmitButton();
}

// Update the team display
function updateTeamDisplay() {
    const teamSection = document.querySelector('.selected-players');
    teamSection.innerHTML = '';

    selectedPlayers.forEach(player => {
        const playerCard = document.createElement('div');
        playerCard.className = 'player-card';
        
        // Escape any special characters in the player name for the onclick attribute
        const escapedName = player.name.replace(/'/g, "\\'").replace(/"/g, '\\"');
        
        playerCard.innerHTML = `
            <div class="player-info">
                <span class="player-name">${player.name} (${player.cost})</span>
            </div>
            <button onclick="removePlayer('${escapedName}')" class="remove-button" ${hasSubmitted ? 'disabled' : ''}>Remove</button>
        `;
        teamSection.appendChild(playerCard);
    });

    updateBudgetDisplay();
}

// Update budget display
function updateBudgetDisplay() {
    const budgetDisplay = document.querySelector('.budget-display');
    if (!budgetDisplay) {
        const budgetDiv = document.createElement('div');
        budgetDiv.className = 'budget-display';
        document.querySelector('.team-section').insertBefore(budgetDiv, document.querySelector('.selected-players'));
    }
    document.querySelector('.budget-display').textContent = `Remaining Budget: $${remainingBudget}`;
}

// Update submit button state
function updateSubmitButton() {
    const submitButton = document.getElementById('submit-team');
    const inputHint = document.querySelector('.input-hint');
    
    if (selectedPlayers.length !== 5) {
        submitButton.disabled = true;
        inputHint.classList.remove('show');
    } else if (!playerName) {
        submitButton.disabled = true;
        inputHint.classList.add('show');
    } else {
        submitButton.disabled = false;
        inputHint.classList.remove('show');
    }
}

// Remove a player from the team
function removePlayer(playerName) {
    if (hasSubmitted) {
        showError('You have already submitted your team. Cannot make changes.');
        return;
    }
    
    // Find the player by name, using a more robust comparison
    const playerIndex = selectedPlayers.findIndex(player => {
        // Normalize both strings for comparison
        const normalizedPlayerName = player.name.toLowerCase().replace(/['"]/g, '');
        const normalizedInputName = playerName.toLowerCase().replace(/['"]/g, '');
        return normalizedPlayerName === normalizedInputName;
    });
    
    if (playerIndex !== -1) {
        const player = selectedPlayers[playerIndex];
        remainingBudget += getPlayerCost(player.cost);
        selectedPlayers.splice(playerIndex, 1);
        updateTeamDisplay();
        displayPlayerOptions();
        updateSubmitButton();
    }
}

// Show error message
function showError(message) {
    const errorDiv = document.querySelector('.error-message') || document.createElement('div');
    errorDiv.className = 'error-message';
    errorDiv.textContent = message;
    
    if (!document.querySelector('.error-message')) {
        document.querySelector('.team-section').insertBefore(errorDiv, document.querySelector('.record-display'));
    }
    
    setTimeout(() => errorDiv.remove(), 5000);
}

// Submit the team for simulation
function submitTeam() {
    if (selectedPlayers.length !== 5 || !playerName) {
        showError('Please select exactly 5 players and enter your nickname!');
        return;
    }

    const teamData = {
        players: selectedPlayers.map(player => player.name),
        playerName: playerName
    };

    fetch('/api/simulate', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(teamData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            showError(data.error);
        } else {
            hasSubmitted = true;
            updateRecordDisplay(data.record);
            
            // Disable the submit button and player name input
            document.getElementById('submit-team').disabled = true;
            document.getElementById('player-name').disabled = true;
            
            // Update the submit button text
            document.getElementById('submit-team').textContent = 'Team Submitted';
            
            // Disable all player buttons
            displayPlayerOptions();
            
            // Show a success message
            const successDiv = document.createElement('div');
            successDiv.className = 'success-message';
            successDiv.textContent = 'Your team has been submitted successfully!';
            document.querySelector('.team-section').insertBefore(successDiv, document.querySelector('.record-display'));
        }
    })
    .catch(error => {
        console.error('Error simulating team:', error);
        showError('Error simulating team. Please try again.');
    });
}

// Update the record display with player stats
function updateRecordDisplay(record) {
    const recordDisplay = document.querySelector('.record-display');
    
    // First, fetch the player stats from the server
    fetch('/api/player_pool')
        .then(response => response.json())
        .then(playerPool => {
            // Create a mapping of player names to their stats
            const playerStatsMap = {};
            for (const category in playerPool) {
                playerPool[category].forEach(player => {
                    playerStatsMap[player.name] = player.stats;
                });
            }
            
            // Now generate the HTML with the stats
            recordDisplay.innerHTML = `
                <div class="record">Projected Record: ${record}</div>
                <div class="player-stats-container">
                    ${selectedPlayers.map(player => {
                        // Get the player's stats from our map
                        const baseStats = playerStatsMap[player.name] || {
                            points: 0,
                            rebounds: 0,
                            assists: 0,
                            steals: 0,
                            blocks: 0
                        };
                        
                        // Generate slightly varied stats (per game)
                        const variation = 0.1; // 10% variation
                        const projectedStats = {
                            ppg: (baseStats.points * (1 + (Math.random() * variation * 2 - variation))).toFixed(1),
                            rpg: (baseStats.rebounds * (1 + (Math.random() * variation * 2 - variation))).toFixed(1),
                            apg: (baseStats.assists * (1 + (Math.random() * variation * 2 - variation))).toFixed(1),
                            spg: (baseStats.steals * (1 + (Math.random() * variation * 2 - variation))).toFixed(1),
                            bpg: (baseStats.blocks * (1 + (Math.random() * variation * 2 - variation))).toFixed(1)
                        };
                        
                        return `
                            <div class="player-season-stats">
                                <h3>${player.name}</h3>
                                <div class="stats-grid">
                                    <span>${projectedStats.ppg} PPG</span>
                                    <span>${projectedStats.rpg} RPG</span>
                                    <span>${projectedStats.apg} APG</span>
                                    <span>${projectedStats.spg} SPG</span>
                                    <span>${projectedStats.bpg} BPG</span>
                                </div>
                            </div>
                        `;
                    }).join('')}
                </div>
            `;
            recordDisplay.classList.add('show');
        })
        .catch(error => {
            console.error('Error fetching player stats:', error);
            recordDisplay.innerHTML = `<div class="record">Projected Record: ${record}</div>`;
            recordDisplay.classList.add('show');
        });
}

// Initialize when the page loads
document.addEventListener('DOMContentLoaded', initializeTeamBuilder);

// Load leaderboard preview
async function loadLeaderboardPreview() {
    try {
        const response = await fetch('/leaderboard');
        const html = await response.text();
        
        // Extract the table from the HTML
        const parser = new DOMParser();
        const doc = parser.parseFromString(html, 'text/html');
        const table = doc.querySelector('.leaderboard-table table');
        
        if (table) {
            const leaderboardPreview = document.querySelector('.leaderboard-preview');
            leaderboardPreview.innerHTML = '';
            
            // Create a simplified version of the table (top 5)
            const tbody = table.querySelector('tbody');
            const rows = tbody.querySelectorAll('tr');
            
            if (rows.length > 0) {
                const previewTable = document.createElement('table');
                const previewTbody = document.createElement('tbody');
                
                // Add top 5 rows
                for (let i = 0; i < Math.min(5, rows.length); i++) {
                    previewTbody.appendChild(rows[i].cloneNode(true));
                }
                
                previewTable.appendChild(previewTbody);
                leaderboardPreview.appendChild(previewTable);
            } else {
                leaderboardPreview.innerHTML = '<p class="no-submissions">No submissions yet for today\'s challenge.</p>';
            }
        }
    } catch (error) {
        console.error('Error loading leaderboard preview:', error);
    }
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('submission-modal');
    if (event.target === modal) {
        modal.style.display = 'none';
    }
}

// Check if user has already submitted a team
async function checkSubmission() {
    try {
        const response = await fetch(`/api/check_submission?player_name=${playerName}`);
        const data = await response.json();
        
        if (data.has_submission) {
            hasSubmitted = true;
            await loadSubmittedTeam();
        }
    } catch (error) {
        console.error('Error checking submission:', error);
    }
}

// Load submitted team data
async function loadSubmittedTeam() {
    try {
        const response = await fetch(`/api/submitted_team?player_name=${playerName}`);
        const data = await response.json();
        
        selectedPlayers = data.players;
        updateTeamDisplay();
        document.getElementById('submit-button').disabled = true;
        document.getElementById('submit-button').textContent = 'Team Submitted';
        
        // Show record
        const record = data.record;
        document.getElementById('current-record').textContent = `${record.wins}-${record.losses}`;
    } catch (error) {
        console.error('Error loading submitted team:', error);
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    playerName = document.getElementById('player-name').value;
    checkSubmission();
}); 