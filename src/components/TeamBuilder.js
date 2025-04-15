import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './TeamBuilder.css';

// Get API URL from environment variable or use default
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const TeamBuilder = () => {
    const [playerPool, setPlayerPool] = useState({});
    const [selectedPlayers, setSelectedPlayers] = useState([]);
    const [playerOptions, setPlayerOptions] = useState([]);
    const [budget, setBudget] = useState(10);
    const [record, setRecord] = useState(null);
    const [playerName, setPlayerName] = useState('');
    const [error, setError] = useState('');

    useEffect(() => {
        loadPlayerPool();
    }, []);

    const loadPlayerPool = async () => {
        try {
            const response = await axios.get(`${API_URL}/api/player-pool`);
            setPlayerPool(response.data);
            updatePlayerOptions(response.data);
        } catch (error) {
            setError('Error loading player pool');
        }
    };

    const updatePlayerOptions = (pool) => {
        const options = [];
        ['$3', '$2', '$1', '$0'].forEach(category => {
            if (pool[category]) {
                const players = pool[category].filter(player => 
                    !selectedPlayers.some(p => p.name === player.name)
                );
                if (players.length > 0) {
                    options.push(...players.map(player => ({
                        ...player,
                        cost: parseInt(category.replace('$', ''))
                    })));
                }
            }
        });
        setPlayerOptions(options);
    };

    const selectPlayer = (player) => {
        if (selectedPlayers.length >= 5) {
            setError('Team is already full');
            return;
        }
        if (budget < player.cost) {
            setError('Not enough budget');
            return;
        }

        const newSelectedPlayers = [...selectedPlayers, player];
        setSelectedPlayers(newSelectedPlayers);
        setBudget(budget - player.cost);
        updatePlayerOptions(playerPool);
        setError('');
    };

    const removePlayer = (playerName) => {
        const player = selectedPlayers.find(p => p.name === playerName);
        if (player) {
            setSelectedPlayers(selectedPlayers.filter(p => p.name !== playerName));
            setBudget(budget + player.cost);
            updatePlayerOptions(playerPool);
        }
    };

    const simulateTeam = async () => {
        if (selectedPlayers.length !== 5) {
            setError('Team must have exactly 5 players');
            return;
        }

        try {
            const response = await axios.post(`${API_URL}/api/simulate`, {
                players: selectedPlayers.map(p => p.name),
                player_name: playerName
            });
            setRecord(response.data);
            setError('');
        } catch (error) {
            setError('Error simulating team');
        }
    };

    return (
        <div className="team-builder">
            <div className="team-section">
                <h2>Your Team</h2>
                <div className="budget-display">
                    Remaining Budget: ${budget}
                </div>
                <div className="selected-players">
                    {selectedPlayers.map(player => (
                        <div key={player.name} className="player-card">
                            <h3>{player.name}</h3>
                            <p>Cost: ${player.cost}</p>
                            <button onClick={() => removePlayer(player.name)}>Remove</button>
                        </div>
                    ))}
                </div>
                {record && (
                    <div className="record-display">
                        <h3>Projected Record: {record.wins}-{record.losses}</h3>
                        <div className="player-stats">
                            {selectedPlayers.map(player => (
                                <div key={player.name} className="player-stat">
                                    <h4>{player.name}</h4>
                                    <p>PPG: {record.player_stats[player.name].ppg.toFixed(1)}</p>
                                    <p>RPG: {record.player_stats[player.name].rpg.toFixed(1)}</p>
                                    <p>APG: {record.player_stats[player.name].apg.toFixed(1)}</p>
                                    <p>SPG: {record.player_stats[player.name].spg.toFixed(1)}</p>
                                    <p>BPG: {record.player_stats[player.name].bpg.toFixed(1)}</p>
                                </div>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <div className="player-section">
                <h2>Available Players</h2>
                <div className="player-options">
                    {playerOptions.map(player => (
                        <div key={player.name} className="player-card">
                            <h3>{player.name}</h3>
                            <p>Cost: ${player.cost}</p>
                            <button 
                                onClick={() => selectPlayer(player)}
                                disabled={budget < player.cost || selectedPlayers.length >= 5}
                            >
                                Select
                            </button>
                        </div>
                    ))}
                </div>
            </div>

            {error && <div className="error-message">{error}</div>}

            <div className="simulation-section">
                <input
                    type="text"
                    value={playerName}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="Enter your name"
                    className="player-name-input"
                />
                <button 
                    onClick={simulateTeam}
                    disabled={selectedPlayers.length !== 5 || !playerName}
                    className="simulate-button"
                >
                    Simulate Team
                </button>
            </div>
        </div>
    );
};

export default TeamBuilder; 